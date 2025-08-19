from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TransactionRequest(BaseModel):
    model_config = ConfigDict(
        # Use ConfigDict instead of deprecated Config class
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: float = Field(..., gt=0, description="Transaction amount (positive)")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    description: str = Field(..., min_length=1, max_length=255)
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = None

class TransactionResponse(BaseModel):
    transactionId: str
    status: TransactionStatus
    submittedAt: datetime
    completedAt: Optional[datetime] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    queue_depth: int
    error_rate: float
    uptime: float
    worker_status: Dict[str, Any]