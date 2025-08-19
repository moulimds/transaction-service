import json
import redis
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.models import TransactionRequest, TransactionResponse, TransactionStatus
from app.config import settings

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.queue_key = "transaction_queue"
        self.status_key_prefix = "transaction_status:"
        self.dedup_key_prefix = "transaction_dedup:"
        
    async def submit_transaction(self, transaction: TransactionRequest) -> TransactionResponse:
        """Submit transaction for processing"""
        transaction_id = transaction.id
        
        # Check for duplicate submission
        dedup_key = f"{self.dedup_key_prefix}{transaction_id}"
        if self.redis_client.exists(dedup_key):
            logger.info(f"Duplicate transaction detected: {transaction_id}")
            return await self.get_transaction_status(transaction_id)
        
        # Set deduplication marker
        self.redis_client.setex(dedup_key, 3600, "1")  # 1 hour TTL
        
        # Create transaction record
        now = datetime.now(timezone.utc)
        status_record = {
            "transactionId": transaction_id,
            "status": TransactionStatus.PENDING.value,
            "submittedAt": now.isoformat(),
            "completedAt": None,
            "error": None,
            "retryCount": 0,
            "transaction_data": transaction.model_dump()  # Use model_dump instead of dict()
        }
        
        # Store status
        status_key = f"{self.status_key_prefix}{transaction_id}"
        self.redis_client.setex(
            status_key, 
            86400,  # 24 hours TTL
            json.dumps(status_record, default=str)
        )
        
        # Queue for processing
        queue_item = {
            "transaction_id": transaction_id,
            "queued_at": now.isoformat()
        }
        
        self.redis_client.lpush(self.queue_key, json.dumps(queue_item))
        logger.info(f"Queued transaction {transaction_id}")
        
        return TransactionResponse(
            transactionId=transaction_id,
            status=TransactionStatus.PENDING,
            submittedAt=now
        )
    
    async def get_transaction_status(self, transaction_id: str) -> Optional[TransactionResponse]:
        """Get transaction status"""
        status_key = f"{self.status_key_prefix}{transaction_id}"
        status_data = self.redis_client.get(status_key)
        
        if not status_data:
            return None
        
        try:
            record = json.loads(status_data)
            return TransactionResponse(
                transactionId=record["transactionId"],
                status=TransactionStatus(record["status"]),
                submittedAt=datetime.fromisoformat(record["submittedAt"]),
                completedAt=datetime.fromisoformat(record["completedAt"]) if record["completedAt"] else None,
                error=record.get("error")
            )
        except Exception as e:
            logger.error(f"Error parsing status for {transaction_id}: {str(e)}")
            return None
    
    def update_transaction_status(self, transaction_id: str, status: TransactionStatus, 
                                error: Optional[str] = None, completed_at: Optional[datetime] = None):
        """Update transaction status"""
        status_key = f"{self.status_key_prefix}{transaction_id}"
        status_data = self.redis_client.get(status_key)
        
        if status_data:
            try:
                record = json.loads(status_data)
                record["status"] = status.value
                if error:
                    record["error"] = error
                if completed_at:
                    record["completedAt"] = completed_at.isoformat()
                
                self.redis_client.setex(status_key, 86400, json.dumps(record, default=str))
                logger.info(f"Updated transaction {transaction_id} status to {status.value}")
            except Exception as e:
                logger.error(f"Error updating status for {transaction_id}: {str(e)}")
    
    def get_queue_depth(self) -> int:
        """Get current queue depth"""
        return self.redis_client.llen(self.queue_key)
    
    def get_next_transaction(self) -> Optional[str]:
        """Get next transaction from queue (blocking)"""
        try:
            result = self.redis_client.brpop(self.queue_key, timeout=1)
            if result:
                queue_item = json.loads(result[1])
                return queue_item["transaction_id"]
        except Exception as e:
            logger.error(f"Error getting next transaction: {str(e)}")
        return None