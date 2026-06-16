## Roadmap

- [ ] **Phase 1: Research & Setup**
    - [x] Initialize Project Structure
    - [ ] Start Coding (after module 31)
    - [ ] Study Python Libraries
- [ ] **Phase 2: Webhook Server**
    - [ ] Implement endpoint to receive TradingView alerts
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


## Tech Stack

- **Frontend** = Astro, Tailwind CSS (not open-source)
- **REST API** = Python FastAPI
- **Backend** = Python, C (optionally)
- **Database** = PostgreSQL


## C usage

**Advanced Risk Management (VaR Calculations)**: If you eventually let users set complex parameters—like "Do not execute this trade if my portfolio's Value at Risk (VaR) is above 5%"—your engine will have to pull their entire portfolio history and run Monte Carlo simulations in real-time before executing the webhook. Python will choke on this. C will do it instantly.

**High-Frequency Order Book Analysis**: If you move beyond simple TradingView webhooks and start ingesting live WebSocket data from Binance to check order book depth before routing a trade, you will be processing thousands of events per second. C is perfect for parsing this firehose of data.

**Custom Cryptography**: Encrypting and decrypting user API keys from the Postgres database needs to be fast and secure. While Python has libraries for this, writing a highly optimized C extension to handle the cryptographic keys in memory is a massive security and performance upgrade.

Use libraries like Cython to get C-level performance without writing in C; also use uvloop instead of asyncio and orjson instead of json libraries for more speed.


## Useful GitHub repos (State of the art analysis)

- **vlameiras/tradingview-webhook-integration**: * Why it's useful: This project is built using FastAPI, which is exactly what we decided to use for your src/api module. It bridges TradingView to Binance Futures. You can look at their app.py or router files to see exactly how they set up the FastAPI endpoints to receive JSON webhooks and validate them.

- **51bitquant/binance-tradingview-webhook-bot**: Why it's useful: A very popular bare-bones Python bot for Binance. While it uses Flask instead of FastAPI, it is a great reference for how to structure your .env loading, handle TradingView alert messages, and format the immediate market order execution logic.

- **freqtrade/freqtrade**: * Why it's useful: This is arguably the most famous open-source crypto trading bot in the world. It is written in Python and uses CCXT extensively. You shouldn't try to copy their entire architecture (it's massive), but you should absolutely dig into their codebase to see how they wrap CCXT API calls in try-except blocks, how they handle rate limits (RateLimitExceeded exceptions), and how they calculate position sizing safely.

- **marketcalls/openalgo**: Why it's useful: This is a comprehensive open-source algo trading platform that includes built-in webhook triggers for TradingView. It has order approval workflows, separate database isolation, and Telegram notifications. It's a great place to see how a "Dashboard/SaaS" layout is structured alongside a trading engine.

- **ccxt/ccxt (Examples Folder)**: Why it's useful: The official CCXT repository has a dedicated folder just for Python examples. Before you ask an AI or write your own code to place a "Limit Buy" or a "Stop Loss" order, look here. They have hundreds of short, highly optimized scripts showing exactly how to use ccxt.async_support properly.


## Libraries in `requirements.txt`

*   **`ccxt`**: The backbone of the execution layer. It provides a unified way to connect to and trade on over 100 cryptocurrency exchanges.
*   **`fastapi` & `uvicorn`**: These form the web server. `fastapi` handles the incoming webhook requests from TradingView, and `uvicorn` is the high-performance server that runs the code.
*   **`pydantic` & `pydantic-settings`**: Used for data integrity. `pydantic` ensures the incoming JSON from TradingView follows a strict format, while `pydantic-settings` manages your sensitive configuration (like API keys) safely.
*   **`python-dotenv`**: A utility to load environment variables from a `.env` file into your application.
*   **`requests`**: A standard library for making HTTP requests. *Note: Since your standards require asynchronous execution, this library should likely be replaced by `httpx` or `aiohttp` to avoid blocking the system.
*   **`uvloop`**: This is a drop-in replacement for Python's default asyncio event loop. It is written in Cython (C) and makes Python's asynchronous networking almost as fast as Go or Node.js.
*   **`orjson`**: Instead of Python's built-in json library, use orjson (written in Rust). It parses incoming TradingView webhooks exponentially faster.


## Initial code generated by AI

*   **`app.py` (The Gatekeeper)**: This is the entry point. It sets up an API endpoint (`/webhook`) that listens for signals. It performs a basic "passphrase" check to ensure only your TradingView signals can trigger trades.
*   **`models.py` (The Blueprint)**: Defines exactly what a "Signal" looks like. It expects fields like `strategy`, `action` (buy/sell), `symbol`, and `quantity`. If TradingView sends something different, the system will reject it immediately.
*   **`config.py` (The Vault)**: Centralizes all settings. It pulls your API keys and the "Paper Trading" toggle from the environment, ensuring the rest of the code doesn't have to deal with raw secrets.
*   **`exchange.py` (The Executor)**: This is where the bridge meets the market. It initializes the `ccxt` connection and contains a placeholder function (`execute_order`) meant to translate a "Long" signal into a real exchange order.

Critical Reasoning & Robustness Gaps
*As your critical thinking partner, I’ve identified several high-risk areas in this AI-generated code that violate your new AI Standards:*

1.  **Synchronous Bottleneck**: The code currently uses synchronous calls (e.g., `create_market_buy_order`). If the exchange takes 2 seconds to respond, the entire server "freezes." During high volatility, this could cause you to miss subsequent webhooks or experience significant slippage. **Correction: Must use `ccxt.pro` or the `async` version of CCXT.**
2.  **Lack of Idempotency**: If TradingView sends the same webhook twice (a common occurrence due to network retries), this code will execute the trade twice. There is no logic to check if an order for that specific signal timestamp has already been processed.
3.  **No Position Awareness**: The `execute_order` logic is currently "blind." It doesn't check if you already have a position open before trying to buy more or exit. In real trading, you need to know your current state to avoid "doubling up" or failing to close a position.
4.  **Incomplete Error Handling**: If the exchange returns a `RateLimitExceeded` or `InsufficientFunds` error, the current code just logs a message and stops. There is no mechanism to retry the order or alert you immediately via another channel (like Telegram).
5.  **Race Conditions**: Without a task queue (like Redis/Celery mentioned in your `AI_STANDARDS.md`), multiple webhooks arriving at the same millisecond could lead to conflicting orders being sent to the exchange simultaneously.

**Verdict:** The current code is a helpful "sketch" for understanding the flow, but it is **not safe for real money** as it lacks the robustness required for automated execution.

