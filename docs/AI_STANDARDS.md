# PineRoute (formerly UniStrat): Automated Trading Bridge

> **CRITICAL CONTEXT FOR AI AGENTS (Claude, Gemini, etc.):** 
> This document is the absolute ground truth for this codebase. Before generating any code, refactoring, or suggesting architectural changes, you must read and adhere to every constraint outlined below. Do not deviate from these standards unless explicitly instructed by the repository owner.

## 0. AI Interaction & Reasoning Principles

**The primary role of AI in this repository is to assist in reasoning, validate decisions, and improve system robustness—not to produce code autonomously.**

*   **Code Generation:** Do not produce code unless specifically requested. The goal is for the maintainer to remain highly aware of every line in the repo.
*   **Critical Thinking:** Act as a critical thinking partner. Challenge assumptions, question edge cases, and help improve understanding rather than just generating output.
*   **Trading Logic & Robustness:** Never assume trading logic is correct. Always consider failure scenarios: duplicate webhooks, delayed signals, partial fills, API errors, and rate limits. Idempotency and consistency in order execution are critical.
*   **Separation of Concerns:** Maintain the strict separation between strategy logic (PineScript) and the execution layer (Python). Avoid introducing hidden behaviors that could affect trading outcomes.
*   **Clarity over Cleverness:** Prefer clarity and explicitness. Explain non-trivial logic, highlight potential risks or unintended consequences, and suggest improvements in logging, monitoring, and observability.
*   **System Design:** Identify weak points and failure modes. Suggest ways to make the system more robust and predictable, considering real-world constraints like latency, slippage, and exchange differences.
*   **Product Thinking:** Focus on user trust, transparency, and simplicity. Favor designs that reduce user error and confusion; users need clear explanations for every action taken by the system.
*   **Security:** Treat API keys and sensitive data with maximum caution. Prefer minimal permissions, suggest safe storage practices, and proactively point out potential vulnerabilities.

**The ultimate goal is to build a system that users can trust with real money.**

## 1. Project Overview
A Python-based automated trading bridge that connects TradingView PineScript strategy webhooks to cryptocurrency exchanges using the CCXT library.
* **Source:** TradingView (PineScript strategies)
* **Signal Method:** Webhooks (JSON payload)
* **Execution:** Python script utilizing `ccxt`
* **Current Supported Strategies:**
    * `koenigsegg.pine`: Multi-indicator trend strategy.
    * `koenigsegg_DC.pine`: Daily Confirmation version of the Koenigsegg strategy.

---

## 2. Core Tech Stack & Dependencies

All backend engine development must strictly utilize the following stack. Do not introduce alternative libraries or external dependencies without approval.

| Component | Technology | Specific Usage / Constraints |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Must use PEP 8 compliance and modern Type Hinting. |
| **Framework** | FastAPI / Uvicorn | Used exclusively for the webhook ingestion endpoints. |
| **Exchange API** | CCXT (Pro / Async) | The sole library allowed for interfacing with crypto exchanges. |
| **Task Queue** | Redis + Celery / ARQ | Used to decouple incoming webhooks from order execution. |
| **Validation** | Pydantic | Used to validate incoming JSON payloads. |
| **Config** | Pydantic-Settings | Loading from `.env` via `python-dotenv`. |

---

## 3. Architectural Constraints & Code Styles

### Naming Conventions
* **Classes:** `PascalCase`
* **Functions/Variables:** `snake_case`
* **Constants:** `SCREAMING_SNAKE_CASE`

### Asynchronous Execution (Non-Negotiable)
Network latency is our primary bottleneck. Blocking the main thread will cause dropped webhooks.
* **Rule:** Every network call, exchange interaction, and database query **must** be written using `async` and `await`. 
* **Rule:** Never use synchronous execution patterns (`time.sleep()`, synchronous `requests`, etc.). 

### Testing
* Use `pytest` for unit testing.
* **Crucial:** Mock exchange responses for testing order execution logic without hitting real APIs.

---

## 4. CCXT Integration & Exchange Rules

Because this software handles real financial capital, the CCXT integration must be bulletproof.
* **Modularity:** Separate webhook handling, order execution, and exchange connectivity.
* **Error Handling:** Use robust try-except blocks, especially for network calls (CCXT). Implement retries where appropriate.
* **Instantiation:** Always initialize exchange classes using the asynchronous variant.

---

## 5. Webhook Ingestion & Security

To prevent race conditions and unauthorized trading, follow this data flow pipeline: