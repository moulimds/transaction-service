import asyncio
import aiohttp
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"
NUM_REQUESTS = 100           # Total number of requests
CONCURRENCY = 10             # Number of concurrent tasks
MAX_RESPONSE_MS = 100        # Max acceptable response time per request


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
            if response.status != 200:
                print(f"[FAIL] {transaction_id}: status {response.status}")
                return False, response_time
            if response_time > MAX_RESPONSE_MS:
                print(f"[SLOW] {transaction_id}: {response_time:.2f}ms")
                return True, response_time
            return True, response_time
    except Exception as e:
        print(f"[ERROR] {transaction_id}: {e}")
        return False, 0


async def run_load_test():
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with aiohttp.ClientSession() as session:
        async def sem_task(i):
            async with semaphore:
                return await submit_transaction(session, f"load-test-{i}")

        tasks = [sem_task(i) for i in range(NUM_REQUESTS)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        successful_requests = sum(1 for success, _ in results if success)
        total_time = end_time - start_time
        throughput = successful_requests / total_time

        avg_response = sum(rt for _, rt in results if rt > 0) / max(successful_requests, 1)

        print("\n==== Load Test Results ====")
        print(f"Total requests: {NUM_REQUESTS}")
        print(f"Successful requests: {successful_requests}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} req/s")
        print(f"Average response time: {avg_response:.2f}ms")
        print("===========================")

        # Performance assertions
        assert successful_requests >= NUM_REQUESTS * 0.95, "Less than 95% success rate"
        assert throughput >= 50, "Throughput below 50 req/s"


if __name__ == "__main__":
    asyncio.run(run_load_test())
