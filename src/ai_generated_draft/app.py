from fastapi import FastAPI, HTTPException, Depends
from .models import WebhookPayload
from .config import settings
from .exchange import exchange_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UniStrat Trading Bridge")

@app.get("/")
async def root():
    return {"message": "UniStrat Trading Bridge is running"}

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    # 1. Validate Passphrase
    if payload.passphrase != settings.WEBHOOK_PASSPHRASE:
        logger.warning(f"Unauthorized access attempt with passphrase: {payload.passphrase}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"Received signal: {payload.strategy} - {payload.action} for {payload.symbol}")

    # 2. Process Signal
    result = exchange_manager.execute_order(
        symbol=payload.symbol,
        action=payload.action,
        amount=payload.quantity
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return {"status": "success", "result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
