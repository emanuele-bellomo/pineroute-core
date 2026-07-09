
Bugs fixed

  1. Redis shutdown crash (src/main.py) — shutdown called .close() then await .wait_closed(), which is the old aioredis API. The
  project now runs on redis-py's redis.asyncio.Redis (via arq), which has no wait_closed() — I verified this against the actual
  installed package (redis 5.3.1) and it would have thrown AttributeError on every graceful shutdown. Fixed to await ...aclose().
  2. Timing-unsafe passphrase check (src/api/dependencies.py) — used != to compare the webhook passphrase, which leaks timing
  information about how many leading characters an attacker guessed correctly. Switched to secrets.compare_digest, per
  AI_STANDARDS' explicit call to treat secrets "with maximum caution."
  3. Errors returned as HTTP 202 (src/api/webhooks.py) — the status_code=202 on the route decorator applies regardless of what the
  function returns, so a Redis outage or enqueue failure was reported back to TradingView as "Accepted" with an "error" string
  buried in the body. Now raises proper HTTPExceptions (503/500) so failures are visible to monitoring.
  4. Latent crash on missing Redis pool (same file) — request.app.state.redis raises AttributeError when unset (Starlette's State
  doesn't return None), so the existing if not redis_pool: safety check could never actually run. Fixed with getattr(..., None).
  5. Dead/broken orjson config (src/models/schemas.py) — the class Config: json_loads = orjson.loads / json_dumps = ... block is
  Pydantic v1 syntax; the rest of the codebase is already on v2 (model_dump, SettingsConfigDict). It was silently a no-op and
  threw a UserWarning on every model load — confirmed via a live test. Removed the dead code. Note: orjson is now unused entirely
  in src/ — it's still in requirements.txt. Say the word if you want it either wired up properly (e.g., ORJSONResponse in FastAPI)
  or dropped from dependencies.

  Robustness gap closed (per AI_STANDARDS §0: idempotency is "critical")

  6. No duplicate-webhook protection — src/workers/queue.py had comments acknowledging this was unhandled. I added a Redis-backed
  idempotency guard in webhooks.py: a SHA-256 fingerprint of the tradeable fields (strategy, action, symbol, quantity, price,
  side) is SET NX EX 10 before enqueueing, so an exact repeat within 10 seconds is dropped instead of double-executing. This is a
  content-hash heuristic, not a true unique-ID check — for a stronger guarantee, consider adding {{timenow}} to your TradingView
  alert JSON so signals can be deduped by real timestamp instead.
  7. Unvalidated action field (schemas.py) — any string was accepted and only checked deep in the worker, so a typo'd action would
  get a 202 success from the API and then fail silently in a background log line. Added a field_validator restricting action to
  the values execute_order actually understands, returning a clean 422 immediately.

  I verified all of this by actually running the code — installed real dependencies in a scratch venv, confirmed wait_closed()
  doesn't exist on the installed redis package, and ran the fixed webhook handler end-to-end (dup-signal rejection, missing-Redis
  503, passphrase check, schema validation) rather than just reading it.

  What I deliberately did not touch

  ExchangeManager.execute_order in src/services/exchange.py still has the real create_market_buy_order/create_market_sell_order
  calls commented out, and "exit" doesn't actually fetch/close positions. This isn't a bug I introduced or silently fixed — it's a
  documented placeholder (your own notes.md and docs/usage.md call it out as unfinished, Phase 3 in the roadmap). Wiring it up
  involves decisions I shouldn't make for you on a live-money system: is quantity base-currency or notional? Should buy/sell check
  for an existing opposing position first? Should orders carry a clientOrderId for exchange-side idempotency? Happy to build this
  out once you tell me how you want position sizing and position-awareness to work.

✻ Worked for 6m 59s

※ recap: Reviewing and hardening the Gemini-generated PineRoute trading bridge in src/, I've fixed several bugs (redis shutdown
  crash, timing-unsafe passphrase check, error handling, missing idempotency). Next: waiting on your call on how to wire up real
  order execution in exchange.py. (disable recaps in /config)
