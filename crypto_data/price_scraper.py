import ccxt
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
symbol = 'BTC/USDT'
timeframe = '15m'
# Data di inizio: Anno-Mese-Giorno Ore:Minuti:Secondi
start_date = "2018-01-01 00:00:00"
filename = 'btc_2018_2026_M15.csv'

exchange = ccxt.binance()

# Convertiamo la data di inizio in "timestamp milliseconds" (la lingua di Binance)
# parse8601 è una funzione magica di ccxt che trasforma la stringa in numero
since = exchange.parse8601(start_date)

all_candles = []  # Qui accumuleremo tutti i pezzi
batch_count = 0   # Solo per contare quante richieste facciamo

print(f"--- Inizio scaricamento {symbol} dal {start_date} ad oggi ---")

while True:
    try:
        # 1. Scarichiamo 1000 candele a partire da 'since'
        print(f"Scaricando batch {batch_count + 1}... (Partenza: {exchange.iso8601(since)})")
        
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        
        # 2. SE LA LISTA È VUOTA, abbiamo finito (siamo arrivati a oggi)
        if len(ohlcv) == 0:
            print("Nessun altro dato trovato. Fine scaricamento.")
            break
        
        # 3. Aggiungiamo i dati trovati alla lista gigante
        all_candles.extend(ohlcv)
        
        # 4. AGGIORNIAMO IL PUNTO DI PARTENZA
        # Prendiamo il timestamp dell'ultima candela scaricata + 1 minuto (60000 ms)
        # Così la prossima richiesta parte esattamente dal minuto successivo
        last_candle_timestamp = ohlcv[-1][0]
        since = last_candle_timestamp + 60000 
        
        batch_count += 1
        
        # Check di sicurezza: se abbiamo superato "adesso", fermiamoci
        now = exchange.milliseconds()
        if since > now:
            print("Raggiunto il presente.")
            break
            
        # 5. PAUSA ANTIBAN (Rate Limiting)
        # Binance è generosa, ma un piccolo riposino evita errori 429 (Too Many Requests)
        time.sleep(0.5) # Mezzo secondo di pausa
        
    except Exception as e:
        print(f"Errore: {e}")
        print("Provo a ripartire tra 5 secondi...")
        time.sleep(5)

# --- SALVATAGGIO ---
print(f"Scaricamento completato! Totale candele: {len(all_candles)}")
print("Elaborazione e salvataggio in corso...")

df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Salviamo
df.to_csv(filename, index=False)
print(f"Fatto! File salvato come: {filename}")