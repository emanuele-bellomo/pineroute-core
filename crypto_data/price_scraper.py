import ccxt
import pandas as pd
import time
import sys

def download_data(symbol, timeframe, start_date, filename, exchange_id='binance'):
    if exchange_id == 'binance':
        exchange = ccxt.binance()
    elif exchange_id == 'bybit':
        exchange = ccxt.bybit()
    else:
        raise ValueError(f"Unsupported exchange: {exchange_id}")

    since = exchange.parse8601(start_date)

    all_candles = []
    batch_count = 0

    print(f"Downloading {symbol} from {start_date} to present from {exchange_id}...")

    while True:
        try:
            print(f"Batch {batch_count + 1} (from {exchange.iso8601(since)})...")

            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)

            if len(ohlcv) == 0:
                print("No more data. Download complete.")
                break

            all_candles.extend(ohlcv)

            # Advance past the last fetched candle to avoid a duplicate on the next request.
            # Use the timeframe to calculate the next since if ohlcv is empty, 
            # but here it's already handled by the break.
            since = ohlcv[-1][0] + 1
            batch_count += 1

            if since > exchange.milliseconds():
                print("Reached the present.")
                break

            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

    if not all_candles:
        print(f"No candles downloaded for {symbol}")
        return

    print(f"Download complete. Total candles: {len(all_candles)}")

    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.to_csv(filename, index=False)
    print(f"Saved as: {filename}")

if __name__ == "__main__":
    # Default behavior (backward compatible)
    symbol = 'BTC/USDT'
    timeframe = '15m'
    start_date = "2018-01-01 00:00:00"
    filename = 'btc_2018_2026_M15.csv'
    
    # If arguments are provided, use them
    if len(sys.argv) > 1:
        # Simple arg parsing for this specific task
        # Usage: python price_scraper.py <symbol> <timeframe> <start_date> <filename> [exchange_id]
        symbol = sys.argv[1]
        timeframe = sys.argv[2]
        start_date = sys.argv[3]
        filename = sys.argv[4]
        exchange_id = sys.argv[5] if len(sys.argv) > 5 else 'binance'
        download_data(symbol, timeframe, start_date, filename, exchange_id)
    else:
        download_data(symbol, timeframe, start_date, filename)
