import pytest
from unittest.mock import AsyncMock, patch
from app.services.posting_client import PostingServiceClient
from app.models import TransactionRequest
from datetime import datetime, timezone
import uuid

@pytest.mark.asyncio
@patch("app.services.posting_client.PostingServiceClient.post_transaction", new_callable=AsyncMock)
@patch("app.services.posting_client.PostingServiceClient.get_transaction", new_callable=AsyncMock)
async def test_posting_service_integration(mock_get, mock_post):
    """Test integration with mocked posting service"""
    
    # Mock the post_transaction to succeed
    mock_post.return_value = (True, None)
    
    # Mock get_transaction to return the transaction
    mock_get.return_value = (True, {
        "id": "mock-id",
        "amount": 123.45,
        "currency": "USD",
        "description": "Integration test transaction"
    })
    
    client = PostingServiceClient()
    
    transaction = TransactionRequest(
        id="mock-id",
        amount=123.45,
        currency="USD",
        description="Integration test transaction",
        timestamp=datetime.now(timezone.utc)  # timezone-aware
    )
    
    # Test posting
    success, error = await client.post_transaction(transaction)
    assert success
    assert error is None
    
    # Test retrieval
    exists, data = await client.get_transaction(transaction.id)
    assert exists
    assert data["id"] == transaction.id
    assert float(data["amount"]) == transaction.amount

@pytest.mark.asyncio
@patch("app.services.posting_client.PostingServiceClient.post_transaction", new_callable=AsyncMock)
async def test_posting_service_failure_handling(mock_post):
    """Test handling of posting service failures"""
    
    # Mock a failure response
    mock_post.return_value = (False, "Posting failed: simulated error")
    
    client = PostingServiceClient()
    
    transaction = TransactionRequest(
        id="failure-id",
        amount=50.0,
        currency="USD",
        description="Failure test",
        timestamp=datetime.now(timezone.utc)  # timezone-aware
    )
    
    success, error = await client.post_transaction(transaction)
    
    # Should handle the error gracefully
    assert success is False
    assert error == "Posting failed: simulated error"

@pytest.mark.asyncio
@patch("app.services.posting_client.PostingServiceClient.post_transaction", new_callable=AsyncMock)
@patch("app.services.posting_client.PostingServiceClient.get_transaction", new_callable=AsyncMock)
async def test_idempotency_check(mock_get, mock_post):
    """Test idempotency checking"""
    
    # Mock post_transaction to succeed
    mock_post.return_value = (True, None)
    
    # Mock get_transaction to return the transaction on first call and non-existent on second
    mock_get.side_effect = [
        (True, {"id": "idempotent-id", "amount": 99.99, "currency": "USD", "description": "Idempotency test"}),
        (False, None)
    ]
    
    client = PostingServiceClient()
    
    transaction = TransactionRequest(
        id="idempotent-id",
        amount=99.99,
        currency="USD",
        description="Idempotency test",
        timestamp=datetime.now(timezone.utc)  # timezone-aware
    )
    
    success, error = await client.post_transaction(transaction)
    assert success
    
    exists, data = await client.get_transaction(transaction.id)
    assert exists
    
    exists, data = await client.get_transaction("non-existent-id")
    assert not exists
    assert data is None
