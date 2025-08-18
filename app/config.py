from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
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