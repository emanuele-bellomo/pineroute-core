from fastapi import FastAPI, HTTPException, Depends
from models import WebhookPayload
from config import settings
from exchange import exchange_manager
import logging

# Basic logging configuration to output INFO level messages to the console.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI application.
app = FastAPI(title="UniStrat Trading Bridge")

@app.get("/")
async def root():
    """
    Health check endpoint to verify the bridge is online.
    """
    return {"message": "UniStrat Trading Bridge is running"}

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    """
    The main endpoint that receives TradingView alerts.
    It validates the passphrase, logs the signal, and triggers order execution.
    """
    # 1. Security Check: Validate the incoming passphrase against our local settings.
    if payload.passphrase != settings.WEBHOOK_PASSPHRASE:
        logger.warning(f"Unauthorized access attempt with passphrase: {payload.passphrase}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Log the details of the received signal for auditing.
    logger.info(f"Received signal: {payload.strategy} - {payload.action} for {payload.symbol}")

    # 2. Process Signal: Pass the validated data to the exchange manager.
    # In this draft, this currently simulates the trade rather than executing it.
    result = exchange_manager.execute_order(
        symbol=payload.symbol,
        action=payload.action,
        amount=payload.quantity
    )
    
    # If the exchange manager reports an error, return a 500 Internal Server Error.
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    # Return the success status and the details of the (simulated) trade.
    return {"status": "success", "result": result}

# Entry point for running the application directly via 'python app.py'.
if __name__ == "__main__":
    import uvicorn
    # Start the Uvicorn server on all network interfaces at port 8000.
    uvicorn.run(app, host="0.0.0.0", port=8000)
