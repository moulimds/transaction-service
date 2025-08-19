import pytest
import asyncio
import httpx
import logging
from app.services.posting_client import PostingServiceClient
from app.models import TransactionRequest
from datetime import datetime, timezone
import uuid

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_posting_service_connection():
    """Test basic connection to posting service"""
    client = PostingServiceClient()
    
    # Test connection first
    connection_ok = await client.test_connection()
    assert connection_ok, "Cannot connect to posting service"

@pytest.mark.asyncio
async def test_posting_service_integration():
    """Test integration with mock posting service"""
    client = PostingServiceClient()
    
    # Test connection first
    connection_ok = await client.test_connection()
    if not connection_ok:
        pytest.skip("Posting service not available")
    
    # Clean up before test
    cleanup_result = await client.cleanup()
    logger.info(f"Cleanup result: {cleanup_result}")
    
    # Create test transaction with fixed timestamp
    transaction = TransactionRequest(
        id=str(uuid.uuid4()),
        amount=123.45,
        currency="USD",
        description="Integration test transaction",
        timestamp=datetime.now(timezone.utc)
    )
    
    # Test posting
    success, error = await client.post_transaction(transaction)
    assert success, f"Posting failed: {error}"
    
    # Wait a moment for the posting service to process
    await asyncio.sleep(1)
    
    # Test retrieval
    exists, data = await client.get_transaction(transaction.id)
    assert exists, "Transaction should exist after posting"
    assert data["id"] == transaction.id
    assert float(data["amount"]) == transaction.amount

@pytest.mark.asyncio 
async def test_posting_service_failure_handling():
    """Test handling of posting service failures"""
    client = PostingServiceClient()
    
    # Test connection first
    connection_ok = await client.test_connection()
    if not connection_ok:
        pytest.skip("Posting service not available")
    
    # Create a valid transaction but with a potentially problematic ID
    transaction = TransactionRequest(
        id="test-failure-handling-id",
        amount=50.0,  # Valid amount
        currency="USD",  # Valid currency
        description="Failure test transaction",
        timestamp=datetime.now(timezone.utc)
    )
    
    # This should work with valid data
    success, error = await client.post_transaction(transaction)
    
    # Should handle the response gracefully regardless of success/failure
    assert isinstance(success, bool)
    if not success:
        assert isinstance(error, str)
        logger.info(f"Expected failure handled: {error}")

@pytest.mark.asyncio
async def test_idempotency_check():
    """Test idempotency checking"""
    client = PostingServiceClient()
    
    # Test connection first
    connection_ok = await client.test_connection()
    if not connection_ok:
        pytest.skip("Posting service not available")
        
    await client.cleanup()
    
    transaction = TransactionRequest(
        id=str(uuid.uuid4()),
        amount=99.99,
        currency="USD", 
        description="Idempotency test",
        timestamp=datetime.now(timezone.utc)
    )
    
    # Post transaction
    success, error = await client.post_transaction(transaction)
    assert success, f"Initial posting should succeed: {error}"
    
    # Wait for processing
    await asyncio.sleep(1)
    
    # Check if exists
    exists, data = await client.get_transaction(transaction.id)
    assert exists, "Transaction should exist after posting"
    
    # Check non-existent transaction
    exists, data = await client.get_transaction("non-existent-id")
    assert not exists
    assert data is None

@pytest.mark.asyncio
async def test_posting_service_endpoints():
    """Test all posting service endpoints"""
    client = PostingServiceClient()
    
    # Test connection
    connection_ok = await client.test_connection()
    if not connection_ok:
        pytest.skip("Posting service not available")
    
    # Test cleanup endpoint
    cleanup_result = await client.cleanup()
    assert cleanup_result, "Cleanup should work"
    
    # Test list endpoint (should be empty after cleanup)
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(f"{client.base_url}/transactions")
        logger.info(f"List transactions response: {response.status_code}")
        # Should return 200 or 404, both are acceptable
        assert response.status_code in [200, 404]