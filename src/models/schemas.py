import orjson
from pydantic import BaseModel
from typing import Optional

def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()

class WebhookPayload(BaseModel):
    passphrase: str      # Security token to verify the request is from a trusted source.
    strategy: str        # Name of the PineScript strategy that triggered the alert.
    action: str          # The trade command (e.g., "buy", "sell", "long", "short", "exit").
    symbol: str          # The trading pair (e.g., "BTC/USDT").
    price: Optional[float] = None     # The price at the time of the alert (optional).
    quantity: Optional[float] = None  # The amount to trade (optional).
    side: Optional[str] = None        # Additional field for granular trade direction if needed.

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
