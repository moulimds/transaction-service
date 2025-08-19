import asyncio
import redis
import httpx
import subprocess
import sys

async def check_posting_service():
    """Check if posting service is running"""
    print("🎯 Checking Mock Posting Service...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test multiple endpoints
            endpoints = ["/transactions", "/health"]
            
            for endpoint in endpoints:
                try:
                    response = await client.get(f"http://localhost:8080{endpoint}")
                    print(f"   GET {endpoint}: {response.status_code} ✅")
                except Exception as e:
                    print(f"   GET {endpoint}: Failed - {e} ❌")
            
            # Test posting a transaction
            test_transaction = {
                "id": "diagnostic-test",
                "amount": 100.0,
                "currency": "USD",
                "description": "Diagnostic test",
                "timestamp": "2025-01-15T10:30:00Z"
            }
            
            try:
                response = await client.post(
                    "http://localhost:8080/transactions",
                    json=test_transaction
                )
                print(f"   POST /transactions: {response.status_code} ✅")
                print(f"   Response: {response.text[:100]}...")
            except Exception as e:
                print(f"   POST /transactions: Failed - {e} ❌")
                
    except Exception as e:
        print(f"❌ Posting service check failed: {e}")
        return False
    
    return True

def check_redis():
    """Check if Redis is running"""
    print("📡 Checking Redis...")
    
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        ping_result = r.ping()
        print(f"   Redis ping: {ping_result} ✅")
        
        # Test basic operations
        r.set("test_key", "test_value")
        value = r.get("test_key")
        r.delete("test_key")
        print(f"   Redis operations: Working ✅")
        
        return True
    except Exception as e:
        print(f"❌ Redis check failed: {e}")
        return False

def check_docker_services():
    """Check Docker services"""
    print("🐳 Checking Docker services...")
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("   Docker Compose status:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Docker Compose failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

async def main():
    """Run all diagnostics"""
    print("🔧 Running System Diagnostics...\n")
    
    all_good = True
    
    # Check Docker services
    if not check_docker_services():
        all_good = False
        print("💡 Try: docker-compose up -d")
    
    # Check Redis
    if not check_redis():
        all_good = False
        print("💡 Try: docker-compose restart redis")
    
    # Check posting service
    if not await check_posting_service():
        all_good = False
        print("💡 Try: docker-compose restart posting-service")
    
    print("\n" + "="*50)
    if all_good:
        print("🎉 All systems operational!")
        print("✅ Ready to run tests: pytest tests/test_integration.py -v")
    else:
        print("⚠️  Some issues found. Please fix the above problems.")
        print("🔧 Quick fix: docker-compose down && docker-compose up -d")
    
    return all_good

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)