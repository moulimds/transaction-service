from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import time
import logging
from app.models import TransactionRequest, TransactionResponse, HealthResponse
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_transaction_service() -> TransactionService:
    return TransactionService()

@router.post("/api/transactions", response_model=TransactionResponse)
async def submit_transaction(
    transaction: TransactionRequest,
    service: TransactionService = Depends(get_transaction_service)
):
    """Submit a transaction for processing"""
    start_time = time.time()
    
    try:
        response = await service.submit_transaction(transaction)
        
        # Ensure sub-100ms response time
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > 100:
            logger.warning(f"Response time exceeded 100ms: {elapsed_ms:.2f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"Error submitting transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/api/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_status(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction status"""
    try:
        response = await service.get_transaction_status(transaction_id)
        if not response:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/api/health", response_model=HealthResponse)
async def health_check(
    service: TransactionService = Depends(get_transaction_service)
):
    """System health check"""
    try:
        queue_depth = service.get_queue_depth()
        
        return HealthResponse(
            status="healthy",
            queue_depth=queue_depth,
            error_rate=0.0,  # TODO: Implement error rate calculation
            uptime=time.time(),  # TODO: Track actual uptime
            worker_status={"active_workers": 10}  # TODO: Track actual worker status
        )
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )