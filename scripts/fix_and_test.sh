set -e

echo "🔧 Fixing integration test issues..."

# Stop any running services
docker-compose down

# Pull latest posting service image
docker pull vinhopenfabric/mock-posting-service:latest

# Start services with fresh state
docker-compose up -d

# Wait longer for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 15

# Run diagnostics
python scripts/diagnose.py

# If diagnostics pass, run tests
if [ $? -eq 0 ]; then
    echo "✅ Running integration tests..."
    pytest tests/test_integration.py -v -s
else
    echo "❌ Diagnostics failed. Please check service status."
fi
```

## Immediate Fix Instructions

Run these commands to fix your current issues:

```bash
# 1. Stop everything and start fresh
docker-compose down
docker-compose up -d

# 2. Wait for services
sleep 15

# 3. Test posting service directly
python scripts/debug_posting_service.py

# 4. If posting service works, run diagnostics
python scripts/diagnose.py

# 5. Run fixed integration tests
pytest tests/test_integration.py -v -s