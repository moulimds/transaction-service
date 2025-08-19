#!/bin/bash
set -e

echo "🔍 Validating Implementation..."

# Start services
docker-compose up -d
sleep 5

# Start the service in background
python run.py &
SERVICE_PID=$!
sleep 3

# Run validation tests
echo "✅ Testing API response time..."
RESPONSE_TIME=$(curl -w "%{time_total}" -o /dev/null -s -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.50, "currency": "USD", "description": "Validation test"}')

if (( $(echo "$RESPONSE_TIME < 0.1" | bc -l) )); then
    echo "✅ Response time: ${RESPONSE_TIME}s (< 100ms) ✓"
else
    echo "❌ Response time: ${RESPONSE_TIME}s (> 100ms) ✗"
fi

# Test health endpoint
echo "✅ Testing health endpoint..."
HEALTH_STATUS=$(curl -s http://localhost:8000/api/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ Health check: $HEALTH_STATUS ✓"
else
    echo "❌ Health check: $HEALTH_STATUS ✗"
fi

# Test transaction status
echo "✅ Testing transaction status..."
TRANSACTION_ID=$(curl -s -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 50.25, "currency": "EUR", "description": "Status test"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['transactionId'])")

STATUS_RESPONSE=$(curl -s http://localhost:8000/api/transactions/$TRANSACTION_ID)
echo "✅ Status response: $STATUS_RESPONSE"

# Cleanup
kill $SERVICE_PID
docker-compose down

echo "🎉 Validation complete!"