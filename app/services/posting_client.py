import httpx
import asyncio
import logging
from typing import Optional, Dict, Any
from app.config import settings
from app.models import TransactionRequest

logger = logging.getLogger(__name__)

class PostingServiceClient:
    def __init__(self):
        self.base_url = settings.posting_service_url
        self.timeout = httpx.Timeout(30.0)
    
    async def post_transaction(self, transaction: TransactionRequest) -> tuple[bool, Optional[str]]:
        """
        Post transaction to posting service.
        Returns (success, error_message)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload = transaction.dict()
                payload["timestamp"] = payload["timestamp"].isoformat()
                
                response = await client.post(
                    f"{self.base_url}/transactions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully posted transaction {transaction.id}")
                    return True, None
                else:
                    error_msg = f"Posting failed with status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"Posting service error: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
    
    async def get_transaction(self, transaction_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if transaction exists in posting service.
        Returns (exists, transaction_data)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/transactions/{transaction_id}")
                
                if response.status_code == 200:
                    return True, response.json()
                elif response.status_code == 404:
                    return False, None
                else:
                    logger.warning(f"Unexpected status {response.status_code} when checking transaction {transaction_id}")
                    return False, None
                    
            except Exception as e:
                logger.error(f"Error checking transaction {transaction_id}: {str(e)}")
                return False, None
    
    async def cleanup(self) -> bool:
        """Cleanup all transactions (for testing)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/cleanup")
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Cleanup failed: {str(e)}")
                return False