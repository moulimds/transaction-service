from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from contextlib import asynccontextmanager

from app.api.routes import router
from app.services.worker import TransactionWorker
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global worker instance
worker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global worker
    
    # Startup
    logger.info("Starting Transaction Processing Service")
    worker = TransactionWorker()
    
    # Start worker in background
    worker_task = asyncio.create_task(worker.start())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Transaction Processing Service")
    if worker:
        worker.stop()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

# Create FastAPI app
app = FastAPI(
    title="High Performance Transaction Processing Service",
    description="A reliable intermediary between clients and posting service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Transaction Processing Service is running"}