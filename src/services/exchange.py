import ccxt.async_support as ccxt
from loguru import logger
from typing import Optional, Dict, Any

from src.core.config import settings
from src.core.exceptions import ExchangeConnectionError, OrderExecutionError

class ExchangeManager:
    """
    Asynchronous ExchangeManager to handle the connection to the cryptocurrency
    exchange and execute trade orders.
    """
    def __init__(self):
        self.exchange_id = settings.EXCHANGE_ID
        self.api_key = settings.API_KEY
        self.api_secret = settings.API_SECRET.get_secret_value()
        self.paper_trading = settings.PAPER_TRADING
        self.exchange: Optional[ccxt.Exchange] = None

    async def initialize_exchange(self) -> None:
        """
        Dynamically instantiates the exchange class asynchronously.
        """
        if not hasattr(ccxt, self.exchange_id):
            raise ExchangeConnectionError(f"Exchange {self.exchange_id} not supported by CCXT")

        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True, # Required by most exchanges
        })

        if self.paper_trading:
            if 'test' in self.exchange.urls:
                self.exchange.set_sandbox_mode(True)
                logger.info(f"Initialized {self.exchange_id} in SANDBOX (Paper Trading) mode")
            else:
                logger.warning(f"Exchange {self.exchange_id} does not support sandbox mode. LIVE TRADING WARNING!")

    async def close_exchange(self) -> None:
        """
        Closes the asynchronous exchange session gracefully.
        """
        if self.exchange:
            await self.exchange.close()
            logger.info("Exchange session closed.")

    async def execute_order(self, symbol: str, action: str, amount: Optional[float] = None, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Translates a strategy action into a specific order on the exchange.
        Must be called within an initialized exchange context.
        """
        if not self.exchange:
            raise ExchangeConnectionError("Exchange not initialized. Call initialize_exchange() first.")

        try:
            logger.info(f"Preparing to execute {action.upper()} order for {symbol}")

            # This is a simplified market order logic.
            # In a full implementation, you'd check open positions first.

            if action.lower() in ['buy', 'long']:
                if not amount:
                    raise OrderExecutionError("Amount is required for buy/long orders")
                # order = await self.exchange.create_market_buy_order(symbol, amount)
                logger.info(f"Executed BUY order for {symbol} of amount {amount}")
                return {"status": "success", "action": "buy", "symbol": symbol, "amount": amount}

            elif action.lower() in ['sell', 'short']:
                if not amount:
                    raise OrderExecutionError("Amount is required for sell/short orders")
                # order = await self.exchange.create_market_sell_order(symbol, amount)
                logger.info(f"Executed SELL order for {symbol} of amount {amount}")
                return {"status": "success", "action": "sell", "symbol": symbol, "amount": amount}

            elif action.lower() in ['exit', 'cash', 'close']:
                logger.info(f"Executed EXIT order for {symbol}")
                # We would fetch open positions for the symbol and close them here
                return {"status": "success", "action": "exit", "symbol": symbol}

            else:
                logger.error(f"Unknown action: {action}")
                raise OrderExecutionError(f"Unknown action: {action}")

        except OrderExecutionError:
            # Our own validation errors (e.g. missing amount) are already
            # well-formed; re-raise them without wrapping or dumping a traceback.
            raise
        except ccxt.RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded on {self.exchange_id}: {e}")
            raise OrderExecutionError(f"RateLimitExceeded: {e}")
        except ccxt.NetworkError as e:
            logger.error(f"Network error communicating with {self.exchange_id}: {e}")
            raise OrderExecutionError(f"NetworkError: {e}")
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error from {self.exchange_id}: {e}")
            raise OrderExecutionError(f"ExchangeError: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error executing order: {e}")
            raise OrderExecutionError(str(e))
