import secrets

from fastapi import HTTPException, Request, status
from loguru import logger
from src.core.config import settings

def verify_passphrase(passphrase: str, request: Request):
    """
    Dependency to verify the webhook passphrase.
    """
    expected_passphrase = settings.WEBHOOK_PASSPHRASE.get_secret_value()
    # Constant-time comparison: a plain `!=` short-circuits on the first
    # differing byte, which leaks how many leading characters were guessed
    # correctly to anyone timing responses.
    if not secrets.compare_digest(passphrase, expected_passphrase):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Unauthorized webhook access attempt from {client_host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase"
        )
    return True
