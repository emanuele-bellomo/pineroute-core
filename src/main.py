import sys
import uvloop
import asyncio
from fastapi import FastAPI
from loguru import logger
from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings
from api.webhooks import router as webhooks_router

# Replace standard asyncio event loop with uvloop for higher performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

def setup_logging():
    """
    Configure loguru to act as the central logger.
    """
    # Remove default handler
    logger.remove()
    
    # Add a custom handler with detailed formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )

# Initialize application
setup_logging()

app = FastAPI(
    title="PineRoute Bridge",
    description="Automated Trading Bridge for TradingView signals",
    version="0.1.0"
)

app.include_router(webhooks_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger.info("PineRoute Bridge is starting up...")
    # Initialize ARQ Redis Pool
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    app.state.redis = await create_pool(redis_settings)
    logger.info("Redis connection pool created")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("PineRoute Bridge is shutting down...")
    if hasattr(app.state, "redis"):
        app.state.redis.close()
        await app.state.redis.wait_closed()
        logger.info("Redis connection pool closed")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
