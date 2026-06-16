from pydantic import BaseModel
from typing import Optional

# WebhookPayload defines the structure of the incoming JSON data from TradingView.
# Pydantic automatically validates that the incoming request contains all required fields
# and that the data types are correct.
class WebhookPayload(BaseModel):
    passphrase: str      # Security token to verify the request is from a trusted source.
    strategy: str        # Name of the PineScript strategy that triggered the alert.
    action: str          # The trade command (e.g., "buy", "sell", "long", "short", "exit").
    symbol: str          # The trading pair (e.g., "BTC/USDT").
    price: Optional[float] = None     # The price at the time of the alert (optional).
    quantity: Optional[float] = None  # The amount to trade (optional).
    side: Optional[str] = None        # Additional field for granular trade direction if needed.
