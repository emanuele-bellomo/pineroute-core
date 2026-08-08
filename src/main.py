import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from arq import create_pool
from arq.connections import RedisSettings

from src.core.config import settings
from src.api.webhooks import router as webhooks_router


# Making a custom logger setup
def setup_logging():
    """Loguru's logger custom configuration."""
    logger.remove() # Remove the standard one

    logger.add(sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )

setup_logging()

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """
    FastAPI's modern "lifespan" pattern. Creates an ARQ Redis pool and stores it on "app.state.redis".
    """
    # Startup
    logger.info("PineRoute Bridge is starting up...")
    # Initialize ARQ Redis Pool
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    fastapi_app.state.redis = await create_pool(redis_settings)
    logger.info("Redis connection pool created")

    yield  # App runs here

    # Shutdown
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


if __name__ == "__main__":
    # Allows launching the web server with `python -m src.main` from the
    # project root. The equivalent explicit command is
    # `uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload`.
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
