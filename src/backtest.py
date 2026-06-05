import pandas as pd
import numpy as np

# Configurazione Generale Backtest
# Nome del file di dati prezzo CSV
CSV_FILENAME    = '../crypto_data/btc_2018_2026_M15.csv'
# Capitale iniziale della simulazione in USDT
INITIAL_CAPITAL = 1000000.0


# Logica degli indicatori
def calculate_koenigsegg_signals(df):
    """
    Calcola tutti i 5 indicatori della strategia Koenigsegg Jesko Absolut
    e restituisce il DataFrame con la colonna 'TPI' (1 Long, -1 Cash, 0 Neutro).
    """
    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    hl2 = (high + low) / 2

    # Funzioni di utilità generiche
    def wma(series, length):
        weights = np.arange(1, length + 1)
        return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    
    def hma(series, length):
        half_len = int(length / 2)
        sqrt_len = int(np.sqrt(length))
        return wma(2 * wma(series, half_len) - wma(series, length), sqrt_len)
    
    def rma(series, length):
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
        plus_di = 100 * rma(pd.Series(plus_dm), length) / tr
        minus_di = 100 * rma(pd.Series(minus_dm), length) / tr
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1))
        adx = rma(dx, smooth)
        return plus_di, minus_di, adx

    # 1. TSP Oscillator
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

    # 2. G-FRAMA
    len_FG, sigma_FG = 31, 4.7
    w_g = np.exp(-0.5 * (((np.arange(len_FG) - (len_FG - 1) / 2) / sigma_FG) ** 2))
    w_g /= w_g.sum()
    filter_Gaussian = close.rolling(len_FG).apply(lambda x: np.dot(x, w_g), raw=True)
    frama = filter_Gaussian.ewm(span=23, adjust=False).mean() 
    filter_ATR = atr(high, low, close, 15) * 3.1
    df['QB'] = np.where(close > (frama + filter_ATR), 1, np.where(close < (frama - atr(high, low, close, 15)), -1, 0))

    # 3. ADX SuperTrend
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

    # 4. For Loop THMA
    hma1 = hma(hl2, 31)
    hma2 = hma(hma1, 31)
    hma3 = hma(hma2, 31)
    med1 = 3 * hma1 - 3 * hma2 + hma3
    trendEma = hl2.ewm(span=20, adjust=False).mean()
    plus_di9, minus_di9, adx14 = dmi(high, low, close, 9, 14)
    
    counter = pd.Series(0.0, index=df.index)
    for i in range(3, 31):
        counter += np.where(med1 > med1.shift(i), 1, -1)
    
    bullTrend = (plus_di9 > minus_di9) & (adx14 > 27)
    bearTrend = (minus_di9 > plus_di9) & (adx14 > 27)
    finalLong = (counter > 25) & (hl2 > trendEma) & bullTrend
    finalShort = (counter < -21) & (hl2 < trendEma) & bearTrend
    df['CharonQuant'] = np.where(finalLong & ~finalShort, 1, np.where(finalShort, -1, 0))

    # 5. Percentile Momentum
    mult_75, mult_25 = 2.1, 2.5
    percentile_75 = high.rolling(30).quantile(0.75)
    percentile_25 = high.rolling(30).quantile(0.25)
    atrq = atr(high, low, close, 45)
    
    df['Quantum'] = np.where(close > (percentile_75 + mult_75 * atrq), 1, 
                    np.where(close < (percentile_25 - mult_25 * atrq), -1, 0))

    # Voto Finale (Threshold)
    cols = ['Med', 'QB', 'Rako', 'CharonQuant', 'Quantum']
    df[cols] = df[cols].fillna(0)
    df['THRESHOLD'] = df[cols].sum(axis=1)
    df['TPI'] = np.where(df['THRESHOLD'] > 1, 1, np.where(df['THRESHOLD'] < 0, -1, 0))
    
    return df

# Esecuzione del Backtest
if __name__ == "__main__":
    print(f"Caricamento dati dal file: {CSV_FILENAME}...")
    df = pd.read_csv(CSV_FILENAME)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print("Calcolo degli indicatori (potrebbe richiedere qualche secondo)...")
    df = calculate_koenigsegg_signals(df)
    
    # Logica di portafoglio
    capital = INITIAL_CAPITAL
    position = 0.0
    in_market = False
    trades = []
    
    for i in range(1, len(df)):
        current_tpi = df['TPI'].iloc[i-1] 
        price = df['close'].iloc[i]
        date = df['timestamp'].iloc[i]
        
        # Buy
        if current_tpi == 1 and not in_market:
            position = capital / price
            capital = 0.0
            in_market = True
            trades.append({'Date': date, 'Type': 'Buy', 'Price': price})
            
        # Sell
        elif current_tpi == -1 and in_market:
            capital = position * price
            position = 0.0
            in_market = False
            trades.append({'Date': date, 'Type': 'Sell', 'Price': price})
            
    if in_market:
        capital = position * df['close'].iloc[-1]
        
    print(f"\n--- RISULTATI BACKTEST ---")
    print(f"File analizzato:   {CSV_FILENAME}")
    print(f"Capitale Iniziale: ${INITIAL_CAPITAL:,.2f}")
    print(f"Capitale Finale:   ${capital:,.2f}")
    print(f"Ritorno Netto:     {((capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100:.2f}%")
    print(f"Trade eseguiti:    {len(trades) // 2}")