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

SL_PCT = 0.022  # %2.2 Stop Loss
TP_PCT = 0.066  # %6.6 Take Profit
ENTRY_TRIGGER = 0.03 # %3.0 Günlük Açılıştan İtibaren Yükseliş
FEE_R = 0.04 # Komisyon ve Kayma (R cinsinden)

# 1. Preload BTC minute candles into memory for fast lookup
def load_btc_map():
    btc_path = os.path.join(RAW_DIR, "BTCUSDT.db")
    conn = sqlite3.connect(btc_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT open_time, open, close
        FROM klines
        WHERE symbol = 'BTCUSDT' AND interval = '1m' AND open_time >= ? AND open_time <= ?
        ORDER BY open_time ASC
    """, (START_DATE, END_DATE))
    rows = cur.fetchall()
    conn.close()

    btc_by_time = {}
    btc_day_open = {}

    for t, op, cl in rows:
        dt = t[:10]
        if dt not in btc_day_open:
            btc_day_open[dt] = op
        btc_by_time[t] = cl

    return btc_by_time, btc_day_open

# Global BTC lookup maps
BTC_BY_TIME, BTC_DAY_OPEN = load_btc_map()

def backtest_filtered(sym):
    # Exclude BTC itself from altcoin test
    if sym == "BTCUSDT":
        return []

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

            if entry_idx != -1 and entry_idx < len(bars) - 1:
                entry_time = bars[entry_idx][0]

                # ========================================================
                # KANTİTATİF FİLTRELER
                # ========================================================
                
                # FİLTRE 1: Zaman Penceresi (Günün ilk 4 saati: 240 dakika)
                # Geç saatlerde gelen tükenme kırılımlarını ele
                if entry_idx > 240:
                    continue

                # FİLTRE 2: Erken Kümülatif Hacim Filtresi
                # Giriş anına kadar en az 2,000,000$ hacim dönmüş olmalı
                cum_vol = sum(b[5] for b in bars[:entry_idx + 1])
                if cum_vol < 2_000_000:
                    continue

                # FİLTRE 3: Bitcoin Trend / Piyasa Rejim Filtresi
                # Giriş anında BTC günlük açılış fiyatının üzerinde olmalı
                btc_d_open = BTC_DAY_OPEN.get(dt, 0)
                btc_curr = BTC_BY_TIME.get(entry_time, 0)
                if btc_d_open > 0 and btc_curr < btc_d_open:
                    continue # BTC kırmızı ise altcoin kırılımına girme!

                # ========================================================
                # İŞLEM SİMÜLASYONU (TP: +%6.6 | SL: -%2.2)
                # ========================================================
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
                        r_result = 3.0
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
                    "entry_time": entry_time,
                    "outcome": outcome,
                    "gross_r": r_result,
                    "net_r": net_r
                })

        return trades
    except Exception:
        return []

def main():
    valid = [s for s in CANDIDATE_SYMBOLS if os.path.exists(os.path.join(RAW_DIR, f"{s}.db")) and s != "BTCUSDT"]
    print(f"Test Edilen Likit Altcoin Sayısı: {len(valid)}")
    print(f"Uygulanan Filtreler:")
    print("   1. BTC Trend Filtresi: Giriş anında BTC > Günlük Açılış")
    print("   2. Zaman Filtresi    : Giriş ilk 4 saat içinde (00:00 - 04:00 UTC)")
    print("   3. Hacim Filtresi    : Kırılım anında kümülatif hacim >= $2,000,000")
    print("   4. R:R Oranı         : 1:3 (SL: -%2.2 | TP: +%6.6)\n")

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=6) as ex:
        nested = list(ex.map(backtest_filtered, valid))

    all_t = [t for sub in nested for t in sub]
    elapsed = time.time() - t0
    print(f"✅ Filtreli Backtest {elapsed:.2f} saniyede tamamlandı!\n")

    total = len(all_t)
    wins = [t for t in all_t if t["outcome"] == "WIN"]
    losses = [t for t in all_t if t["outcome"] == "LOSS"]
    eods = [t for t in all_t if t["outcome"] == "EOD"]
    eod_pos = [t for t in eods if t["gross_r"] > 0]
    total_net_r = sum(t["net_r"] for t in all_t)

    win_rate = len(wins) / total * 100 if total > 0 else 0
    pos_rate = (len(wins) + len(eod_pos)) / total * 100 if total > 0 else 0

    print("=" * 75)
    print("🏆 FİLTRELİ STRATEJİ BACKTEST SONUÇLARI (6 AY / NİSAN - EKİM 2026)")
    print("=" * 75)
    print(f"Açılan Toplam İşlem Sayısı     : {total:,} adet (Günde ortalama {total/192:.1f} işlem)")
    print(f"Hedefe Ulaşan Tam Win (+3.0R)  : {len(wins):,} adet (%{win_rate:.2f})")
    print(f"Stop Olan Tam Loss (-1.0R)    : {len(losses):,} adet (%{len(losses)/total*100:.2f})")
    print(f"Gün Sonu Kapanan (EOD)        : {len(eods):,} adet (%{len(eods)/total*100:.2f})")
    print(f"   • Gün Sonu Kârda Kapanan    : {len(eod_pos):,} adet")
    print("-" * 75)
    print(f"Katı Win Rate (Sadece +3R TP)  : %{win_rate:.2f}")
    print(f"Kârda Kapanma Oranı (TP + EOD+): %{pos_rate:.2f}")
    print(f"TOPLAM NET KAZANÇ (R)          : {total_net_r:+,.2f} R")
    print(f"Aylık Ortalama Net Getiri (R)  : {total_net_r / 6.3:+.2f} R / Ay")
    print(f"Günlük Ortalama Net Getiri (R) : {total_net_r / 192:+.2f} R / Gün")

    # Coin rankings
    sym_scores = defaultdict(lambda: {"trades": 0, "wins": 0, "net_r": 0.0})
    for t in all_t:
        s = t["symbol"]
        sym_scores[s]["trades"] += 1
        if t["outcome"] == "WIN": sym_scores[s]["wins"] += 1
        sym_scores[s]["net_r"] += t["net_r"]

    top_syms = sorted(sym_scores.items(), key=lambda x: x[1]["net_r"], reverse=True)[:8]
    print("\n🌟 FİLTRELİ MODELDE EN ÇOK KAZANDIRAN İLK 8 KOİN:")
    for s, d in top_syms:
        w_pct = d["wins"] / d["trades"] * 100 if d["trades"] > 0 else 0
        print(f"   • {s:<14}: {d['trades']:>3} İşlem | Win: %{w_pct:>4.1f} | Net: {d['net_r']:>+7.2f} R")

if __name__ == "__main__":
    main()
