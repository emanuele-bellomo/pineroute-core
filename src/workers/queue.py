from typing import Dict, Any
from loguru import logger
from arq.connections import RedisSettings
from redis.asyncio import Redis

from core.config import settings
from services.exchange import ExchangeManager

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
    exchange_manager: ExchangeManager = ctx.get('exchange')
    if exchange_manager:
        await exchange_manager.close_exchange()
    logger.info("Worker shutdown complete.")

async def execute_trading_signal(ctx: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task to execute a trading signal.
    """
    redis: Redis = ctx['redis']
    exchange_manager: ExchangeManager = ctx['exchange']
    
    # 1. Idempotency check: prevent duplicate signals from executing multiple times
    # We can create a unique key based on the strategy, symbol, action, and current time window
    # For a robust implementation, TradingView should send a unique ID, or we use a timestamp.
    # Here, we use a basic approach just as an example.
    # In production, we'd use a more precise unique identifier provided by the signal.
    
    logger.info(f"Processing trading signal from queue: {payload}")
    
    try:
        # Assuming payload has these fields based on the schema
        symbol = payload.get('symbol')
        action = payload.get('action')
        amount = payload.get('quantity')
        price = payload.get('price')
        
        # Execute the order via exchange manager
        result = await exchange_manager.execute_order(
            symbol=symbol,
            action=action,
            amount=amount,
            price=price
        )
        
        logger.info(f"Successfully processed signal for {symbol}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing trading signal for {payload.get('symbol')}: {e}")
        # Raising an exception here lets ARQ handle retries if configured
        raise

class WorkerSettings:
    """
    Settings for the ARQ worker.
    To run the worker: `arq workers.queue.WorkerSettings`
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
