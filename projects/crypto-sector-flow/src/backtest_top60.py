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

SL_PCT = 0.022  # %2.2 Stop
TP_PCT = 0.066  # %6.6 Take Profit
ENTRY_TRIGGER = 0.03 # %3.0 Günlük Açılıştan İtibaren Yükseliş
FEE_PER_TRADE_R = 0.04 # Komisyon ve Kayma (R cinsinden)

def backtest_one(sym):
    db_path = os.path.join(RAW_DIR, f"{sym}.db")
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cur = conn.cursor()
        cur.execute("""
            SELECT open_time, open, high, low, close
            FROM klines
            WHERE symbol = ? AND interval = '1m' AND open_time >= ? AND open_time <= ?
            ORDER BY open_time ASC
        """, (sym, START_DATE, END_DATE))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return []

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

                net_r = r_result - FEE_PER_TRADE_R
                trades.append({
                    "symbol": sym,
                    "date": dt,
                    "outcome": outcome,
                    "gross_r": r_result,
                    "net_r": net_r
                })

        return trades
    except Exception as e:
        return []

def main():
    valid_symbols = [s for s in CANDIDATE_SYMBOLS if os.path.exists(os.path.join(RAW_DIR, f"{s}.db"))]
    print(f"Test Edilecek Likit Kripto Sembol Sayısı: {len(valid_symbols)}")

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=6) as executor:
        nested = list(executor.map(backtest_one, valid_symbols))

    all_trades = [t for sub in nested for t in sub]
    elapsed = time.time() - t0
    print(f"Backtest {elapsed:.2f} saniyede tamamlandı! Toplam {len(all_trades)} işlem simüle edildi.\n")

    total_t = len(all_trades)
    wins = [t for t in all_trades if t["outcome"] == "WIN"]
    losses = [t for t in all_trades if t["outcome"] == "LOSS"]
    eods = [t for t in all_trades if t["outcome"] == "EOD"]
    eod_pos = [t for t in eods if t["gross_r"] > 0]
    eod_neg = [t for t in eods if t["gross_r"] < 0]

    total_gross_r = sum(t["gross_r"] for t in all_trades)
    total_net_r = sum(t["net_r"] for t in all_trades)
    win_rate = len(wins) / total_t * 100 if total_t > 0 else 0
    pos_rate = (len(wins) + len(eod_pos)) / total_t * 100 if total_t > 0 else 0

    print("=" * 75)
    print("🎯 6 AYLIK GERÇEK BACKTEST SONUÇLARI (NİSAN - EKİM 2026)")
    print("=" * 75)
    print(f"Toplam Simüle Edilen Gün Sayısı: 192 Gün")
    print(f"Açılan Toplam İşlem Sayısı     : {total_t:,} adet (Günde ortalama {total_t/192:.1f} işlem)")
    print(f"Hedefe Ulaşan Tam Win (+3.0R)  : {len(wins):,} adet (%{len(wins)/total_t*100:.2f})")
    print(f"Stop Olan Tam Loss (-1.0R)    : {len(losses):,} adet (%{len(losses)/total_t*100:.2f})")
    print(f"Gün Sonu Kapanan (EOD)        : {len(eods):,} adet (%{len(eods)/total_t*100:.2f})")
    print(f"   • Gün Sonu Kârda (+R)       : {len(eod_pos):,} adet")
    print(f"   • Gün Sonu Zararda (-R)     : {len(eod_neg):,} adet")
    print("-" * 75)
    print(f"Katı Win Rate (Sadece +3R TP)  : %{win_rate:.2f}")
    print(f"Toplam Pozitif Kapanma Oranı   : %{pos_rate:.2f}")
    print(f"TOPLAM NET KAZANÇ (R)          : {total_net_r:+,.2f} R")
    print(f"Aylık Ortalama Net Getiri (R)  : {total_net_r / 6.3:+.2f} R / Ay")
    print(f"Günlük Ortalama Net Getiri (R) : {total_net_r / 192:+.2f} R / Gün")

    sym_scores = defaultdict(lambda: {"trades": 0, "wins": 0, "net_r": 0.0})
    for t in all_trades:
        s = t["symbol"]
        sym_scores[s]["trades"] += 1
        if t["outcome"] == "WIN": sym_scores[s]["wins"] += 1
        sym_scores[s]["net_r"] += t["net_r"]

    top_syms = sorted(sym_scores.items(), key=lambda x: x[1]["net_r"], reverse=True)[:8]
    bot_syms = sorted(sym_scores.items(), key=lambda x: x[1]["net_r"])[:5]

    print("\n🏆 EN ÇOK KAZANDIRAN İLK 8 KOİN:")
    for s, d in top_syms:
        w_pct = d["wins"] / d["trades"] * 100 if d["trades"] > 0 else 0
        print(f"   • {s:<14}: {d['trades']:>3} İşlem | Win: %{w_pct:>4.1f} | Net: {d['net_r']:>+7.2f} R")

    print("\n⚠️ EN ÇOK KAYBETTİREN İLK 5 KOİN:")
    for s, d in bot_syms:
        w_pct = d["wins"] / d["trades"] * 100 if d["trades"] > 0 else 0
        print(f"   • {s:<14}: {d['trades']:>3} İşlem | Win: %{w_pct:>4.1f} | Net: {d['net_r']:>+7.2f} R")

if __name__ == "__main__":
    main()
