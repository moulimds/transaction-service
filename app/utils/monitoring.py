import time
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        
    def record_request(self, response_time_ms: float, success: bool):
        """Record a request metric"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        self.response_times.append(response_time_ms)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = time.time() - self.start_time
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_percent": error_rate,
            "average_response_time_ms": avg_response_time,
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0
        }

# Global metrics collector
metrics = MetricsCollector()