# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

UniStrat is a crypto trading strategy project. It ports a TradingView Pine Script strategy
("Koenigsegg Jesko Absolut") to Python so the same signal logic can be backtested against
historical data and run live against Binance. Most code and comments are in Italian.

## Commands

The project uses a local virtualenv (`.venv`, Python 3.14) with `ccxt`, `pandas`, and `numpy`.
There is no `requirements.txt`, test suite, or linter configured.

```powershell
# Activate the venv (PowerShell)
.venv\Scripts\Activate.ps1

# Download/refresh historical OHLCV data -> writes btc_2018_2026_M15.csv into crypto_data/
# Must be run from inside crypto_data/ (output path is relative)
cd crypto_data; python price_scraper.py

# Run the backtest -> must be run from inside src/ (CSV path is '../crypto_data/...')
cd src; python koenigsegg_backtest.py
cd src; python koenigsegg_DC_backtest.py

# Run the live trading bot -> must be run from the REPO ROOT as a module
#   (it imports `src.koenigsegg_backtest`)
python -m src.koenigsegg_live_trading
python -m src.koenigsegg_DC_live_trading
```

## Architecture

The signal logic lives in **one place** and is shared by both backtest and live trading:

- `src/koenigsegg_backtest.py` / `src/koenigsegg_DC_backtest.py` — `calculate_koenigsegg_signals(df)` is the single source of
  truth. It takes an OHLCV DataFrame (`timestamp, open, high, low, close, volume`) and computes
  five independent sub-indicators, each emitting a vote in {1, -1, 0}:
  1. `Med` — TSP (Temporal Slope Proxy) oscillator
  2. `QB` — Gaussian-filtered FRAMA + ATR bands
  3. `Rako` — ADX-scaled SuperTrend
  4. `CharonQuant` — For-Loop THMA with DMI/ADX trend filter
  5. `Quantum` — percentile + ATR momentum breakout

  Votes are summed into `THRESHOLD`, then collapsed to a final `TPI` signal:
  `THRESHOLD > 1 → 1 (long)`, `THRESHOLD < 0 → -1 (cash/short)`, else `0`.
  The `DC` version adds a Daily timeframe filter.

- `src/koenigsegg_live_trading.py` / `src/koenigsegg_DC_live_trading.py` — imports `calculate_koenigsegg_signals` from the backtest
  module and runs it on a polling loop against live Binance data via `ccxt`. **Acts on the
  last *closed* candle** (`df['TPI'].iloc[-2]`, not `-1`) to avoid trading on an unconfirmed bar.
  Tracks `in_position` in memory only — restarting the bot loses position state.
  The `DC` version fetches both 15m and Daily data.

- `crypto_data/price_scraper.py` — standalone data fetcher. Pages through `ccxt` Binance
  `fetch_ohlcv` 1000 candles at a time with rate-limiting, concatenates, and saves to CSV.

- `pinescript_original_scripts/koenigsegg.pine` — the original Pine Script v6 strategy. This is
  the reference spec. When changing indicator math in `calculate_koenigsegg_signals`, cross-check
  against this file — the Python is a hand-port and parameter values / formulas must stay in sync.

## Key conventions and gotchas

- **Working directory matters.** The three entry points each assume a different CWD (see Commands).
  The hardcoded relative paths (`../crypto_data/btc_2018_2026_M15.csv`, `btc_2018_2026_M15.csv`)
  are the reason.
- **Pine-to-Python parity.** Pine functions are reimplemented locally inside
  `calculate_koenigsegg_signals` (`wma`, `hma`, `rma`, `atr`, `dmi`). EMA uses
  `ewm(span=..., adjust=False)` and RMA uses `ewm(alpha=1/length, adjust=False)` to match Pine's
  `ta.ema` / `ta.rma`. Preserve these when editing.
- **Live bot secrets** are placeholder strings (`API_KEY`/`API_SECRET`) at the top of
  `koenigsegg_live_trading.py` — they must be filled in to trade and should never be committed.
- The `btc_2018_2026_M15.csv` dataset (~18 MB) is committed to the repo and is the default
  backtest input.
- `crypto_data/to_do.txt` lists additional symbols/timeframes intended for future strategies
  (SOL, AVAX, MNT, BNB on 4H).
