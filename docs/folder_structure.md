### The PineRoute-Core Directory Tree

```text
pineroute-core/
├── docs/                   # Documentation files
│   ├── AI_STANDARDS.md     # The master AI constraints file we just created
│   ├── usage.md            # Getting started guide
│   └── architecture.md     # Explains the Redis + FastAPI data flow
├── src/                    # The actual source files
│   ├── api/                # FastAPI routers and webhook endpoints
│   │   ├── __init__.py
│   │   ├── dependencies.py # API key validation and security checks
│   │   └── webhooks.py     # The /v1/webhooks/ route that TradingView hits
│   ├── core/               # App-wide settings
│   │   ├── __init__.py
│   │   ├── config.py       # Pydantic BaseSettings loading from .env
│   │   └── exceptions.py   # Custom error handling
│   ├── models/             # Data schemas
│   │   ├── __init__.py
│   │   └── schemas.py      # Pydantic models for incoming JSON payloads
│   ├── services/           # The heavy lifting logic
│   │   ├── __init__.py
│   │   └── exchange.py     # The CCXT async wrapper classes
│   ├── workers/            # Background task processing
│   │   ├── __init__.py
│   │   └── queue.py        # Redis/Celery worker that executes trades
│   └── main.py             # The FastAPI application entry point
├── test/                   # Automated tests
│   ├── integration/        # End-to-end tests
│   └── unit/               # Unit tests
├── .env.example            # Template showing required variables (NO REAL SECRETS)
├── .gitignore              # Ignores __pycache__, actual .env, venv, etc.
├── requirements.txt        # Python dependencies (fastapi, ccxt, redis, etc.)
├── LICENSE                 # Open source license text
└── README.md               # The landing page for your GitHub repo

```

---

* Your `test/unit/` folder will contain small scripts testing if your Pydantic schemas correctly reject badly formatted JSON.
* Your `test/integration/` folder will contain scripts that simulate sending a fake webhook and checking if the Redis queue actually picks it up.

