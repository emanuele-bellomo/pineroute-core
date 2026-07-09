import hashlib

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger

from models.schemas import WebhookPayload
from api.dependencies import verify_passphrase

router = APIRouter()

# How long we remember a signal's fingerprint before allowing an identical
# one through again. This guards against TradingView (or the network)
# redelivering the same alert, not against a strategy re-firing later.
DUPLICATE_SIGNAL_WINDOW_SECONDS = 10


def _build_idempotency_key(payload: WebhookPayload) -> str:
    """Fingerprints the tradeable fields of a signal so exact retries are detectable."""
    fingerprint = "|".join(str(field) for field in (
        payload.strategy, payload.action, payload.symbol,
        payload.quantity, payload.price, payload.side,
    ))
    digest = hashlib.sha256(fingerprint.encode()).hexdigest()
    return f"pineroute:signal:{digest}"


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(payload: WebhookPayload, request: Request):
    """
    Receives TradingView alerts, validates the passphrase,
    and enqueues the task for async execution.
    """
    # Verify Passphrase
    verify_passphrase(payload.passphrase, request)

    logger.info(f"Received valid signal: {payload.strategy} - {payload.action} for {payload.symbol}")

    # Access the Redis queue from app state. `request.app.state` raises
    # AttributeError for unset attributes rather than returning None, so a
    # plain `.redis` access here would crash instead of hitting the
    # "not initialized" branch below.
    redis_pool = getattr(request.app.state, "redis", None)
    if redis_pool is None:
        logger.error("Redis pool is not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal queue error"
        )

    # Idempotency guard: reject an exact repeat of a signal seen moments ago
    # instead of silently double-executing the trade.
    idempotency_key = _build_idempotency_key(payload)
    is_new_signal = await redis_pool.set(
        idempotency_key, "1", nx=True, ex=DUPLICATE_SIGNAL_WINDOW_SECONDS
    )
    if not is_new_signal:
        logger.warning(f"Duplicate signal ignored for {payload.symbol} ({payload.action})")
        return {"status": "duplicate_ignored", "message": "Identical signal already queued recently"}

    # Enqueue the execution task
    # We pass the payload as a dictionary
    try:
        await redis_pool.enqueue_job(
            'execute_trading_signal',
            payload.model_dump(exclude={'passphrase'})
        )
        logger.info(f"Enqueued execute_trading_signal job for {payload.symbol}")
    except Exception as e:
        logger.error(f"Failed to enqueue task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue task"
        )

    return {"status": "success", "message": "Signal queued for execution"}
