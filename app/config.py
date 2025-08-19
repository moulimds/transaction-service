from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"  # default for local
    redis_db: int = 0

    # Posting Service Configuration
    posting_service_url: str = "http://localhost:8080"

    # Worker Configuration
    worker_concurrency: int = 10
    max_retries: int = 5
    retry_delay: int = 2

    # Performance Configuration
    response_timeout_ms: int = 100
    queue_max_size: int = 10000

    # Monitoring
    metrics_enabled: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

# Adjust Redis URL if running in Docker (detect using environment variable)
if os.environ.get("DOCKER_ENV") == "1":
    settings.redis_url = "redis://transaction_service-redis-1:6379/0"
