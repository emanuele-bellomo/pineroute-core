from typing import Optional
import ccxt
from config import settings
import logging

# Initialize a logger for this module to track exchange operations and errors.
logger = logging.getLogger(__name__)

class ExchangeManager:
    """
    ExchangeManager handles the connection to the cryptocurrency exchange 
    and translates strategy signals into actual trade orders.
    """
    def __init__(self):
        # Load configuration from the central settings object.
        self.exchange_id = settings.EXCHANGE_ID
        self.api_key = settings.API_KEY
        self.api_secret = settings.API_SECRET
        self.paper_trading = settings.PAPER_TRADING
        # Initialize the CCXT exchange instance.
        self.exchange = self._initialize_exchange()

    def _initialize_exchange(self):
        """
        Dynamically instantiates the exchange class based on the EXCHANGE_ID setting.
        Configures API keys and toggles sandbox (testnet) mode if requested.
        """
        # Check if CCXT supports the requested exchange.
        if not hasattr(ccxt, self.exchange_id):
            raise ValueError(f"Exchange {self.exchange_id} not supported by CCXT")
        
        # Get the class for the exchange (e.g., ccxt.binance) and instantiate it.
        exchange_class = getattr(ccxt, self.exchange_id)
        exchange = exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True, # Required by most exchanges to avoid IP bans.
        })
        
        # If paper trading is enabled, try to switch to the exchange's sandbox/testnet environment.
        if self.paper_trading:
            if 'test' in exchange.urls:
                exchange.set_sandbox_mode(True)
                logger.info(f"Initialized {self.exchange_id} in SANDBOX mode")
            else:
                logger.warning(f"Exchange {self.exchange_id} does not support sandbox mode. Using LIVE mode!")
        
        return exchange

    def execute_order(self, symbol: str, action: str, amount: Optional[float] = None):
        """
        Translates a generic strategy action into a specific order on the exchange.
        Args:
            symbol: The trading pair (e.g., BTC/USDT).
            action: The signal type ('buy', 'long', 'sell', 'short', 'exit').
            amount: The size of the trade.
        """
        try:
            # Map common TradingView signal terminology to exchange actions.
            
            # Handling Buy/Long signals.
            if action.lower() in ['buy', 'long']:
                logger.info(f"Executing BUY order for {symbol}")
                # Placeholder: In a real implementation, you would call:
                # order = self.exchange.create_market_buy_order(symbol, amount)
                return {"status": "simulated_buy", "symbol": symbol}
            
            # Handling Sell/Short signals.
            elif action.lower() in ['sell', 'short']:
                logger.info(f"Executing SELL order for {symbol}")
                # Placeholder: In a real implementation, you would call:
                # order = self.exchange.create_market_sell_order(symbol, amount)
                return {"status": "simulated_sell", "symbol": symbol}
            
            # Handling Exit/Close signals to flatten positions.
            elif action.lower() in ['exit', 'cash', 'close']:
                logger.info(f"Executing EXIT order for {symbol}")
                # Logic to close existing positions would be implemented here.
                return {"status": "simulated_exit", "symbol": symbol}
            
            # Error handling for unrecognized signal types.
            else:
                logger.error(f"Unknown action: {action}")
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            # Catch any CCXT or network errors and log them.
            logger.error(f"Error executing order: {e}")
            return {"status": "error", "message": str(e)}

# Create a singleton instance to be used by the FastAPI app.
exchange_manager = ExchangeManager()
