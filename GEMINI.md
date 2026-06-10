# UniStrat: Automated Trading Bridge

A Python-based automated trading bridge that connects TradingView PineScript strategy webhooks to cryptocurrency exchanges using the CCXT library.

## Project Overview
- **Source:** TradingView (PineScript strategies)
- **Signal Method:** Webhooks (JSON payload)
- **Execution:** Python script utilizing `ccxt`
- **Current Strategies:**
    - `koenigsegg.pine`: Multi-indicator trend strategy.
    - `koenigsegg_DC.pine`: Daily Confirmation version of the Koenigsegg strategy.

## Tech Stack & Dependencies
- **Language:** Python 3.10+ (PEP 8 compliance, Type Hinting)
- **API Connectivity:** `ccxt`
- **Web Framework:** `fastapi` with `uvicorn`
- **Validation:** `pydantic`
- **Environment Management:** `python-dotenv`, `pydantic-settings`

## Engineering Standards

### Coding Standards
- **Style:** PEP 8 compliance.
- **Type Hinting:** Use type hints for all function signatures and complex variables.
- **Naming Conventions:**
    - Classes: `PascalCase`
    - Functions/Variables: `snake_case`
    - Constants: `SCREAMING_SNAKE_CASE`

### Architecture
- **Modularity:** Separate webhook handling, order execution, and exchange connectivity.
- **Error Handling:** Use robust try-except blocks, especially for network calls (CCXT). Implement retries where appropriate.
- **Security:**
    - Never hardcode API keys. Use environment variables.
    - Validate all incoming webhook requests using a shared secret or IP whitelist.

### Testing
- Use `pytest` for unit testing.
- Mock exchange responses for testing order execution logic without hitting real APIs.

## Roadmap
- [x] **Phase 1: Research & Setup**
    - [x] Analyze PineScript logic
    - [x] Initialize project structure
    - [x] Define engineering standards
- [ ] **Phase 2: Webhook Server**
    - [x] Implement endpoint to receive TradingView alerts
    - [ ] Add basic security (IP filtering or secret tokens)
- [ ] **Phase 3: Exchange Integration**
    - [ ] Setup CCXT client
    - [ ] Implement order execution logic (Market/Limit)
- [ ] **Phase 4: Monitoring & Logging**
    - [ ] Implement logging for trades and errors
    - [ ] Add Telegram/Discord notifications (optional)
- [ ] **Phase 5: Live Testing**
    - [ ] Test with paper trading/testnet
    - [ ] Deploy to production

## Directory Structure & File Explanations

Here is a simple breakdown of what each file in the `src/` folder does:

- **`app.py`**: The **Brain/Gateway**. This script runs the web server. It listens for incoming webhooks from TradingView, checks if the secret passphrase is correct, and then tells the `exchange.py` script what to do.
- **`exchange.py`**: The **Executor**. This script talks directly to your crypto exchange (Binance, Kraken, etc.) using the CCXT library. It handles the actual buying, selling, and closing of positions.
- **`models.py`**: The **Translator**. This defines the "shape" of the data we expect from TradingView. It ensures that if TradingView sends a message, it includes everything we need (like the symbol, price, and action) in the right format.
- **`config.py`**: The **Manager**. This script reads your private settings from the `.env` file (like your API keys and exchange name) and makes them available to the rest of the app safely.

---

## Webhook Payload Schema (Draft)
```json
{
  "passphrase": "your_secure_token",
  "strategy": "koenigsegg",
  "action": "buy/sell",
  "symbol": "{{ticker}}",
  "price": "{{close}}",
  "position_size": "100%"
}
```

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with API keys and secrets.
3. Run the server: `python src/app.py`
