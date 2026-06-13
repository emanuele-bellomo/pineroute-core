### 1. Libraries in `requirements.txt`

*   **`ccxt`**: The backbone of the execution layer. It provides a unified way to connect to and trade on over 100 cryptocurrency exchanges.
*   **`fastapi` & `uvicorn`**: These form the web server. `fastapi` handles the incoming webhook requests from TradingView, and `uvicorn` is the high-performance server that runs the code.
*   **`pydantic` & `pydantic-settings`**: Used for data integrity. `pydantic` ensures the incoming JSON from TradingView follows a strict format, while `pydantic-settings` manages your sensitive configuration (like API keys) safely.
*   **`python-dotenv`**: A utility to load environment variables from a `.env` file into your application.
*   **`requests`**: A standard library for making HTTP requests. *Note: Since your standards require asynchronous execution, this library should likely be replaced by `httpx` or `aiohttp` to avoid blocking the system.*

### 2. Code in the `src` Folder

*   **`app.py` (The Gatekeeper)**: This is the entry point. It sets up an API endpoint (`/webhook`) that listens for signals. It performs a basic "passphrase" check to ensure only your TradingView signals can trigger trades.
*   **`models.py` (The Blueprint)**: Defines exactly what a "Signal" looks like. It expects fields like `strategy`, `action` (buy/sell), `symbol`, and `quantity`. If TradingView sends something different, the system will reject it immediately.
*   **`config.py` (The Vault)**: Centralizes all settings. It pulls your API keys and the "Paper Trading" toggle from the environment, ensuring the rest of the code doesn't have to deal with raw secrets.
*   **`exchange.py` (The Executor)**: This is where the bridge meets the market. It initializes the `ccxt` connection and contains a placeholder function (`execute_order`) meant to translate a "Long" signal into a real exchange order.

---

### 3. Critical Reasoning & Robustness Gaps
*As your critical thinking partner, I’ve identified several high-risk areas in this AI-generated code that violate your new AI Standards:*

1.  **Synchronous Bottleneck**: The code currently uses synchronous calls (e.g., `create_market_buy_order`). If the exchange takes 2 seconds to respond, the entire server "freezes." During high volatility, this could cause you to miss subsequent webhooks or experience significant slippage. **Correction: Must use `ccxt.pro` or the `async` version of CCXT.**
2.  **Lack of Idempotency**: If TradingView sends the same webhook twice (a common occurrence due to network retries), this code will execute the trade twice. There is no logic to check if an order for that specific signal timestamp has already been processed.
3.  **No Position Awareness**: The `execute_order` logic is currently "blind." It doesn't check if you already have a position open before trying to buy more or exit. In real trading, you need to know your current state to avoid "doubling up" or failing to close a position.
4.  **Incomplete Error Handling**: If the exchange returns a `RateLimitExceeded` or `InsufficientFunds` error, the current code just logs a message and stops. There is no mechanism to retry the order or alert you immediately via another channel (like Telegram).
5.  **Race Conditions**: Without a task queue (like Redis/Celery mentioned in your `AI_STANDARDS.md`), multiple webhooks arriving at the same millisecond could lead to conflicting orders being sent to the exchange simultaneously.

**Verdict:** The current code is a helpful "sketch" for understanding the flow, but it is **not safe for real money** as it lacks the robustness required for automated execution.