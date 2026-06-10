import ccxt
import pandas as pd
import time
from datetime import datetime
import src.koenigsegg_backtest as backtest

API_KEY            = 'LA_TUA_API_KEY_QUI'
API_SECRET         = 'IL_TUO_API_SECRET_QUI'

SYMBOL             = 'BTC/USDT'
TIMEFRAME          = '15m'       # Must match the backtest timeframe.
TRADE_SIZE_PERCENT = 0.99        # 1% held back to cover fees and slippage.
SLEEP_TIME_MINUTES = 15

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})


def fetch_data():
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=500)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Data fetch error: {e}")
        return None


def execute_trade(action, current_price):
    try:
        base_currency = SYMBOL.split('/')[0]
        quote_currency = SYMBOL.split('/')[1]

        balance = exchange.fetch_balance()

        if action == 'BUY':
            usdt_balance = balance[quote_currency]['free']
            if usdt_balance > 10:
                amount_to_spend = usdt_balance * TRADE_SIZE_PERCENT
                qty = amount_to_spend / current_price
                print(f"Placing BUY: {qty:.6f} {base_currency} at market.")
                order = exchange.create_market_buy_order(SYMBOL, qty)
                print(f"BUY order filled: {order['id']}")
            else:
                print(f"Insufficient {quote_currency} balance to buy (need >10).")

        elif action == 'SELL':
            token_balance = balance[base_currency]['free']
            if (token_balance * current_price) > 10:
                print(f"Placing SELL: {token_balance:.6f} {base_currency} at market.")
                order = exchange.create_market_sell_order(SYMBOL, token_balance)
                print(f"SELL order filled: {order['id']}")
            else:
                print(f"No significant {base_currency} balance to sell.")

    except Exception as e:
        print(f"CRITICAL ORDER ERROR: {e}")


def run_bot():
    print(f"[{datetime.now()}] Starting bot on {SYMBOL} ({TIMEFRAME})")
    # in_position is tracked in memory only — restarting the bot loses position state.
    in_position = False

    while True:
        try:
            print(f"[{datetime.now()}] Fetching and analyzing data...")
            df = fetch_data()

            if df is not None:
                df = backtest.calculate_koenigsegg_signals(df)

                # Use iloc[-2] (last closed candle) to avoid acting on an unconfirmed bar.
                last_closed_signal = df['TPI'].iloc[-2]
                current_price = df['close'].iloc[-1]

                print(f"Signal (1=Buy, -1=Sell): {last_closed_signal} | Price: {current_price}")

                if last_closed_signal == 1 and not in_position:
                    execute_trade('BUY', current_price)
                    in_position = True

                elif last_closed_signal == -1 and in_position:
                    execute_trade('SELL', current_price)
                    in_position = False

            time.sleep(60 * SLEEP_TIME_MINUTES)

        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run_bot()
