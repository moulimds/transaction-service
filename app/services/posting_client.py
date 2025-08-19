import httpx
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
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
                # Use model_dump instead of deprecated dict()
                payload = transaction.model_dump()
                
                # Ensure timestamp is properly formatted
                if isinstance(payload["timestamp"], datetime):
                    payload["timestamp"] = payload["timestamp"].isoformat()
                
                logger.info(f"Posting transaction {transaction.id} to {self.base_url}/transactions")
                
                response = await client.post(
                    f"{self.base_url}/transactions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info(f"Posting service response: {response.status_code} - {response.text}")
                
                # Check for successful status codes (200, 201)
                if response.status_code in [200, 201]:
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
                logger.info(f"Checking transaction {transaction_id} at {self.base_url}/transactions/{transaction_id}")
                
                response = await client.get(f"{self.base_url}/transactions/{transaction_id}")
                
                logger.info(f"Get transaction response: {response.status_code}")
                
                if response.status_code == 200:
                    data = await response.json()
                    return True, data
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
                logger.info(f"Cleaning up posting service at {self.base_url}/cleanup")
                response = await client.post(f"{self.base_url}/cleanup")
                logger.info(f"Cleanup response: {response.status_code}")
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Cleanup failed: {str(e)}")
                return False
    
    async def test_connection(self) -> bool:
        """Test connection to posting service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Try to get transactions list first
                response = await client.get(f"{self.base_url}/transactions")
                logger.info(f"Connection test response: {response.status_code}")
                return response.status_code in [200, 404]  # 404 is OK if no transactions
            except Exception as e:
                logger.error(f"Connection test failed: {str(e)}")
                return False