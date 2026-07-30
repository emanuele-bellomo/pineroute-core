# PineRoute

A Python-based automated trading bridge that connects TradingView PineScript strategy webhooks to cryptocurrency exchanges.

This project is currently **in development**!

## What this project does: Tradingview & PineScript

When you write a strategy in PineScript and it fires off an alert, Tradingview allows you to send an HTTP `POST` request to a URL you specify, with a JSON (or plain text) body you define in the alert's "Message" box, this is the **webhook**.

The problem is that Tradingview's alert:
- has no built-in authentication
- has no duplicate detection (could happen if the server is slow)
- sends raw strings and numbers and not orders ready for exchange APIs
- times out too fast.

So PineRoute has to:
- receive the JSON body and validate its shape/security token
- acknowledge Tradingview immediately (so it doesn't time out) while the trade executes in the background
- deduplicate repeated deliveries of the same alert
- translate the signal into a real exchange order with **ccxt**.

```mermaid
flowchart TD
    A[TradingView Alert fires] --> B[POST JSON to /api/webhook]
    B --> C[FastAPI: Pydantic validates schema]
    C --> D[Passphrase check]
    D --> E[Idempotency check in Redis]
    E --> F[Push job to Redis queue via ARQ]
    F --> G[Return 202 Accepted to TradingView immediately]
    F --> H[ARQ background worker picks up job]
    H --> I[ExchangeManager translates action to order]
    I --> J[ccxt.async_support sends order to exchange]
```
