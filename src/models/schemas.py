from pydantic import BaseModel, field_validator
from typing import Optional

# Must stay in sync with the actions ExchangeManager.execute_order understands.
SUPPORTED_ACTIONS = {"buy", "long", "sell", "short", "exit", "cash", "close"}

class WebhookPayload(BaseModel):
    passphrase: str      # Security token to verify the request is from a trusted source.
    strategy: str        # Name of the PineScript strategy that triggered the alert.
    action: str          # The trade command (e.g., "buy", "sell", "long", "short", "exit").
    symbol: str          # The trading pair (e.g., "BTC/USDT").
    price: Optional[float] = None     # The price at the time of the alert (optional).
    quantity: Optional[float] = None  # The amount to trade (optional).
    side: Optional[str] = None        # Additional field for granular trade direction if needed.

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        # Reject unrecognized actions here (a clean 422) instead of letting them
        # reach the worker, where a failure is just a log line TradingView never sees.
        normalized = value.lower()
        if normalized not in SUPPORTED_ACTIONS:
            raise ValueError(f"action must be one of {sorted(SUPPORTED_ACTIONS)}")
        return normalized
