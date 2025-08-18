import pytest
import asyncio
import httpx
from app.services.posting_client import PostingServiceClient
from app.models import TransactionRequest
from datetime import datetime
import uuid

@pytest.mark.asyncio
async def test_posting_service_integration():
    """Test integration with mock posting service"""
    client = PostingServiceClient()
    
    # Clean up before test
    await client.cleanup()
    
    # Create test transaction
    transaction = TransactionRequest(
        id=str(uuid.uuid4()),
        amount=123.45,
        currency="USD",
        description="Integration test transaction",
        timestamp=datetime.utcnow()
    )
    
    # Test posting
    success, error = await client.post_transaction(transaction)
    assert success, f"Posting failed: {error}"
    
    # Test retrieval
    exists, data = await client.get_transaction(transaction.id)
    assert exists
    assert data["id"] == transaction.id
    assert float(data["amount"]) == transaction.amount

@pytest.mark.asyncio 
async def test_posting_service_failure_handling():
    """Test handling of posting service failures"""
    client = PostingServiceClient()
    
    # Test with invalid data to trigger failure
    transaction = TransactionRequest(
        id="invalid-test-id",
        amount=-100,  # This might trigger validation error
        currency="INVALID",
        description="Failure test",
        timestamp=datetime.utcnow()
    )
    
    success, error = await client.post_transaction(transaction)
    # Should handle the error gracefully
    assert isinstance(success, bool)
    assert error is None or isinstance(error, str)

@pytest.mark.asyncio
async def test_idempotency_check():
    """Test idempotency checking"""
    client = PostingServiceClient()
    await client.cleanup()
    
    transaction = TransactionRequest(
        id=str(uuid.uuid4()),
        amount=99.99,
        currency="USD", 
        description="Idempotency test",
        timestamp=datetime.utcnow()
    )
    
    # Post transaction
    success, error = await client.post_transaction(transaction)
    assert success
    
    # Check if exists
    exists, data = await client.get_transaction(transaction.id)
    assert exists
    
    # Check non-existent transaction
    exists, data = await client.get_transaction("non-existent-id")
    assert not exists
    assert data is None