import asyncio
import logging
import time
from datetime import datetime
from app.services.transaction_service import TransactionService
from app.services.posting_client import PostingServiceClient
from app.models import TransactionRequest, TransactionStatus
from app.config import settings

logger = logging.getLogger(__name__)

class TransactionWorker:
    def __init__(self):
        self.transaction_service = TransactionService()
        self.posting_client = PostingServiceClient()
        self.running = False
        
    async def start(self):
        """Start worker pool"""
        self.running = True
        logger.info(f"Starting {settings.worker_concurrency} workers")
        
        tasks = []
        for i in range(settings.worker_concurrency):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def stop(self):
        """Stop worker pool"""
        self.running = False
        logger.info("Stopping workers")
    
    async def _worker_loop(self, worker_id: str):
        """Main worker loop"""
        logger.info(f"{worker_id} started")
        
        while self.running:
            try:
                # Get next transaction
                transaction_id = self.transaction_service.get_next_transaction()
                if not transaction_id:
                    await asyncio.sleep(0.1)
                    continue
                
                await self._process_transaction(worker_id, transaction_id)
                
            except Exception as e:
                logger.error(f"{worker_id} error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_transaction(self, worker_id: str, transaction_id: str):
        """Process a single transaction"""
        logger.info(f"{worker_id} processing transaction {transaction_id}")
        
        # Update status to processing
        self.transaction_service.update_transaction_status(
            transaction_id, 
            TransactionStatus.PROCESSING
        )
        
        # Get transaction data
        status_record = await self.transaction_service.get_transaction_status(transaction_id)
        if not status_record:
            logger.error(f"No status record found for {transaction_id}")
            return
        
        # Get full transaction data from Redis
        status_key = f"{self.transaction_service.status_key_prefix}{transaction_id}"
        status_data = self.transaction_service.redis_client.get(status_key)
        if not status_data:
            logger.error(f"No transaction data found for {transaction_id}")
            return
        
        import json
        record = json.loads(status_data)
        transaction_data = record["transaction_data"]
        transaction = TransactionRequest(**transaction_data)
        
        # Process with retries
        max_retries = settings.max_retries
        retry_count = record.get("retryCount", 0)
        
        for attempt in range(retry_count, max_retries):
            try:
                # First check if transaction already exists (idempotency)
                exists, existing_data = await self.posting_client.get_transaction(transaction_id)
                if exists:
                    logger.info(f"Transaction {transaction_id} already exists in posting service")
                    self.transaction_service.update_transaction_status(
                        transaction_id,
                        TransactionStatus.COMPLETED,
                        completed_at=datetime.utcnow()
                    )
                    return
                
                # Try to post transaction
                success, error = await self.posting_client.post_transaction(transaction)
                
                if success:
                    # Success - mark as completed
                    self.transaction_service.update_transaction_status(
                        transaction_id,
                        TransactionStatus.COMPLETED,
                        completed_at=datetime.utcnow()
                    )
                    logger.info(f"Successfully processed transaction {transaction_id}")
                    return
                else:
                    # POST failed - check if it was post-write failure
                    await asyncio.sleep(1)  # Brief delay
                    exists, _ = await self.posting_client.get_transaction(transaction_id)
                    if exists:
                        # Post-write failure - transaction was actually saved
                        logger.info(f"Post-write failure detected for {transaction_id} - transaction exists")
                        self.transaction_service.update_transaction_status(
                            transaction_id,
                            TransactionStatus.COMPLETED,
                            completed_at=datetime.utcnow()
                        )
                        return
                    else:
                        # Pre-write failure - retry
                        logger.warning(f"Pre-write failure for {transaction_id}, attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            # Update retry count
                            record["retryCount"] = attempt + 1
                            self.transaction_service.redis_client.setex(
                                status_key, 
                                86400, 
                                json.dumps(record, default=str)
                            )
                            await asyncio.sleep(settings.retry_delay * (2 ** attempt))  # Exponential backoff
                        else:
                            # Max retries exceeded
                            self.transaction_service.update_transaction_status(
                                transaction_id,
                                TransactionStatus.FAILED,
                                error=f"Max retries exceeded: {error}",
                                completed_at=datetime.utcnow()
                            )
                            logger.error(f"Transaction {transaction_id} failed after {max_retries} attempts")
                            return
                            
            except Exception as e:
                error_msg = f"Worker error processing {transaction_id}: {str(e)}"
                logger.error(error_msg)
                if attempt >= max_retries - 1:
                    self.transaction_service.update_transaction_status(
                        transaction_id,
                        TransactionStatus.FAILED,
                        error=error_msg,
                        completed_at=datetime.utcnow()
                    )
                    return
                await asyncio.sleep(settings.retry_delay)