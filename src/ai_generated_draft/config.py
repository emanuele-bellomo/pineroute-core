import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    WEBHOOK_PASSPHRASE: str = os.getenv("WEBHOOK_PASSPHRASE", "default_passphrase")
    EXCHANGE_ID: str = os.getenv("EXCHANGE_ID", "binance")
    API_KEY: str = os.getenv("API_KEY", "")
    API_SECRET: str = os.getenv("API_SECRET", "")
    PAPER_TRADING: bool = os.getenv("PAPER_TRADING", "True").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()
