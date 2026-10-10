import glob
import os
import sqlite3
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

RAW_DIR = "/home/smhvz/Desktop/DATA-SCIENCE/projects/data-backtest/raw_data"
db_files = sorted([f for f in glob.glob(os.path.join(RAW_DIR, "*.db")) if not f.endswith(".tmp")])

# Date range: Past 6 months (2026-04-01 to 2026-10-09)
START_DATE = "2026-04-01 00:00:00"
END_DATE = "2026-10-09 23:59:59"

SL_PCT = 0.022  # %2.2 Stop Loss
TP_PCT = 0.066  # %6.6 Take Profit
ENTRY_THRESHOLD = 0.03 # %3.0 Entry Trigger from Day Open
FEE_PER_TRADE_R = 0.04 # Commission + slippage in R terms (~0.08% / 2.2% = ~0.036R)

def backtest_symbol(db_path):
    sym = os.path.basename(db_path).replace(".db", "")
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cur = conn.cursor()
        
        # We need 1m bars
        query = """
            SELECT open_time, open, high, low, close, quote_volume
            FROM klines
            WHERE symbol = ? AND interval = '1m' AND open_time >= ? AND open_time <= ?
            ORDER BY open_time ASC
        """
        cur.execute(query, (sym, START_DATE, END_DATE))
        rows = cur.fetchall()
        conn.close()
        
        if not rows or len(rows) < 1440:
            return sym, []

        day_bars = defaultdict(list)
        for r in rows:
            day_bars[r[0][:10]].append(r)

        symbol_trades = []

        for dt, bars in day_bars.items():
            if len(bars) < 720: # At least half day
                continue

            day_open = bars[0][1]
            if day_open <= 0:
                continue

            entry_target = day_open * (1.0 + ENTRY_THRESHOLD)
            entry_idx = -1
            entry_price = entry_target

            # Find first 1m bar that touches +3%
            for i, b in enumerate(bars):
                if b[2] >= entry_target: # high >= target
                    entry_idx = i
                    # Real execution price: if bar opened above target, use open, else use target
                    entry_price = entry_target if b[1] <= entry_target else b[1]
                    break

            if entry_idx != -1 and entry_idx < len(bars) - 1:
                tp_price = entry_price * (1.0 + TP_PCT)
                sl_price = entry_price * (1.0 - SL_PCT)

                outcome = None
                r_result = 0.0
                exit_time = None
                exit_price = entry_price

                # Check subsequent bars until end of day
                for b in bars[entry_idx + 1:]:
                    hit_tp = (b[2] >= tp_price)
                    hit_sl = (b[3] <= sl_price)

                    if hit_tp and hit_sl:
                        # Conservative worst-case execution: assume stop hit first
                        outcome = "LOSS"
                        r_result = -1.0
                        exit_price = sl_price
                        exit_time = b[0]
                        break
                    elif hit_sl:
                        outcome = "LOSS"
                        r_result = -1.0
                        exit_price = sl_price
                        exit_time = b[0]
                        break
                    elif hit_tp:
                        outcome = "WIN"
                        r_result = 3.0
                        exit_price = tp_price
                        exit_time = b[0]
                        break

                if outcome is None:
                    # Position remained open until end of day (23:59)
                    outcome = "EOD"
                    exit_price = bars[-1][4]
                    exit_time = bars[-1][0]
                    # Calculate fractional R
                    gain_pct = (exit_price - entry_price) / entry_price
                    r_result = gain_pct / SL_PCT

                # Net R after fees
                net_r = r_result - FEE_PER_TRADE_R

                symbol_trades.append({
                    "symbol": sym,
                    "date": dt,
                    "entry_time": bars[entry_idx][0],
                    "entry_price": entry_price,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "outcome": outcome,
                    "gross_r": r_result,
                    "net_r": net_r,
                    "day_total_volume": sum(b[5] for b in bars)
                })

        return sym, symbol_trades
    except Exception as e:
        return sym, []

print(f"⚡ 6 Aylık Gerçek Backtest Başlatılıyor...")
print(f"Tarih Aralığı: {START_DATE[:10]} - {END_DATE[:10]}")
print(f"Strateji Parametreleri: Giriş: +%3.0 | Stop Loss: -%2.2 | Take Profit: +%6.6 (1:3 R:R)")
print(f"Toplam Taranacak Veri Tabanı Sayısı: {len(db_files)}\n")

t0 = time.time()
with ThreadPoolExecutor(max_workers=20) as executor:
    results_dict = dict(executor.map(backtest_symbol, db_files))

elapsed = time.time() - t0
print(f"✅ Tüm simülasyon {elapsed:.2f} saniyede tamamlandı!\n")

all_trades = [t for sub in results_dict.values() for t in sub]

# 1. Genel Sonuçlar (Tüm Koinler - Filtresiz)
total_trades = len(all_trades)
wins = [t for t in all_trades if t["outcome"] == "WIN"]
losses = [t for t in all_trades if t["outcome"] == "LOSS"]
eods = [t for t in all_trades if t["outcome"] == "EOD"]
eod_positive = [t for t in eods if t["gross_r"] > 0]
eod_negative = [t for t in eods if t["gross_r"] < 0]

total_gross_r = sum(t["gross_r"] for t in all_trades)
total_net_r = sum(t["net_r"] for t in all_trades)
win_rate_strict = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0
win_rate_with_eod = ((len(wins) + len(eod_positive)) / total_trades * 100.0) if total_trades > 0 else 0.0

print("=" * 80)
print("📊 1. TÜM PİYASA GENELİ BACKTEST SONUÇLARI (6 AY / FİLTRESİZ)")
print("=" * 80)
print(f"Toplam Açılan İşlem Sayısı: {total_trades:,} adet")
print(f"Hedefe Ulaşan Tam Win (+3.0R) : {len(wins):,} (%{len(wins)/total_trades*100:.1f})")
print(f"Stop Olan Tam Loss (-1.0R)   : {len(losses):,} (%{len(losses)/total_trades*100:.1f})")
print(f"Gün Sonu Kapanan (EOD)       : {len(eods):,} (%{len(eods)/total_trades*100:.1f})")
print(f"   ↳ Gün Sonunda Kârda Kapanan (+R) : {len(eod_positive):,}")
print(f"   ↳ Gün Sonunda Zararda Kapanan (-R): {len(eod_negative):,}")
print("-" * 80)
print(f"Katı Win Rate (Sadece +3R TP) : %{win_rate_strict:.2f}")
print(f"Kârda Kapanma Oranı (TP + EOD+): %{win_rate_with_eod:.2f}")
print(f"Toplam Brüt R Kazancı         : {total_gross_r:+,.2f} R")
print(f"Komisyon/Kayma Sonrası NET R  : {total_net_r:+,.2f} R")
avg_daily_trades = total_trades / 190.0
avg_daily_net_r = total_net_r / 190.0
print(f"Günlük Ortalama Açılan İşlem  : {avg_daily_trades:.1f} işlem/gün")
print(f"Günlük Ortalama Net R Getirisi: {avg_daily_net_r:+.2f} R / gün")

# 2. Likidite Filtreli Sonuçlar (Günde En Az $5M Hacimli Koinler)
filtered_trades = [t for t in all_trades if t["day_total_volume"] >= 5_000_000]
if filtered_trades:
    f_total = len(filtered_trades)
    f_wins = [t for t in filtered_trades if t["outcome"] == "WIN"]
    f_losses = [t for t in filtered_trades if t["outcome"] == "LOSS"]
    f_net_r = sum(t["net_r"] for t in filtered_trades)
    print("\n" + "=" * 80)
    print("💎 2. LİKİDİTE FİLTRELİ SONUÇLAR (Hacim >= $5,000,000 Olan Gerçekçi Koinler)")
    print("=" * 80)
    print(f"Toplam İşlem Sayısı         : {f_total:,} adet")
    print(f"Win Sayısı (+3.0R TP)       : {len(f_wins):,} (%{len(f_wins)/f_total*100:.1f})")
    print(f"Loss Sayısı (-1.0R Stop)    : {len(f_losses):,} (%{len(f_losses)/f_total*100:.1f})")
    print(f"Likidite Filtreli NET R     : {f_net_r:+,.2f} R")
    print(f"Günlük Ortalama Net R       : {f_net_r / 190.0:+.2f} R / gün")

# 3. En İyi Performans Gösteren İlk 10 Koin
sym_stats = defaultdict(lambda: {"trades": 0, "wins": 0, "net_r": 0.0})
for t in all_trades:
    s = t["symbol"]
    sym_stats[s]["trades"] += 1
    if t["outcome"] == "WIN": sym_stats[s]["wins"] += 1
    sym_stats[s]["net_r"] += t["net_r"]

top_syms = sorted(sym_stats.items(), key=lambda x: x[1]["net_r"], reverse=True)[:10]
print("\n" + "=" * 80)
print("🏆 BU STRATEJİDE EN ÇOK R KAZANDIRAN İLK 10 KOİN (6 AY)")
print("=" * 80)
for s, st in top_syms:
    wr = st["wins"] / st["trades"] * 100 if st["trades"] > 0 else 0
    print(f"   • {s:<15}: {st['trades']:>3} İşlem | Win Rate: %{wr:>5.1f} | Net Kazanç: {st['net_r']:>+7.2f} R")
