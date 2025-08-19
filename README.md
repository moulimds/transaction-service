# High Performance Transaction Processing Service

[![Python](https://img.shields.io/badge/python-3.11-blue)]() [![Redis](https://img.shields.io/badge/redis-7-orange)]()

A high-performance, reliable transaction processing service providing **sub-100ms API responses**, zero data loss, and no duplicates. Designed to handle unreliable posting services at high throughput.

---

## ⚡ Features
- **Immediate Response**: API responds in <100ms  
- **Reliable Delivery**: Zero transaction loss  
- **Duplicate Prevention**: Idempotent via UUID & GET verification  
- **Status Tracking**: `pending | processing | completed | failed`  
- **High Throughput**: 1000+ TPS  
- **Retry Mechanism**: Handles pre-write & post-write failures  
- **Monitoring**: Health endpoint with queue depth, errors, retries  

---

##  Quick Start

```bash
git clone https://github.com/moulimds/transaction-service
cd transaction-processing-service

# Start dependencies
docker run -d -p 6379:6379 redis:7-alpine
docker run -p 8080:8080 vinhopenfabric/mock-posting-service:latest

# Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start service
python run.py

# Run tests
pytest -v

Request:
{
  "amount": 100.50,
  "currency": "USD",
  "description": "Payment",
  "metadata": {"order_id":"12345"}
}

Response (<100ms):
{
  "transactionId": "uuid",
  "status": "pending",
  "submittedAt": "2025-08-19T12:00:00Z",
  "completedAt": null,
  "error": null
}

Response:
{
  "transactionId": "uuid",
  "status": "processing|completed|failed",
  "submittedAt": "...",
  "completedAt": "...",
  "error": "string (if failed)"
}

Response:
{
  "status": "healthy",
  "queueDepth": 123,
  "retryCount": 5,
  "errorRate": 0.02
}
```
## ⚙️ Design Highlights

Queue: Redis for async high-throughput processing

Deduplication: Track UUID, verify via GET before POST

Retries: Exponential backoff for failed submissions

Horizontal Scaling: Worker pool can scale independently

Observability: Queue depth, errors, retries, response times

## 🧪 Testing

Unit tests for services

Integration tests with mock posting service

Load testing up to 1000+ TPS

Use POST /cleanup to reset state between tests

## 📂 Structure

app/         # API, services, utils

tests/       # Unit & integration tests

scripts/     # Setup & validation scripts

requirements.txt

run.py

Dockerfile

docker-compose.yml

README.md


