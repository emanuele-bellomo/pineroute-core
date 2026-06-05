import ccxt
import pandas as pd
import time
from datetime import datetime
import src.backtest as backtest

# ==========================================
# --- CONFIGURAZIONE GENERALE BOT LIVE ---
# ==========================================
API_KEY            = 'LA_TUA_API_KEY_QUI'
API_SECRET         = 'IL_TUO_API_SECRET_QUI'

SYMBOL             = 'BTC/USDT'  # Token da scambiare (es: 'ETH/USDT', 'SOL/USDT')
TIMEFRAME          = '15m'       # Timeframe della strategia (deve combaciare con i backtest)
TRADE_SIZE_PERCENT = 0.99        # Usa il 99% del saldo disponibile per l'ordine (1% per coprire fee e slippage)
SLEEP_TIME_MINUTES = 15          # Ogni quanti minuti controllare il mercato (ideale: uguale al timeframe)

# ==========================================
# --- CONNESSIONE E FUNZIONI BOT ---
# ==========================================
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
        print(f"Errore nel fetch dei dati: {e}")
        return None

def execute_trade(action, current_price):
    try:
        base_currency = SYMBOL.split('/')[0]  # Es. 'BTC'
        quote_currency = SYMBOL.split('/')[1] # Es. 'USDT'
        
        balance = exchange.fetch_balance()
        
        if action == 'BUY':
            usdt_balance = balance[quote_currency]['free']
            if usdt_balance > 10: 
                amount_to_spend = usdt_balance * TRADE_SIZE_PERCENT
                qty = amount_to_spend / current_price
                print(f"Esecuzione BUY di {qty:.6f} {base_currency} a mercato.")
                order = exchange.create_market_buy_order(SYMBOL, qty)
                print("Ordine BUY completato:", order['id'])
            else:
                print(f"Saldo {quote_currency} insufficiente per comprare (>10).")
                
        elif action == 'SELL':
            token_balance = balance[base_currency]['free']
            if (token_balance * current_price) > 10:
                print(f"Esecuzione SELL di {token_balance:.6f} {base_currency} a mercato.")
                order = exchange.create_market_sell_order(SYMBOL, token_balance)
                print("Ordine SELL completato:", order['id'])
            else:
                print(f"Nessun saldo {base_currency} rilevante da vendere.")
                
    except Exception as e:
        print(f"ERRORE CRITICO NELL'ESECUZIONE DELL'ORDINE: {e}")

# ==========================================
# --- MOTORE PRINCIPALE ---
# ==========================================
def run_bot():
    print(f"[{datetime.now()}] Avvio Bot su {SYMBOL} ({TIMEFRAME})")
    in_position = False 
    
    while True:
        try:
            print(f"[{datetime.now()}] Download e analisi dati...")
            df = fetch_data()
            
            if df is not None:
                # Applica calcolo
                df = backtest.calculate_koenigsegg_signals(df)
                
                # Prende il segnale della candela appena chiusa
                last_closed_signal = df['TPI'].iloc[-2]
                current_price = df['close'].iloc[-1]
                
                print(f"Segnale attuale (1=Buy, -1=Sell): {last_closed_signal} | Prezzo: {current_price}")
                
                if last_closed_signal == 1 and not in_position:
                    execute_trade('BUY', current_price)
                    in_position = True
                
                elif last_closed_signal == -1 and in_position:
                    execute_trade('SELL', current_price)
                    in_position = False
            
            # Pausa calcolata dalla configurazione in alto
            time.sleep(60 * SLEEP_TIME_MINUTES) 
            
        except KeyboardInterrupt:
            print("Bot interrotto dall'utente.")
            break
        except Exception as e:
            print(f"Errore nel ciclo principale: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()