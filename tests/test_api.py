import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.transaction_service import TransactionService
import json
import time

client = TestClient(app)

@pytest.fixture
def transaction_service():
    return TransactionService()

def test_submit_transaction():
    """Test transaction submission"""
    transaction_data = {
        "amount": 100.50,
        "currency": "USD",
        "description": "Test transaction"
    }
    
    start_time = time.time()
    response = client.post("/api/transactions", json=transaction_data)
    end_time = time.time()
    
    # Check response time < 100ms
    assert (end_time - start_time) < 0.1
    
    assert response.status_code == 200
    data = response.json()
    
    assert "transactionId" in data
    assert data["status"] == "pending"
    assert "submittedAt" in data

def test_get_transaction_status():
    """Test getting transaction status"""
    # First submit a transaction
    transaction_data = {
        "amount": 50.25,
        "currency": "EUR",
        "description": "Status test transaction"
    }
    
    submit_response = client.post("/api/transactions", json=transaction_data)
    transaction_id = submit_response.json()["transactionId"]
    
    # Get status
    status_response = client.get(f"/api/transactions/{transaction_id}")
    assert status_response.status_code == 200
    
    data = status_response.json()
    assert data["transactionId"] == transaction_id
    assert data["status"] in ["pending", "processing", "completed"]

def test_get_nonexistent_transaction():
    """Test getting status of non-existent transaction"""
    fake_id = "non-existent-id"
    response = client.get(f"/api/transactions/{fake_id}")
    assert response.status_code == 404

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "queue_depth" in data

def test_duplicate_transaction():
    """Test duplicate transaction handling"""
    transaction_data = {
        "id": "duplicate-test-id",
        "amount": 75.00,
        "currency": "USD",
        "description": "Duplicate test"
    }
    
    # Submit first transaction
    response1 = client.post("/api/transactions", json=transaction_data)
    assert response1.status_code == 200
    
    # Submit duplicate
    response2 = client.post("/api/transactions", json=transaction_data)
    assert response2.status_code == 200
    
    # Both should return same transaction ID
    assert response1.json()["transactionId"] == response2.json()["transactionId"]

def test_invalid_transaction_data():
    """Test invalid transaction data"""
    # Negative amount
    invalid_data = {
        "amount": -50.00,
        "currency": "USD",
        "description": "Invalid transaction"
    }
    
    response = client.post("/api/transactions", json=invalid_data)
    assert response.status_code == 422  # Validation error
    
    # Invalid currency
    invalid_data = {
        "amount": 50.00,
        "currency": "INVALID",
        "description": "Invalid currency"
    }
    
    response = client.post("/api/transactions", json=invalid_data)
    assert response.status_code == 422