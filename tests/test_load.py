# tests/load_test.py

import pytest
import asyncio
import aiohttp
import time
import uuid
from locust import HttpUser, task, between

BASE_URL = "http://127.0.0.1:8000"

# =========================
# Pytest Async Load Test
# =========================
@pytest.mark.asyncio
async def test_load_performance():
    """Test system performance under load using asyncio and aiohttp"""

    async def submit_transaction(session, transaction_id):
        transaction_data = {
            "id": transaction_id,
            "amount": 100.0,
            "currency": "USD",
            "description": f"Load test transaction {transaction_id}"
        }

        start_time = time.time()
        try:
            async with session.post(f"{BASE_URL}/api/transactions", json=transaction_data) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                assert response.status == 200, f"Status {response.status} != 200"
                assert response_time < 100, f"Response time {response_time:.2f}ms exceeded 100ms"
                return await response.json()
        except Exception as e:
            return e  # Capture exception for reporting

    num_requests = 100
    async with aiohttp.ClientSession() as session:
        tasks = [submit_transaction(session, f"load-test-{i}") for i in range(num_requests)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

    successful_requests = sum(1 for r in results if not isinstance(r, Exception))
    total_time = end_time - start_time
    throughput = successful_requests / total_time

    print("=== Load Test Results ===")
    print(f"Total requests: {num_requests}")
    print(f"Successful requests: {successful_requests}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {throughput:.2f} req/s")

    assert successful_requests >= num_requests * 0.95, "Success rate below 95%"
    assert throughput >= 500, "Throughput below 500 req/s"


# =========================
# Locust Load Test
# =========================
class TransactionUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def submit_transaction(self):
        transaction_data = {
            "id": str(uuid.uuid4()),
            "amount": 100.0,
            "currency": "USD",
            "description": "Locust load test transaction"
        }
        with self.client.post("/api/transactions", json=transaction_data, catch_response=True) as response:
            if response.elapsed.total_seconds() * 1000 > 100:
                response.failure(f"Response time {response.elapsed.total_seconds() * 1000:.2f}ms > 100ms")

    @task(1)
    def check_health(self):
        self.client.get("/api/health")
