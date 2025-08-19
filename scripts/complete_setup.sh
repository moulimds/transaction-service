#!/bin/bash
set -e

echo "🚀 Setting up High Performance Transaction Processing Service"

# Phase 1: Environment Setup
echo "📦 Setting up environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Phase 2: Start Dependencies
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Test Redis
echo "📡 Testing Redis connection..."
timeout 30 bash -c 'until redis-cli -h localhost -p 6379 ping; do sleep 1; done'

# Test Posting Service
echo "🎯 Testing Posting Service..."
timeout 30 bash -c 'until curl -f http://localhost:8080/transactions 2>/dev/null; do sleep 1; done'

echo "✅ Setup complete!"
echo ""
echo "🏃‍♂️ To start the service: python run.py"
echo "🧪 To run tests: pytest"
echo "⚡ To run load test: python scripts/performance_test.py"