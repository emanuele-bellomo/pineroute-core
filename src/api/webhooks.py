from fastapi import APIRouter, Depends, Request, status
from loguru import logger
from models.schemas import WebhookPayload
from api.dependencies import verify_passphrase

router = APIRouter()

@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(payload: WebhookPayload, request: Request):
    """
    Receives TradingView alerts, validates the passphrase, 
    and enqueues the task for async execution.
    """
    # Verify Passphrase
    verify_passphrase(payload.passphrase)
    
    logger.info(f"Received valid signal: {payload.strategy} - {payload.action} for {payload.symbol}")

    # Access the Redis queue from app state
    redis_pool = request.app.state.redis
    if not redis_pool:
        logger.error("Redis pool is not initialized")
        return {"status": "error", "message": "Internal queue error"}

    # Enqueue the execution task
    # We pass the payload as a dictionary
    try:
        await redis_pool.enqueue_job(
            'execute_trading_signal',
            payload.dict(exclude={'passphrase'})
        )
        logger.info(f"Enqueued execute_trading_signal job for {payload.symbol}")
    except Exception as e:
        logger.error(f"Failed to enqueue task: {e}")
        return {"status": "error", "message": "Failed to queue task"}

    return {"status": "success", "message": "Signal queued for execution"}
