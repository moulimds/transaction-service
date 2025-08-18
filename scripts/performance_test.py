import asyncio
import aiohttp
import time
import json
import uuid
import statistics
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"
POSTING_SERVICE_URL = "http://localhost:8080"

async def cleanup_posting_service():
    """Clean up posting service before testing"""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{POSTING_SERVICE_URL}/cleanup") as response:
            print(f"Cleanup response: {response.status}")

async def submit_single_transaction(session, transaction_id):
    """Submit a single transaction and measure response time"""
    transaction_data = {
        "id": transaction_id,
        "amount": 100.0,
        "currency": "USD",
        "description": f"Performance test transaction {transaction_id}"
    }
    
    start_time = time.time()
    try:
        async with session.post(
            f"{BASE_URL}/api/transactions",
            json=transaction_data,
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "response_time_ms": response_time_ms,
                    "transaction_id": data["transactionId"],
                    "status": data["status"]
                }
            else:
                return {
                    "success": False,
                    "response_time_ms": response_time_ms,
                    "error": f"HTTP {response.status}"
                }
    except Exception as e:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        return {
            "success": False,
            "response_time_ms": response_time_ms,
            "error": str(e)
        }

async def run_load_test(num_requests=1000, concurrency=50):
    """Run load test with specified parameters"""
    print(f"Starting load test: {num_requests} requests, {concurrency} concurrent")
    print("Cleaning up posting service...")
    await cleanup_posting_service()
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrency)
    
    async def limited_submit(session, transaction_id):
        async with semaphore:
            return await submit_single_transaction(session, transaction_id)
    
    async with aiohttp.ClientSession() as session:
        # Generate transaction IDs
        transaction_ids = [f"perf-test-{uuid.uuid4()}" for _ in range(num_requests)]
        
        # Start test
        start_time = time.time()
        tasks = [limited_submit(session, tid) for tid in transaction_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception) and r["success"]]
        failed_results = [r for r in results if isinstance(r, Exception) or not r["success"]]
        
        response_times = [r["response_time_ms"] for r in successful_results]
        
        total_time = end_time - start_time
        throughput = len(successful_results) / total_time
        
        print(f"\n=== Load Test Results ===")
        print(f"Total requests: {num_requests}")
        print(f"Successful requests: {len(successful_results)}")
        print(f"Failed requests: {len(failed_results)}")
        print(f"Success rate: {len(successful_results)/num_requests*100:.1f}%")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Throughput: {throughput:.2f} requests/second")
        
        if response_times:
            print(f"\n=== Response Time Statistics ===")
            print(f"Average: {statistics.mean(response_times):.2f} ms")
            print(f"Median: {statistics.median(response_times):.2f} ms")
            print(f"95th percentile: {statistics.quantiles(response_times, n=20)[18]:.2f} ms")
            print(f"99th percentile: {statistics.quantiles(response_times, n=100)[98]:.2f} ms")
            print(f"Max: {max(response_times):.2f} ms")
            print(f"Min: {min(response_times):.2f} ms")
            
            # Check sub-100ms requirement
            slow_requests = [rt for rt in response_times if rt > 100]
            print(f"Requests > 100ms: {len(slow_requests)} ({len(slow_requests)/len(response_times)*100:.1f}%)")
        
        if failed_results:
            print(f"\n=== Sample Errors ===")
            for i, result in enumerate(failed_results[:5]):  # Show first 5 errors
                if isinstance(result, Exception):
                    print(f"Error {i+1}: {result}")
                else:
                    print(f"Error {i+1}: {result.get('error', 'Unknown error')}")

async def test_status_queries():
    """Test transaction status query performance"""
    print("\n=== Testing Status Queries ===")
    
    # First submit some transactions
    transaction_ids = []
    async with aiohttp.ClientSession() as session:
        for i in range(10):
            result = await submit_single_transaction(session, f"status-test-{i}")
            if result["success"]:
                transaction_ids.append(result["transaction_id"])
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
        # Query statuses
        start_time = time.time()
        for tid in transaction_ids:
            async with session.get(f"{BASE_URL}/api/transactions/{tid}") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Transaction {tid}: {data['status']}")
        
        query_time = time.time() - start_time
        print(f"Status query time for {len(transaction_ids)} transactions: {query_time:.2f}s")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance test for transaction processing service")
    parser.add_argument("--requests", type=int, default=1000, help="Number of requests to send")
    parser.add_argument("--concurrency", type=int, default=50, help="Number of concurrent requests")
    parser.add_argument("--test-queries", action="store_true", help="Test status queries")
    
    args = parser.parse_args()
    
    async def main():
        await run_load_test(args.requests, args.concurrency)
        
        if args.test_queries:
            await test_status_queries()
    
    asyncio.run(main())