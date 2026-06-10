import pandas as pd
import numpy as np

CSV_FILENAME    = '../crypto_data/btc_2018_2026_M15.csv'
INITIAL_CAPITAL = 1000000.0


def calculate_koenigsegg_signals(df):
    """
    Computes all 5 Koenigsegg Jesko Absolut sub-indicators and returns the
    DataFrame with a 'TPI' column (1 = long, -1 = cash, 0 = neutral).
    """
    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    hl2 = (high + low) / 2

    # Local re-implementations of Pine Script built-ins to keep parity with
    # ta.wma / ta.hma / ta.rma / ta.atr / ta.dmi. Do not swap these out for
    # generic pandas equivalents — the alpha/span choices matter.
    def wma(series, length):
        weights = np.arange(1, length + 1)
        return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    def hma(series, length):
        half_len = int(length / 2)
        sqrt_len = int(np.sqrt(length))
        return wma(2 * wma(series, half_len) - wma(series, length), sqrt_len)

    def rma(series, length):
        # ewm(alpha=1/length) matches Pine's ta.rma; ta.ema uses span instead.
        return series.ewm(alpha=1/length, adjust=False).mean()

    def atr(high, low, close, length):
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return rma(tr, length)

    def dmi(high, low, close, length, smooth):
        up = high - high.shift(1)
        down = low.shift(1) - low
        plus_dm = np.where((up > down) & (up > 0), up, 0)
        minus_dm = np.where((down > up) & (down > 0), down, 0)
        tr = atr(high, low, close, length)
        # Avoid division by zero
        tr_safe = tr.replace(0, np.nan)
        plus_di = 100 * rma(pd.Series(plus_dm, index=df.index), length) / tr_safe
        minus_di = 100 * rma(pd.Series(minus_dm, index=df.index), length) / tr_safe
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1))
        adx = rma(dx, smooth)
        return plus_di, minus_di, adx

    # --- 1. Med: TSP (Temporal Slope Proxy) oscillator ---
    nSmooth, tspSmooth, tspDeltaSmooth = 42, 22, 25
    minStrength, momentumEMA_len, momentumThresh = 1.7, 4, 0.3

    emaSmooth = close.ewm(span=nSmooth, adjust=False).mean()
    emaSlope = emaSmooth.diff()
    tspEma = emaSlope.ewm(span=tspSmooth, adjust=False).mean()
    tspDelta = (tspEma - tspEma.shift(1).fillna(0)).ewm(span=tspDeltaSmooth, adjust=False).mean()
    volNorm = emaSlope.abs().ewm(span=nSmooth, adjust=False).mean()
    normSlope = emaSlope / volNorm.replace(0, np.nan)
    normSlopeEMA = normSlope.ewm(span=momentumEMA_len, adjust=False).mean()

    bullFilter = (tspEma > 0) & (tspDelta > 0) & (normSlope >= minStrength) & (normSlope > normSlopeEMA + momentumThresh)
    bearFilter = (tspEma < 0) & (tspDelta < 0) & (normSlope <= -minStrength) & (normSlope < normSlopeEMA - momentumThresh)
    df['Med'] = np.where(bullFilter & ~bearFilter, 1, np.where(bearFilter, -1, 0))

    # --- 2. QB: Gaussian-filtered FRAMA + ATR bands ---
    len_FG, sigma_FG = 31, 4.7
    w_g = np.exp(-0.5 * (((np.arange(len_FG) - (len_FG - 1) / 2) / sigma_FG) ** 2))
    w_g /= w_g.sum()
    filter_Gaussian = close.rolling(len_FG).apply(lambda x: np.dot(x, w_g), raw=True)
    frama = filter_Gaussian.ewm(span=23, adjust=False).mean()
    filter_ATR = atr(high, low, close, 15) * 3.1
    df['QB'] = np.where(close > (frama + filter_ATR), 1, np.where(close < (frama - atr(high, low, close, 15)), -1, 0))

    # --- 3. Rako: ADX-scaled SuperTrend ---
    baseline = high.ewm(span=3, adjust=False).mean()
    atr19 = atr(high, low, close, 19)
    plus_di, minus_di, adx7 = dmi(high, low, close, 7, 7)

    tRaw = (adx7 - 2) / (12.0 - 2.0)
    t = tRaw.clip(0.0, 1.0)
    scale = (1.0 + (1.35 - 1.0) * (t ** 1)).clip(1.0, 1.35)
    effMult = 2.5 * scale

    upperband = baseline + effMult * atr19
    lowerband = baseline - effMult * atr19
    df['Rako'] = np.where(close > upperband, 1, np.where(close < lowerband, -1, 0))

    # --- 4. CharonQuant: For-Loop THMA with DMI/ADX trend filter ---
    hma1 = hma(hl2, 31)
    hma2 = hma(hma1, 31)
    hma3 = hma(hma2, 31)
    med1 = 3 * hma1 - 3 * hma2 + hma3
    trendEma = hl2.ewm(span=20, adjust=False).mean()
    plus_di9, minus_di9, adx14 = dmi(high, low, close, 9, 14)

    counter = pd.Series(0.0, index=df.index)
    # Optimized for-loop approach using shifts
    for i in range(3, 31):
        counter += np.where(med1 > med1.shift(i), 1, -1)

    bullTrend = (plus_di9 > minus_di9) & (adx14 > 27)
    bearTrend = (minus_di9 > plus_di9) & (adx14 > 27)
    finalLong = (counter > 25) & (hl2 > trendEma) & bullTrend
    finalShort = (counter < -21) & (hl2 < trendEma) & bearTrend
    df['CharonQuant'] = np.where(finalLong & ~finalShort, 1, np.where(finalShort, -1, 0))

    # --- 5. Quantum: percentile + ATR momentum breakout ---
    mult_75, mult_25 = 2.1, 2.5
    percentile_75 = high.rolling(30).quantile(0.75)
    percentile_25 = high.rolling(30).quantile(0.25)
    atrq = atr(high, low, close, 45)

    df['Quantum'] = np.where(close > (percentile_75 + mult_75 * atrq), 1,
                    np.where(close < (percentile_25 - mult_25 * atrq), -1, 0))

    # Sum votes; TPI collapses the total: >1 → long, <0 → cash, else neutral.
    cols = ['Med', 'QB', 'Rako', 'CharonQuant', 'Quantum']
    df[cols] = df[cols].fillna(0)
    df['THRESHOLD'] = df[cols].sum(axis=1)
    df['TPI'] = np.where(df['THRESHOLD'] > 1, 1, np.where(df['THRESHOLD'] < 0, -1, 0))

    return df


if __name__ == "__main__":
    import sys
    csv_to_load = sys.argv[1] if len(sys.argv) > 1 else CSV_FILENAME

    print(f"Loading data from: {csv_to_load}...")
    df_15m = pd.read_csv(csv_to_load)
    df_15m['timestamp'] = pd.to_datetime(df_15m['timestamp'])

    print("Computing 15m signals...")
    df_15m = calculate_koenigsegg_signals(df_15m)

    print("Computing Daily signals (HTF Filter)...")
    # Resample to Daily timeframe
    df_daily = df_15m.set_index('timestamp').resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index()
    
    # Calculate signals on Daily data
    df_daily = calculate_koenigsegg_signals(df_daily)
    
    # Shift Daily TPI to avoid lookahead (barmerge.lookahead_off)
    # The signal from the *completed* previous day is used for all 15m bars of today.
    df_daily['TPI_Daily'] = df_daily['TPI'].shift(1)
    
    # Map Daily TPI back to 15m data
    # Create a 'date' column for merging
    df_15m['date'] = df_15m['timestamp'].dt.date
    df_daily['date'] = df_daily['timestamp'].dt.date
    
    df_15m = df_15m.merge(df_daily[['date', 'TPI_Daily']], on='date', how='left')
    
    print("Combining signals...")
    # finalLongCondition = (TPI_15m == 1) and (TPI_Daily == 1)
    # finalCashCondition = (TPI_15m == -1) or (TPI_Daily != 1)
    
    # Initialize FINAL_TPI with neutral (0)
    df_15m['FINAL_TPI'] = 0
    
    # We apply the logic statefully similar to how TPI is used in the Pine script
    # but for simplicity in the backtest loop, we'll just pre-calculate the final signal.
    # Actually, the Pine Script logic for final signal is:
    # if finalLongCondition -> strategy.entry("Long")
    # if finalCashCondition -> strategy.close("Long")
    
    # Let's define the conditions
    long_cond = (df_15m['TPI'] == 1) & (df_15m['TPI_Daily'] == 1)
    cash_cond = (df_15m['TPI'] == -1) | (df_15m['TPI_Daily'] != 1)
    
    # Fill FINAL_TPI: 1 for long entry, -1 for cash/exit, 0 otherwise
    df_15m['FINAL_TPI'] = np.where(long_cond, 1, np.where(cash_cond, -1, 0))

    capital = INITIAL_CAPITAL
    position = 0.0
    in_market = False
    trades = []
    equity_curve = [INITIAL_CAPITAL]
    trade_returns = []
    entry_price = 0.0

    print("Running backtest...")
    # Signal from bar i-1 drives the trade executed at bar i's close price.
    for i in range(1, len(df_15m)):
        current_tpi = df_15m['FINAL_TPI'].iloc[i-1]
        price = df_15m['close'].iloc[i]
        date = df_15m['timestamp'].iloc[i]

        if current_tpi == 1 and not in_market:
            position = capital / price
            entry_price = price
            capital = 0.0
            in_market = True
            trades.append({'Date': date, 'Type': 'Buy', 'Price': price})

        elif current_tpi == -1 and in_market:
            capital = position * price
            trade_return = (price - entry_price) / entry_price * 100
            trade_returns.append(trade_return)
            position = 0.0
            in_market = False
            trades.append({'Date': date, 'Type': 'Sell', 'Price': price})
        
        # Track equity
        current_equity = capital + (position * price if in_market else 0)
        equity_curve.append(current_equity)

    if in_market:
        final_price = df_15m['close'].iloc[-1]
        capital = position * final_price
        trade_return = (final_price - entry_price) / entry_price * 100
        trade_returns.append(trade_return)
        equity_curve.append(capital)

    # Calculate Metrics
    net_profit_pct = ((capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
    num_trades = len(trade_returns)
    profitable_trades = [r for r in trade_returns if r > 0]
    win_rate = (len(profitable_trades) / num_trades * 100) if num_trades > 0 else 0
    avg_trade_pct = np.mean(trade_returns) if num_trades > 0 else 0

    # Max Drawdown calculation
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max
    max_drawdown_pct = drawdown.min() * 100

    print(f"\n--- BACKTEST RESULTS (DC VERSION) ---")
    print(f"File:                {csv_to_load}")
    print(f"Initial Capital:     ${INITIAL_CAPITAL:,.2f}")
    print(f"Final Capital:       ${capital:,.2f}")
    print(f"Net Profit %:        {net_profit_pct:.2f}%")
    print(f"Max DrawDown %:      {abs(max_drawdown_pct):.2f}%")
    print(f"Profitable %:        {win_rate:.2f}%")
    print(f"Number of trades:    {num_trades}")
    print(f"Average % per trade: {avg_trade_pct:.2f}%")
