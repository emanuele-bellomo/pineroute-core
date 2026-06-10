from typing import Optional
import ccxt
from .config import settings
import logging

logger = logging.getLogger(__name__)

class ExchangeManager:
    def __init__(self):
        self.exchange_id = settings.EXCHANGE_ID
        self.api_key = settings.API_KEY
        self.api_secret = settings.API_SECRET
        self.paper_trading = settings.PAPER_TRADING
        self.exchange = self._initialize_exchange()

    def _initialize_exchange(self):
        if not hasattr(ccxt, self.exchange_id):
            raise ValueError(f"Exchange {self.exchange_id} not supported by CCXT")
        
        exchange_class = getattr(ccxt, self.exchange_id)
        exchange = exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        
        if self.paper_trading:
            if 'test' in exchange.urls:
                exchange.set_sandbox_mode(True)
                logger.info(f"Initialized {self.exchange_id} in SANDBOX mode")
            else:
                logger.warning(f"Exchange {self.exchange_id} does not support sandbox mode. Using LIVE mode!")
        
        return exchange

    def execute_order(self, symbol: str, action: str, amount: Optional[float] = None):
        """
        Execute an order on the exchange.
        action: 'buy', 'sell', 'long', 'short', 'exit'
        """
        try:
            # Placeholder for actual order logic
            # TradingView usually sends "Long" or "Short" or "Cash" (Exit)
            # We need to map these to exchange actions
            
            if action.lower() in ['buy', 'long']:
                logger.info(f"Executing BUY order for {symbol}")
                # order = self.exchange.create_market_buy_order(symbol, amount)
                return {"status": "simulated_buy", "symbol": symbol}
            
            elif action.lower() in ['sell', 'short']:
                logger.info(f"Executing SELL order for {symbol}")
                # order = self.exchange.create_market_sell_order(symbol, amount)
                return {"status": "simulated_sell", "symbol": symbol}
            
            elif action.lower() in ['exit', 'cash', 'close']:
                logger.info(f"Executing EXIT order for {symbol}")
                # Logic to close existing positions
                return {"status": "simulated_exit", "symbol": symbol}
            
            else:
                logger.error(f"Unknown action: {action}")
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {"status": "error", "message": str(e)}

exchange_manager = ExchangeManager()
