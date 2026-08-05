from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    """Application configuration via environment variables (or a .env file)."""

    WEBHOOK_PASSPHRASE: SecretStr # No default: required

    # Exchange configuration
    EXCHANGE_ID: str = "binance"
    API_KEY: str = ""
    API_SECRET: SecretStr = SecretStr("")

    # If True, use the exchange's testnet environment.
    PAPER_TRADING: bool = True

    # Redis configuration for ARQ
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton instance
settings = Settings()
