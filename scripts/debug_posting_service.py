import asyncio
import httpx
import json
from datetime import datetime, timezone

async def debug_posting_service():
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🔍 Debugging Posting Service...")
        
        # Test 1: Check if service is running
        try:
            response = await client.get(f"{base_url}/transactions")
            print(f"✅ GET /transactions: {response.status_code}")
            if response.status_code == 200:
                data = await response.json()
                print(f"   Response: {data}")
        except Exception as e:
            print(f"❌ GET /transactions failed: {e}")
            return
        
        # Test 2: Test cleanup
        try:
            response = await client.post(f"{base_url}/cleanup")
            print(f"✅ POST /cleanup: {response.status_code}")
            if response.status_code == 200:
                data = await response.json()
                print(f"   Cleaned up: {data}")
        except Exception as e:
            print(f"❌ POST /cleanup failed: {e}")
        
        # Test 3: Post a transaction
        test_transaction = {
            "id": "debug-test-123",
            "amount": 100.0,
            "currency": "USD",
            "description": "Debug test transaction",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            response = await client.post(
                f"{base_url}/transactions",
                json=test_transaction,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ POST /transactions: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code in [200, 201]:
                # Test getting the transaction back
                await asyncio.sleep(2)  # Wait for processing
                get_response = await client.get(f"{base_url}/transactions/{test_transaction['id']}")
                print(f"✅ GET /transactions/{test_transaction['id']}: {get_response.status_code}")
                if get_response.status_code == 200:
                    data = await get_response.json()
                    print(f"   Retrieved: {data}")
                    
        except Exception as e:
            print(f"❌ POST /transactions failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_posting_service())