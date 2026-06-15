from pydantic import BaseModel
from typing import Optional

class WebhookPayload(BaseModel):
    passphrase: str
    strategy: str
    action: str  # e.g., "buy", "sell", "long", "short", "exit"
    symbol: str
    price: Optional[float] = None
    quantity: Optional[float] = None
    side: Optional[str] = None # For more granular control if needed
