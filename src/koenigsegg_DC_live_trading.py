import ccxt
import pandas as pd
import time
from datetime import datetime
import src.koenigsegg_DC_backtest as dc_backtest

# --- CONFIGURATION ---
API_KEY            = 'LA_TUA_API_KEY_QUI'
API_SECRET         = 'IL_TUO_API_SECRET_QUI'

SYMBOL             = 'BTC/USDT'
TIMEFRAME_15M      = '15m'
TIMEFRAME_DAILY    = '1d'
TRADE_SIZE_PERCENT = 0.99        # 1% held back to cover fees and slippage.
SLEEP_TIME_MINUTES = 15

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})


def fetch_data(timeframe, limit=500):
    """
    Fetches OHLCV data from the exchange for a given timeframe.
    """
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Data fetch error ({timeframe}): {e}")
        return None


def execute_trade(action, current_price):
    """
    Executes a market BUY or SELL order based on the specified action.
    """
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
    """
    Main loop for the Koenigsegg DC Live Trading bot.
    """
    print(f"[{datetime.now()}] Starting bot on {SYMBOL} with Daily Confirmation (DC)")
    # in_position is tracked in memory only — restarting the bot loses position state.
    in_position = False

    while True:
        try:
            print(f"[{datetime.now()}] Fetching and analyzing 15m and Daily data...")
            
            # Fetch at least 500 bars for 15m and 100 for Daily to satisfy indicators history
            df_15m = fetch_data(TIMEFRAME_15M, limit=500)
            df_daily = fetch_data(TIMEFRAME_DAILY, limit=100)

            if df_15m is not None and df_daily is not None:
                # Calculate signals for both timeframes
                df_15m = dc_backtest.calculate_koenigsegg_signals(df_15m)
                df_daily = dc_backtest.calculate_koenigsegg_signals(df_daily)

                # Use iloc[-2] (last closed candle) for both to avoid lookahead/repainting
                signal_15m = df_15m['TPI'].iloc[-2]
                signal_daily = df_daily['TPI'].iloc[-2]
                
                # Current price for execution (last tick price)
                current_price = df_15m['close'].iloc[-1]

                print(f"Signals -> 15m: {signal_15m} | Daily: {signal_daily} | Price: {current_price}")

                # Daily Confirmation Logic:
                # longCondition = (signal_15m == 1) and (signal_daily == 1)
                # cashCondition = (signal_15m == -1) or (signal_daily != 1)
                
                long_condition = (signal_15m == 1) and (signal_daily == 1)
                cash_condition = (signal_15m == -1) or (signal_daily != 1)

                if long_condition and not in_position:
                    execute_trade('BUY', current_price)
                    in_position = True

                elif cash_condition and in_position:
                    execute_trade('SELL', current_price)
                    in_position = False
                
                if in_position:
                    print(f"Status: IN POSITION")
                else:
                    print(f"Status: IN CASH")

            time.sleep(60 * SLEEP_TIME_MINUTES)

        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run_bot()
