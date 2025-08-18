set -e

echo "Setting up Transaction Processing Service..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start services with Docker Compose
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Test posting service
echo "Testing posting service..."
curl -f http://localhost:8080/transactions || echo "Posting service not ready"

# Test Redis
echo "Testing Redis..."
redis-cli -h localhost -p 6379 ping || echo "Redis not ready"

echo "Setup complete!"
echo "To run the service: python run.py"
echo "To run tests: pytest"
echo "To run load test: python scripts/performance_test.py"