from typing import Dict, Any
from loguru import logger
from arq.connections import RedisSettings

from src.core.config import settings
from src.services.exchange import ExchangeManager
from src.models.schemas import WebhookPayload

async def startup(ctx: Dict[str, Any]) -> None:
    """
    ARQ worker startup event.
    Initializes the ExchangeManager and attaches it to the context.
    """
    logger.info("Worker starting up. Initializing Exchange Manager...")
    exchange_manager = ExchangeManager()
    await exchange_manager.initialize_exchange()
    ctx['exchange'] = exchange_manager
    # Note: ctx['redis'] is automatically injected by ARQ and contains the redis pool.
    logger.info("Worker startup complete.")

async def shutdown(ctx: Dict[str, Any]) -> None:
    """
    ARQ worker shutdown event.
    Closes the exchange connection gracefully.
    """
    logger.info("Worker shutting down...")
    exchange_manager: ExchangeManager | None = ctx.get('exchange')
    if exchange_manager:
        await exchange_manager.close_exchange()
    logger.info("Worker shutdown complete.")

async def execute_trading_signal(ctx, payload: dict) -> dict:
    """
    Background task to execute a trading signal.

    Idempotency (dropping duplicate deliveries of the same alert) is handled
    upstream in `src/api/webhooks.py` via an atomic Redis `SET NX EX` before
    the job is ever enqueued, so there is nothing to de-duplicate here.
    """
    signal = WebhookPayload.model_validate({**payload, "passphrase": "-"})
    exchange_manager: ExchangeManager = ctx.get('exchange')

    logger.info(f"Processing trading signal from queue: {payload}")

    try:

        # Execute the order via exchange manager
        result = await exchange_manager.execute_order(
            symbol=signal.symbol,
            action=signal.action,
            amount=signal.quantity,
            price=signal.price
        )

        logger.info(f"Successfully processed signal for {payload.get('symbol')}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error processing trading signal for {payload.get('symbol')}: {e}")
        # Raising an exception here lets ARQ handle retries if configured
        raise

class WorkerSettings:
    """
    Settings for the ARQ worker.
    To run the worker (from the project root): `arq src.workers.queue.WorkerSettings`
    """
    functions = [execute_trading_signal]
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    on_startup = startup
    on_shutdown = shutdown
    # ARQ defaults to 5 max_jobs, 10 seconds retry, etc. Can be tuned here.
    max_jobs = 10
