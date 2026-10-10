import os
import sqlite3
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

RAW_DIR = "/home/smhvz/Desktop/DATA-SCIENCE/projects/data-backtest/raw_data"

CANDIDATE_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT", 
    "SUIUSDT", "NEARUSDT", "AVAXUSDT", "1000PEPEUSDT", "WIFUSDT", "1000SHIBUSDT", 
    "ARBUSDT", "OPUSDT", "LINKUSDT", "TIAUSDT", "APTUSDT", "FETUSDT", "WLDUSDT", 
    "MINAUSDT", "MANTAUSDT", "ARPAUSDT", "RENDERUSDT", "INJUSDT", "UNIUSDT", 
    "AAVEUSDT", "STRKUSDT", "SEIUSDT", "TONUSDT", "ORDIUSDT", "1000BONKUSDT", 
    "1000FLOKIUSDT", "GALAUSDT", "SANDUSDT", "AXSUSDT", "RLCUSDT", "GTCUSDT", 
    "OGNUSDT", "MOVRUSDT", "CRVUSDT", "MKRUSDT", "LDOUSDT", "PENDLEUSDT", 
    "ONDOUSDT", "MANTRAUSDT", "JUPUSDT", "ENAUSDT", "NOTUSDT", "BOMEUSDT", 
    "DYDXUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", 
    "POLUSDT", "ATOMUSDT", "BEAMXUSDT"
]

START_DATE = "2026-04-01 00:00:00"
END_DATE = "2026-10-09 23:59:59"

# Test 1:2 R:R (SL: -2.0%, TP: +4.0%)
SL_PCT = 0.020
TP_PCT = 0.040
ENTRY_TRIGGER = 0.03
FEE_R = 0.04

def backtest_improved(sym):
    db_path = os.path.join(RAW_DIR, f"{sym}.db")
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cur = conn.cursor()
        cur.execute("""
            SELECT open_time, open, high, low, close, quote_volume
            FROM klines
            WHERE symbol = ? AND interval = '1m' AND open_time >= ? AND open_time <= ?
            ORDER BY open_time ASC
        """, (sym, START_DATE, END_DATE))
        rows = cur.fetchall()
        conn.close()

        if not rows: return []

        day_bars = defaultdict(list)
        for r in rows:
            day_bars[r[0][:10]].append(r)

        trades = []
        for dt, bars in day_bars.items():
            if len(bars) < 720: continue
            day_open = bars[0][1]
            if day_open <= 0: continue

            target_price = day_open * (1.0 + ENTRY_TRIGGER)
            entry_idx = -1
            entry_price = target_price

            for i, b in enumerate(bars):
                if b[2] >= target_price:
                    entry_idx = i
                    entry_price = target_price if b[1] <= target_price else b[1]
                    break

            # Filter: Giriş anındaki kümülatif hacim kontrolü (Hacimsiz ölü hareketleri ele)
            if entry_idx != -1 and entry_idx < len(bars) - 1:
                cum_vol = sum(b[5] for b in bars[:entry_idx + 1])
                # En az $1.5M hacim oluşmuş olmalı
                if cum_vol < 1_500_000:
                    continue

                tp_price = entry_price * (1.0 + TP_PCT)
                sl_price = entry_price * (1.0 - SL_PCT)

                outcome = None
                r_result = 0.0

                for b in bars[entry_idx + 1:]:
                    hit_tp = (b[2] >= tp_price)
                    hit_sl = (b[3] <= sl_price)

                    if hit_tp and hit_sl:
                        outcome = "LOSS"
                        r_result = -1.0
                        break
                    elif hit_sl:
                        outcome = "LOSS"
                        r_result = -1.0
                        break
                    elif hit_tp:
                        outcome = "WIN"
                        r_result = 2.0 # 1:2 R
                        break

                if outcome is None:
                    outcome = "EOD"
                    last_close = bars[-1][4]
                    gain_pct = (last_close - entry_price) / entry_price
                    r_result = gain_pct / SL_PCT

                net_r = r_result - FEE_R
                trades.append({
                    "symbol": sym,
                    "date": dt,
                    "outcome": outcome,
                    "net_r": net_r
                })

        return trades
    except Exception:
        return []

def main():
    valid = [s for s in CANDIDATE_SYMBOLS if os.path.exists(os.path.join(RAW_DIR, f"{s}.db"))]
    with ProcessPoolExecutor(max_workers=6) as ex:
        nested = list(ex.map(backtest_improved, valid))
    all_t = [t for sub in nested for t in sub]
    
    total = len(all_t)
    wins = [t for t in all_t if t["outcome"] == "WIN"]
    losses = [t for t in all_t if t["outcome"] == "LOSS"]
    net_r = sum(t["net_r"] for t in all_t)

    print(f"--- 1:2 R:R + HACİM FİLTRELİ MODEL SONUCU ---")
    print(f"Toplam İşlem: {total} adet")
    print(f"Win Sayısı: {len(wins)} (%{len(wins)/total*100:.2f})")
    print(f"Loss Sayısı: {len(losses)} (%{len(losses)/total*100:.2f})")
    print(f"Toplam Net R: {net_r:+,.2f} R")

if __name__ == "__main__":
    main()
