import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# load_dotenv reads key-value pairs from a .env file and sets them as environment variables.
load_dotenv()

# Settings handles the configuration of the application using environment variables.
# It provides default values if the environment variables are not found.
class Settings(BaseSettings):
    # Security token used to validate incoming webhooks.
    WEBHOOK_PASSPHRASE: str = os.getenv("WEBHOOK_PASSPHRASE", "default_passphrase")
    
    # The identifier for the crypto exchange (e.g., 'binance', 'kraken').
    EXCHANGE_ID: str = os.getenv("EXCHANGE_ID", "binance")
    
    # API credentials for the exchange.
    API_KEY: str = os.getenv("API_KEY", "")
    API_SECRET: str = os.getenv("API_SECRET", "")
    
    # Flag to determine if the bridge should use the exchange's testnet/sandbox.
    PAPER_TRADING: bool = os.getenv("PAPER_TRADING", "True").lower() == "true"
    
    class Config:
        # Specifies the source file for environment variables.
        env_file = ".env"

# Create a singleton instance of the settings to be used throughout the application.
settings = Settings()
