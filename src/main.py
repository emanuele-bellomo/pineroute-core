import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from arq import create_pool
from arq.connections import RedisSettings

from core.config import settings
from api.webhooks import router as webhooks_router


def setup_logging():
    """
    Configure loguru to act as the central logger.
    """
    # Remove default handler
    logger.remove()

    # Add a custom handler with detailed formatting
    logger.add(sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )


# Initialize application
setup_logging()


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # --- Startup ---
    logger.info("PineRoute Bridge is starting up...")
    # Initialize ARQ Redis Pool
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    fastapi_app.state.redis = await create_pool(redis_settings)
    logger.info("Redis connection pool created")

    yield  # App runs here

    # --- Shutdown ---
    logger.info("PineRoute Bridge is shutting down...")
    if hasattr(fastapi_app.state, "redis"):
        await fastapi_app.state.redis.aclose()
        logger.info("Redis connection pool closed")

app = FastAPI(
    title="PineRoute Bridge",
    description="Automated Trading Bridge for TradingView signals",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(webhooks_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
