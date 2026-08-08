# PineRoute — Setup & Hosting Guide

Welcome, Trader. This guide takes you from a fresh copy of the code to a running
server that receives TradingView alerts — even if you have **never hosted an
application before**. Read the first section slowly; the rest is copy‑paste.

---

## 1. What this thing actually is (the 60‑second version)

TradingView can fire an "alert" when your strategy triggers. That alert sends a
little HTTP message (a **webhook**) to a web address you choose. PineRoute is the
program that *sits at that web address*, checks the message is really from you,
and turns it into a real order on a crypto exchange (via a library called
`ccxt`).

The important thing to understand is that **PineRoute is not one program — it is
two programs that run at the same time** and talk to each other through a third
program called **Redis**:

```
                        ┌─────────────────────────────┐
  TradingView  ──POST──▶│  1. Web server (uvicorn)     │   answers TradingView
                        │     receives + checks alert  │   instantly
                        └──────────────┬──────────────┘
                                       │ drops a "job" into
                                       ▼
                            ┌────────────────────┐
                            │   Redis (a queue)  │
                            └─────────┬──────────┘
                                      │ hands the job to
                                      ▼
                        ┌─────────────────────────────┐
                        │  2. Worker (arq)             │   does the slow part:
                        │     places the exchange order│   talking to the exchange
                        └─────────────────────────────┘
```

Why split it in two? Because talking to an exchange can be slow, and TradingView
gives up if you don't answer in a couple of seconds. So the web server answers
*immediately* ("got it 👍") and lets the worker do the slow trading part in the
background. **You must run all three: Redis, the web server, and the worker.** If
the worker isn't running, alerts are received but no trade is ever attempted.

> ### ⚠️ Read this before you get excited
> **PineRoute does not place real orders yet.** The actual exchange calls in
> `src/services/exchange.py` are intentionally commented out — the code *logs*
> "Executed BUY order..." and returns a fake success, but nothing reaches Binance
> or any exchange. This is on purpose (safety first). You will see the whole
> pipeline work end‑to‑end, but no money moves. See
> [Section 8](#8-going-live-when-youre-ready) for how to switch it on later.

---

## 2. What you need installed

| Tool | Why | Check it's there |
| :--- | :--- | :--- |
| **Python 3.10+** | Runs the code | `python --version` |
| **Redis** | The queue between the two programs | `redis-cli ping` → `PONG` |
| **git** | To download/update the code | `git --version` |

Getting Redis:
- **Linux (a server):** `sudo apt update && sudo apt install -y redis-server`
- **macOS:** `brew install redis && brew services start redis`
- **Windows (your laptop):** Redis doesn't run natively. Easiest is Docker:
  `docker run -d -p 6379:6379 redis` — or just skip local Redis and test on a
  Linux server (Section 7). WSL also works.

---

## 3. First‑time setup (do this once)

Run every command **from the project root** (the folder that contains `src/` and
`requirements.txt`). This matters — see the box after step 5.

```bash
# 1. Create an isolated Python environment
python -m venv .venv

# 2. Activate it
#    Linux / macOS:
source .venv/bin/activate
#    Windows PowerShell:
.venv\Scripts\Activate.ps1

# 3. Install the dependencies
pip install -r requirements.txt

# 4. Create your secret settings file from the template
cp .env.example .env        # Windows PowerShell: copy .env.example .env

# 5. Open .env in an editor and fill it in (see Section 4)
```

> **⚠️ Always run PineRoute from the project root**, and always with the `src.`
> prefix (e.g. `uvicorn src.main:app`, `arq src.workers.queue.WorkerSettings`).
> The code loads your `.env` from wherever you launch it, so launching from the
> project root is what lets it find your settings. If you `cd` into `src/` and
> run things from there, you'll get `ModuleNotFoundError` and a "missing
> WEBHOOK_PASSPHRASE" crash. Root, always.

---

## 4. Filling in your `.env`

Your `.env` file holds your secrets. It is **never** committed to git (it's in
`.gitignore`). Here's what each line means:

```ini
# A password YOU invent. TradingView must send this exact string in every
# alert, or PineRoute rejects it. Make it long and random. REQUIRED.
WEBHOOK_PASSPHRASE=make_this_a_long_random_string

# Which exchange to use (any ccxt exchange id: binance, kraken, bybit, ...).
EXCHANGE_ID=binance

# Your exchange API keys. You can leave these as-is while testing, because
# no real orders are placed yet (see the warning in Section 1).
API_KEY=your_api_key
API_SECRET=your_api_secret

# True  = use the exchange's fake "testnet" money (SAFE — keep this while learning)
# False = real money. Do NOT set this to False until you've read Section 8.
PAPER_TRADING=True
```

The only value you **must** set to run the server is `WEBHOOK_PASSPHRASE`. If
it's missing, PineRoute refuses to start (on purpose — an unauthenticated trading
webhook is dangerous).

---

## 5. Running it locally (three terminals)

Open **three** terminal windows in the project root. Activate the venv in each
(step 2 above), then:

**Terminal 1 — Redis** (skip if you installed it as a background service):
```bash
redis-server
```

**Terminal 2 — the web server:**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
`--reload` auto‑restarts when you edit code (handy while learning; drop it in
production). You can also just run `python -m src.main`, which starts the same
server.

**Terminal 3 — the worker:**
```bash
arq src.workers.queue.WorkerSettings
```

If all three are happy, terminal 2 prints "PineRoute Bridge is starting up..."
and terminal 3 prints "Worker startup complete."

---

## 6. Testing that it works

With all three running, open a **fourth** terminal and send a fake alert. Use the
same passphrase you put in `.env`:

```bash
curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
        "passphrase": "make_this_a_long_random_string",
        "strategy": "my_first_strategy",
        "action": "buy",
        "symbol": "BTC/USDT",
        "quantity": 0.001
      }'
```

What you should see:
- **curl** returns `{"status":"success","message":"Signal queued for execution"}`
- **Terminal 2** logs "Received valid signal..." and "Enqueued...".
- **Terminal 3** logs "Processing trading signal..." and "Executed BUY order...".

Quick checks:
- `curl http://localhost:8000/health` → `{"status":"healthy"}`
- Open `http://localhost:8000/docs` in a browser for an interactive test page.
- Send the same curl twice within 10 seconds → the second returns
  `"duplicate_ignored"`. That's the anti‑duplicate protection working.
- Wrong passphrase → `401 Invalid passphrase`.

> **The correct URL is `/api/webhook`** — not `/webhook`. Older notes in this
> repo were wrong. If you ever get a `404`, this is almost always why.

### The exact message TradingView must send

Paste this into the **"Message"** box of your TradingView alert (fill in your
real passphrase). TradingView lets you use its placeholders like `{{ticker}}`:

```json
{
  "passphrase": "make_this_a_long_random_string",
  "strategy": "koenigsegg",
  "action": "buy",
  "symbol": "BTC/USDT",
  "price": 65000,
  "quantity": 0.01
}
```

Field reference (defined in `src/models/schemas.py`):

| Field | Required? | Notes |
| :--- | :--- | :--- |
| `passphrase` | ✅ | Must equal your `WEBHOOK_PASSPHRASE`. |
| `strategy` | ✅ | Any name for your strategy. |
| `action` | ✅ | One of: `buy`, `long`, `sell`, `short`, `exit`, `cash`, `close`. |
| `symbol` | ✅ | Exchange pair, e.g. `BTC/USDT`. |
| `price` | optional | Informational. |
| `quantity` | optional* | *Required for `buy`/`sell`/`long`/`short` — that's how much to trade. |
| `side` | optional | Spare field for future use. |

---

## 7. Hosting it on a server (so TradingView can reach it 24/7)

Your laptop won't work for real use: TradingView needs a public address that's
always on. You need a small always‑on Linux computer in the cloud (a "VPS").

### Which server should a student pick?

**Best value if you have the [GitHub Student Developer Pack](https://education.github.com/pack)
(free for students):**

| Provider | Student offer | Good because |
| :--- | :--- | :--- |
| **DigitalOcean** | **$200 in credit** via the Student Pack | Dead‑simple dashboard, great tutorials. A $4–6/month "Droplet" runs this for ~3 years on the credit. **Recommended.** |
| **Microsoft Azure** | $100 credit + free services | More complex, but generous. |
| **DigitalOcean App Platform / Namecheap / .TECH** | Extra credits & a free domain for 1 year | The free domain is handy for HTTPS (below). |

**Genuinely free (no card / tiny free tiers):**

| Provider | Free tier | Watch out for |
| :--- | :--- | :--- |
| **Oracle Cloud "Always Free"** | A small VM free *forever* | Sign‑up can be fussy, but it's the most generous permanently‑free option. |
| **Google Cloud / AWS** | ~$300 credit / 12‑month free tier | Needs a credit card; easy to accidentally exceed free limits. |
| **Fly.io / Render** | Small free apps | Great, but you'd also need a managed Redis (both offer one). |

> **Recommendation for you:** claim the **GitHub Student Pack**, then create a
> basic **DigitalOcean Droplet** (Ubuntu, the cheapest size is plenty). The steps
> below assume exactly that. Everything transfers to any other Ubuntu server.

### Step‑by‑step: deploy on an Ubuntu server

Once you've created the Droplet, DigitalOcean shows you its **public IP address**
(e.g. `203.0.113.5`) and lets you open a web console, or you connect from your
laptop with `ssh root@203.0.113.5`.

```bash
# --- On the server ---

# 1. Install the essentials
sudo apt update
sudo apt install -y python3-venv python3-pip redis-server git
sudo systemctl enable --now redis-server     # start Redis + keep it on after reboot

# 2. Get the code
git clone <your-repo-url> pineroute-core
cd pineroute-core

# 3. Set up Python exactly like on your laptop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Create and edit your .env (Section 4). nano is a simple editor.
cp .env.example .env
nano .env        # fill in WEBHOOK_PASSPHRASE, save with Ctrl+O then Ctrl+X
```

### Keeping it running after you log out

If you just run the commands from Section 5, they die the moment you close your
SSH session. Two options:

**Quick & simple — `tmux`** (fine for testing):
```bash
sudo apt install -y tmux
tmux                       # opens a session that survives disconnects
# run the web server here, then press Ctrl+B then " to split, run the worker
# detach with Ctrl+B then D ; come back later with: tmux attach
```

**Proper & automatic — `systemd`** (survives reboots, restarts on crash). Create
two service files:

```bash
sudo nano /etc/systemd/system/pineroute-web.service
```
```ini
[Unit]
Description=PineRoute web server
After=network.target redis-server.service

[Service]
WorkingDirectory=/root/pineroute-core
ExecStart=/root/pineroute-core/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo nano /etc/systemd/system/pineroute-worker.service
```
```ini
[Unit]
Description=PineRoute worker
After=network.target redis-server.service

[Service]
WorkingDirectory=/root/pineroute-core
ExecStart=/root/pineroute-core/.venv/bin/arq src.workers.queue.WorkerSettings
Restart=always

[Install]
WantedBy=multi-user.target
```

Then turn them both on:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pineroute-web pineroute-worker
sudo systemctl status pineroute-web      # check it's "active (running)"
```
(Adjust `/root/pineroute-core` if you cloned elsewhere. `journalctl -u
pineroute-web -f` shows live logs.)

### Making it reachable + HTTPS

- **Open the firewall** for your port so TradingView can reach it. On
  DigitalOcean, either use a Cloud Firewall in the dashboard or:
  `sudo ufw allow 8000 && sudo ufw allow OpenSSH && sudo ufw enable`.
- **You can now point TradingView at `http://YOUR_SERVER_IP:8000/api/webhook`.**
  That already works.
- **Strongly recommended: add HTTPS.** Your passphrase travels in every alert;
  plain `http` sends it in the clear. The easy path: point a domain at your
  server (a free one from the Student Pack works), put **Caddy** in front — it
  gets a free HTTPS certificate automatically:
  ```bash
  sudo apt install -y caddy
  # Caddyfile: two lines
  #   yourdomain.com {
  #       reverse_proxy localhost:8000
  #   }
  ```
  Then TradingView points at `https://yourdomain.com/api/webhook`.

### Point TradingView at it

In your TradingView alert: set **Webhook URL** to your `/api/webhook` address,
and paste the JSON from Section 6 into the **Message** box. Trigger the alert and
watch your server logs (`journalctl -u pineroute-web -f` and
`... pineroute-worker -f`) light up.

---

## 8. Going live (when you're ready)

Only after you've watched the whole pipeline work in paper mode:

1. **Turn on real orders.** In `src/services/exchange.py`, uncomment the real
   ccxt calls and return their result, e.g.:
   ```python
   order = await self.exchange.create_market_buy_order(symbol, amount)
   return {"status": "success", "action": "buy", "symbol": symbol,
           "amount": amount, "order": order}
   ```
   Do the same for the sell branch, and implement position‑closing for `exit`.
2. **Test against the exchange testnet first** — keep `PAPER_TRADING=True`, which
   routes orders to the exchange's sandbox (fake money) when it supports one.
3. **Only then** create real API keys on your exchange, put them in `.env`, and
   set `PAPER_TRADING=False`. Give the keys the **minimum** permissions (trade
   only — never withdrawal), and restrict them to your server's IP if the
   exchange allows it.

Take it slowly. This is the part that touches real money.

---

## 9. Troubleshooting

| Symptom | Cause & fix |
| :--- | :--- |
| `ModuleNotFoundError: No module named 'core'` (or `src`) | You ran from the wrong folder. Run from the **project root** with the `src.` prefix: `uvicorn src.main:app`. |
| Crash mentioning `WEBHOOK_PASSPHRASE` / `ValidationError` on startup | No `.env`, or it's missing `WEBHOOK_PASSPHRASE`, or you launched from a folder where the `.env` isn't. Fix `.env` and launch from the root. |
| `404 Not Found` when sending an alert | You used `/webhook`. The correct path is `/api/webhook`. |
| `401 Invalid passphrase` | The `passphrase` in the JSON doesn't match `WEBHOOK_PASSPHRASE` in `.env`. |
| Alert accepted but nothing trades | The **worker** isn't running, or Redis is down. Start `arq src.workers.queue.WorkerSettings` and check `redis-cli ping`. |
| `Error 111 connecting to localhost:6379` / connection refused | Redis isn't running. Start it (`sudo systemctl start redis-server`). |
| Logs say "Executed BUY order" but the exchange shows nothing | Expected — orders are simulated until you do Section 8. |
| `422 Unprocessable Entity` | Your JSON is malformed or `action` isn't one of the allowed values (Section 6). |

---

## 10. Command cheat‑sheet

```bash
# From the project root, with the venv activated:

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload   # web server
arq src.workers.queue.WorkerSettings                       # worker
python -m src.main                                         # web server (alt.)

redis-cli ping                                             # is Redis alive?
curl http://localhost:8000/health                          # is the web server alive?
```

That's it, Trader. Start local (Sections 3–6), get comfortable, then move to a
server (Section 7). Keep `PAPER_TRADING=True` until you fully trust it.
