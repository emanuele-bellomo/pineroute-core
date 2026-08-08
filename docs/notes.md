# Architecture & Codebase Notes

## Directory & File Structure
I structured the project this way to keep the execution layer decoupled from the API layer, following standard FastAPI best practices.

*   **`src/main.py`**: The entry point. I put the FastAPI app instantiation, logging setup, and Redis pool connection here so that the app starts up fully configured before accepting any requests.
*   **`src/api/`**: Contains everything related to the web endpoints. I named it `api` because it acts as the outer shell receiving HTTP traffic.
    *   **`webhooks.py`**: I created this to handle the `/webhook` route specifically. It validates the request and immediately pushes the data to the background queue so TradingView doesn't time out waiting for the exchange.
    *   **`dependencies.py`**: I put my FastAPI dependency functions here (like `verify_passphrase`). It makes the router clean and allows me to easily reuse security checks across multiple endpoints in the future.
*   **`src/core/`**: The brain of the application's configuration and base rules.
    *   **`config.py`**: Handles environment variables. I used this centralized file so the rest of my code just imports `settings` without worrying about reading `.env` files or parsing types directly.
    *   **`exceptions.py`**: I defined custom error classes here (like `OrderExecutionError`) so I can gracefully handle and distinguish between different types of failures (e.g., a network error vs a bad signal).
*   **`src/models/`**: Defines the shape of the data flowing through the app.
    *   **`schemas.py`**: Contains the Pydantic models (like `WebhookPayload`). I named it schemas because it defines the exact JSON schema TradingView is allowed to send. If they send bad data, Pydantic rejects it automatically here.
*   **`src/services/`**: The business logic that actually does the heavy lifting.
    *   **`exchange.py`**: I named this `exchange` because it manages the connection to Binance/Kraken. I wrapped the `ccxt` library in an `ExchangeManager` class here to encapsulate all the complex exchange interactions (like paper trading modes and async execution).
*   **`src/workers/`**: The background task processing layer.
    *   **`queue.py`**: I put the ARQ worker settings here. This file is responsible for popping the webhook data off the Redis queue and triggering the `ExchangeManager`.

## Dependencies Used

Here is why I chose the specific libraries in my environment:

*   **`fastapi` & `uvicorn`**: I used these to build the web server because they are incredibly fast and natively support asynchronous code, which is critical since network lag is my main bottleneck.
*   **`pydantic` & `pydantic-settings`**: I used Pydantic to strictly validate the incoming JSON from TradingView, and Pydantic-Settings to securely load and type-check my `.env` API keys.
*   **`ccxt` (`ccxt.async_support`)**: I added this to connect to the exchanges. I explicitly used the async version so that placing an order doesn't block the rest of the application.
*   **`arq` & `redis`**: I chose ARQ over Celery because it's built specifically for `asyncio` and Redis. I used this to create a task queue, ensuring that if multiple webhooks arrive at once, they are queued up and processed safely without race conditions.
*   **`orjson`**: I swapped out the standard `json` library for this one in my Pydantic models because it is written in Rust and parses incoming webhooks significantly faster.
*   **`loguru`**: I replaced the standard Python `logging` module with Loguru because it handles asynchronous logging beautifully and gives me much clearer, colorized terminal output out of the box.
*   **`typing` (Built-in)**: I used `Dict`, `Any`, and `Optional` everywhere to add strict type hints, which helps me catch bugs in my IDE before I even run the code.
*   **`sys` (Built-in)**: I used this in `main.py` simply to tell Loguru to output my logs directly to the standard console output (`sys.stdout`).

---

## Roadmap

- [x] **Phase 1: Research & Setup**
    - [x] Initialize Project Structure
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


## Useful GitHub repos ("State of the art" analysis)

- **vlameiras/tradingview-webhook-integration**: * Why it's useful: This project is built using FastAPI. It bridges TradingView to Binance Futures. You can look at their app.py or router files to see exactly how they set up the FastAPI endpoints to receive JSON webhooks and validate them.

- **51bitquant/binance-tradingview-webhook-bot**: Why it's useful: A very popular bare-bones Python bot for Binance. While it uses Flask instead of FastAPI, it is a great reference for how to structure the .env loading, handle TradingView alert messages, and format the immediate market order execution logic.

- **freqtrade/freqtrade**: * Why it's useful: This is arguably the most famous open-source crypto trading bot in the world. It is written in Python and uses CCXT extensively. The architecture is massive, but it's worth digging into their codebase to see how they wrap CCXT API calls in try-except blocks, how they handle rate limits (RateLimitExceeded exceptions), and how they calculate position sizing safely.

- **marketcalls/openalgo**: Why it's useful: This is a comprehensive open-source algo trading platform that includes built-in webhook triggers for TradingView. It has order approval workflows, separate database isolation, and Telegram notifications. It's a great place to see how a "Dashboard/SaaS" layout is structured alongside a trading engine.

- **ccxt/ccxt (Examples Folder)**: Why it's useful: The official CCXT repository has a dedicated folder just for Python examples. Before you ask an AI or write your own code to place a "Limit Buy" or a "Stop Loss" order, look here. They have hundreds of short, highly optimized scripts showing exactly how to use ccxt.async_support properly.


## Logging Module

Logging is the process of recording events and data during a program's execution to provide an **audit trail** for debugging and monitoring.

The built-in Python logging module allows to categorize messages by severity: **DEBUG, INFO, WARNING, ERROR, CRITICAL**; format them by adding timestamps or line numbers, and route them to various destinations like consoles, files or remote servers.

In this project specifically, they have to provide a record of webhooks from TV, API calls to exchanges, and error details.

The built-in Python logging module is fast enough for most applications, but it's synchronous and can block the execution thread while writing to disk. Though the main bottleneck in this project is network latency.

I'm now actually trying to use the loguru library to see if it's worth changing it up.
