from fastapi import HTTPException, status
from loguru import logger
from core.config import settings

def verify_passphrase(passphrase: str):
    """
    Dependency to verify the webhook passphrase.
    """
    if passphrase != settings.WEBHOOK_PASSPHRASE.get_secret_value():
        logger.warning(f"Unauthorized webhook access attempt.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase"
        )
    return True
