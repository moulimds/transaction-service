set -e

echo "Running comprehensive tests..."

# Start services
docker-compose up -d
sleep 5

# Run unit tests
echo "Running unit tests..."
pytest tests/test_api.py -v

# Run integration tests  
echo "Running integration tests..."
pytest tests/test_integration.py -v

# Run load tests
echo "Running load tests..."
pytest tests/test_load.py -v

# Run performance test
echo "Running performance test..."
python scripts/performance_test.py --requests 500 --concurrency 25

echo "All tests completed!"