# PineRoute

A Python-based automated trading bridge that connects TradingView PineScript strategy webhooks to cryptocurrency exchanges using the CCXT library.

### First Steps

- Create a Python virtual environment by typing: `python -m venv .venv`
- Install dependencies by typing: `pip install -r requirements.txt`
- Make an `.env` file, copy `.env.example` to `.env`, fill in your `WEBHOOK_PASSPHRASE`, `API_KEY`, and `API_SECRET`.
- Configure your TradingView alerts to send a JSON payload to your server's `/webhook` endpoint matching the schema in `src/models.py`.
- **Order Logic Refinement**: The `ExchangeManager.execute_order` in `src/exchange.py` currently uses simulated responses. You will need to uncomment the CCXT calls and refine the position sizing logic.
- Start the server by typing: `python src/app.py`

### Project Structure (src folder)

Here is a simple breakdown of what each file in the `src/` folder does:

- **`app.py`**: The **Brain/Gateway**. This script runs the web server. It listens for incoming webhooks from TradingView, checks if the secret passphrase is correct, and then tells the `exchange.py` script what to do.
- **`exchange.py`**: The **Executor**. This script talks directly to your crypto exchange (Binance, Kraken, etc.) using the CCXT library. It handles the actual buying, selling, and closing of positions.
- **`models.py`**: The **Translator**. This defines the "shape" of the data we expect from TradingView. It ensures that if TradingView sends a message, it includes everything we need (like the symbol, price, and action) in the right format.
- **`config.py`**: The **Manager**. This script reads your private settings from the `.env` file (like your API keys and exchange name) and makes them available to the rest of the app safely.

### Webhook Payload Schema

To trigger a trade, your TradingView alert should send a JSON message like this:

```json
{
  "passphrase": "your_secure_token",
  "strategy": "koenigsegg",
  "action": "buy/sell",
  "symbol": "BTC/USDT",
  "price": 65000,
  "quantity": 0.01
}
```

### Roadmap

- [x] **Phase 1: Research & Setup**
    - [x] Analyze PineScript logic
    - [x] Initialize project structure
- [ ] **Phase 2: Webhook Server**
    - [x] Implement endpoint to receive TradingView alerts
    - [ ] Add basic security (IP filtering or secret tokens)
- [ ] **Phase 3: Exchange Integration**
    - [ ] Setup CCXT client
    - [ ] Implement order execution logic (Market/Limit)
- [ ] **Phase 4: Monitoring & Logging**
    - [ ] Implement logging for trades and errors
    - [ ] Add Telegram/Discord notifications
- [ ] **Phase 5: Live Testing**
    - [ ] Test with paper trading/testnet
    - [ ] Deploy to production
