from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Posting Service")

# In-memory storage for transactions
transactions_db: Dict[str, dict] = {}

class TransactionRequest(BaseModel):
    id: str
    amount: float
    timestamp: str

@app.post("/transactions")
async def create_transaction(transaction: TransactionRequest):
    if transaction.id in transactions_db:
        raise HTTPException(status_code=400, detail="Transaction already exists")
    transactions_db[transaction.id] = transaction.dict()
    logger.info(f"Transaction {transaction.id} stored successfully")
    return {"message": "Transaction stored"}

@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    if transaction_id not in transactions_db:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transactions_db[transaction_id]

@app.post("/cleanup")
async def cleanup_transactions():
    transactions_db.clear()
    logger.info("All transactions cleared")
    return {"message": "All transactions cleared"}
