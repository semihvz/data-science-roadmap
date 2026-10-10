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

BTC_BY_TIME, BTC_DAY_OPEN = load_btc_map()

def extract_breakouts_for_sym(sym):
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
        if not rows:
            return []

        day_bars = defaultdict(list)
        for r in rows:
            day_bars[r[0][:10]].append(r)

        breakouts = []
        for dt, bars in day_bars.items():
            if len(bars) < 720:
                continue
            day_open = bars[0][1]
            if day_open <= 0:
                continue
            target = day_open * 1.03
            entry_idx = -1
            entry_p = target
            for i, b in enumerate(bars):
                if b[2] >= target:
                    entry_idx = i
                    entry_p = target if b[1] <= target else b[1]
                    break
            if entry_idx != -1 and entry_idx < len(bars) - 1:
                cum_vol = sum(b[5] for b in bars[:entry_idx + 1])
                # Calculate relative volume (vol of first entry_idx bars vs expected)
                breakouts.append({
                    "symbol": sym,
                    "date": dt,
                    "entry_idx": entry_idx,
                    "entry_time": bars[entry_idx][0],
                    "entry_price": entry_p,
                    "cum_vol": cum_vol,
                    "bars": bars[entry_idx + 1:],
                    "last_close": bars[-1][4]
                })
        return breakouts
    except Exception:
        return []

def evaluate_trades(breakout_list, sl_pct=0.022, tp_pct=0.066, be_trigger=None):
    fee = 0.04
    wins, losses, eods = 0, 0, 0
    net_r_total = 0.0

    for b in breakout_list:
        ep = b["entry_price"]
        tp_p = ep * (1.0 + tp_pct)
        sl_p = ep * (1.0 - sl_pct)
        be_p = ep * (1.0 + sl_pct * be_trigger) if be_trigger else None
        
        hit_be = False
        outcome = None
        r_res = 0.0

        for bar in b["bars"]:
            if be_trigger and not hit_be and bar[2] >= be_p:
                hit_be = True
                sl_p = ep # Move SL to breakeven

            hit_tp = (bar[2] >= tp_p)
            hit_sl = (bar[3] <= sl_p)

            if hit_tp and hit_sl:
                outcome = "LOSS"
                r_res = 0.0 if hit_be else -1.0
                break
            elif hit_sl:
                outcome = "LOSS"
                r_res = 0.0 if hit_be else -1.0
                break
            elif hit_tp:
                outcome = "WIN"
                r_res = tp_pct / sl_pct
                break

        if outcome is None:
            outcome = "EOD"
            gain = (b["last_close"] - ep) / ep
            r_res = gain / sl_pct
            eods += 1
        elif outcome == "WIN":
            wins += 1
        else:
            losses += 1

        net_r_total += (r_res - fee)

    tot = len(breakout_list)
    wr = wins / tot * 100 if tot else 0
    return tot, wins, losses, eods, wr, net_r_total

def main():
    valid = [s for s in CANDIDATE_SYMBOLS if os.path.exists(os.path.join(RAW_DIR, f"{s}.db")) and s != "BTCUSDT"]
    print(f"Toplam {len(valid)} koin taranıyor...")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=6) as ex:
        nested = list(ex.map(extract_breakouts_for_sym, valid))
    all_breakouts = [b for sub in nested for b in sub]
    print(f"6 Ayda toplam %3 kırılımı yapan aday bar sayısı: {len(all_breakouts)} ({time.time() - t0:.2f} sn)\n")

    # BASELINE (Filtresiz)
    tot, w, l, e, wr, nr = evaluate_trades(all_breakouts, 0.022, 0.066)
    print("=" * 80)
    print(f"0. BAZ MODEL (Filtresiz Her Kırılıma Giriş - 1:3 RR):")
    print(f"   İşlem: {tot} | Win: %{wr:.2f} ({w}W / {l}L / {e}EOD) | Net R: {nr:+.2f} R")
    print("=" * 80)

    # FİLTRE 1: BTC > Günlük Açılış
    f_btc = [b for b in all_breakouts if BTC_BY_TIME.get(b["entry_time"], 0) >= BTC_DAY_OPEN.get(b["date"], 0)]
    tot, w, l, e, wr, nr = evaluate_trades(f_btc, 0.022, 0.066)
    print(f"1. Sadece BTC Trend Filtresi (BTC > Day Open):")
    print(f"   İşlem: {tot} | Win: %{wr:.2f} ({w}W / {l}L) | Net R: {nr:+.2f} R")

    # FİLTRE 2: İlk 4 Saat (entry_idx <= 240)
    f_time = [b for b in f_btc if b["entry_idx"] <= 240]
    tot, w, l, e, wr, nr = evaluate_trades(f_time, 0.022, 0.066)
    print(f"2. BTC Trend + İlk 4 Saat Penceresi:")
    print(f"   İşlem: {tot} | Win: %{wr:.2f} ({w}W / {l}L) | Net R: {nr:+.2f} R")

    # FİLTRE 3: Hacim >= 2M
    f_vol2m = [b for b in f_time if b["cum_vol"] >= 2_000_000]
    tot, w, l, e, wr, nr = evaluate_trades(f_vol2m, 0.022, 0.066)
    print(f"3. BTC Trend + İlk 4 Saat + Hacim >= $2,000,000:")
    print(f"   İşlem: {tot} | Win: %{wr:.2f} ({w}W / {l}L) | Net R: {nr:+.2f} R")

    # FİLTRE 3B: Daha Yüksek Hacim (Hacim >= 5M)
    f_vol5m = [b for b in f_time if b["cum_vol"] >= 5_000_000]
    tot, w, l, e, wr, nr = evaluate_trades(f_vol5m, 0.022, 0.066)
    print(f"3B. BTC Trend + İlk 4 Saat + Yüksek Hacim >= $5,000,000:")
    print(f"   İşlem: {tot} | Win: %{wr:.2f} ({w}W / {l}L) | Net R: {nr:+.2f} R")

    # FİLTRE 3C: Daha Yüksek Hacim (Hacim >= 10M)
    f_vol10m = [b for b in f_time if b["cum_vol"] >= 10_000_000]
    tot, w, l, e, wr, nr = evaluate_trades(f_vol10m, 0.022, 0.066)
    print(f"3C. BTC Trend + İlk 4 Saat + Mega Hacim >= $10,000,000:")
    print(f"   İşlem: {tot} | Win: %{wr:.2f} ({w}W / {l}L) | Net R: {nr:+.2f} R")

    # FİLTRE 4: Breakeven Stop Kuralı (+1.5R'a gelince Stop Başabaşa Çekilsin)
    print("\n" + "=" * 80)
    print("4. KÂR KORUMA / TRAILING STOP (Filtre 3 Üzerinde):")
    tot, w, l, e, wr, nr = evaluate_trades(f_vol2m, 0.022, 0.066, be_trigger=1.5)
    print(f"   1:3 RR (+1.5R'da Başabaşa Çek): İşlem: {tot} | Win: %{wr:.2f} | Net R: {nr:+.2f} R")
    tot, w, l, e, wr, nr = evaluate_trades(f_vol2m, 0.022, 0.066, be_trigger=1.0)
    print(f"   1:3 RR (+1.0R'da Başabaşa Çek): İşlem: {tot} | Win: %{wr:.2f} | Net R: {nr:+.2f} R")

    # FİLTRE 5: R:R Oranı Varyasyonları (Filtre 3 Üzerinde)
    print("\n" + "=" * 80)
    print("5. FARKLI R:R HEDEFLERİ (Filtre 3 Üzerinde):")
    tot, w, l, e, wr, nr = evaluate_trades(f_vol2m, 0.022, 0.044) # 1:2 RR
    print(f"   1:2.0 RR (SL: -%2.2 | TP: +%4.4): İşlem: {tot} | Win: %{wr:.2f} | Net R: {nr:+.2f} R")
    tot, w, l, e, wr, nr = evaluate_trades(f_vol2m, 0.022, 0.055) # 1:2.5 RR
    print(f"   1:2.5 RR (SL: -%2.2 | TP: +%5.5): İşlem: {tot} | Win: %{wr:.2f} | Net R: {nr:+.2f} R")

    # FİLTRE 6: PORTFÖY DİSİPLİNİ - Günde Sadece Günün En Yüksek Hacimli Koinini Seçme
    print("\n" + "=" * 80)
    print("6. PORTFÖY DİSİPLİNİ (Günde Sadece En Güçlü Hacme Sahip 1 veya 2 Koin):")
    by_day = defaultdict(list)
    for b in f_vol2m:
        by_day[b["date"]].append(b)

    top1_trades = []
    top2_trades = []
    for dt, blist in by_day.items():
        s = sorted(blist, key=lambda x: x["cum_vol"], reverse=True)
        top1_trades.append(s[0])
        top2_trades.extend(s[:2])

    tot, w, l, e, wr, nr = evaluate_trades(top1_trades, 0.022, 0.066)
    print(f"   Günde Max 1 Koin (En Yüksek Hacimli - 1:3 RR): {tot} İşlem | Win: %{wr:.2f} | Net R: {nr:+.2f} R")
    tot, w, l, e, wr, nr = evaluate_trades(top1_trades, 0.022, 0.044)
    print(f"   Günde Max 1 Koin (En Yüksek Hacimli - 1:2 RR): {tot} İşlem | Win: %{wr:.2f} | Net R: {nr:+.2f} R")
    # FİLTRE 7: OPTİMAL KOMBİNASYON (01:00 - 04:00 UTC, Hacim >= 10M, BTC > Open)
    print("\n" + "=" * 80)
    print("7. 🎯 OPTİMAL KANTİTATİF FİLTRE SETİ:")
    print("   • BTC Trend Filtresi  : Giriş anında BTC > Günlük Açılış")
    print("   • Zaman Penceresi     : 01:00 - 04:00 UTC (Dakika 60 - 240, 00:00 whipsaw elendi)")
    print("   • Kurumsal Hacim Eşiği: Kümülatif İşlem Hacmi >= $10,000,000")
    print("   • R:R Oranı           : 1:3 (SL: -%2.2 | TP: +%6.6)")
    print("=" * 80)
    
    opt_trades = [
        b for b in all_breakouts 
        if 60 <= b["entry_idx"] <= 240 
        and b["cum_vol"] >= 10_000_000 
        and BTC_BY_TIME.get(b["entry_time"], 0) >= BTC_DAY_OPEN.get(b["date"], 0)
    ]
    tot, w, l, e, wr, nr = evaluate_trades(opt_trades, 0.022, 0.066)
    eod_pos = [b for b in opt_trades] # checked in evaluate
    print(f"Toplam İşlem Sayısı            : {tot} adet (Günde ortalama {tot/192:.2f} işlem)")
    print(f"Hedefe Ulaşan Tam Win (+3.0R)  : {w} adet (%{wr:.2f})")
    print(f"Stop Olan Tam Loss (-1.0R)    : {l} adet (%{l/tot*100:.2f})")
    print(f"Gün Sonu Kapanan (EOD)        : {e} adet (%{e/tot*100:.2f})")
    print(f"TOPLAM NET KAZANÇ (R)          : {nr:+.2f} R")
    print(f"Aylık Ortalama Net Getiri (R)  : {nr / 6.3:+.2f} R / Ay")
    print(f"Günlük Ortalama Net Getiri (R) : {nr / 192:+.2f} R / Gün")

    sym_res = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "eod": 0, "net_r": 0.0})
    fee = 0.04
    for b in opt_trades:
        ep = b["entry_price"]
        tp_p = ep * 1.066
        sl_p = ep * (1.0 - 0.022)
        outcome = None
        r_res = 0.0
        for bar in b["bars"]:
            hit_tp = (bar[2] >= tp_p)
            hit_sl = (bar[3] <= sl_p)
            if hit_tp and hit_sl:
                outcome = "LOSS"; r_res = -1.0; break
            elif hit_sl:
                outcome = "LOSS"; r_res = -1.0; break
            elif hit_tp:
                outcome = "WIN"; r_res = 3.0; break
        if outcome is None:
            gain = (b["last_close"] - ep) / ep
            r_res = gain / 0.022
        net_r = r_res - fee
        s = b["symbol"]
        sym_res[s]["trades"] += 1
        if outcome == "WIN": sym_res[s]["wins"] += 1
        elif outcome == "LOSS": sym_res[s]["losses"] += 1
        else: sym_res[s]["eod"] += 1
        sym_res[s]["net_r"] += net_r

    print("\n🌟 OPTİMAL MODELDE EN ÇOK KAZANDIRAN 10 KOİN:")
    for s, d in sorted(sym_res.items(), key=lambda x: x[1]["net_r"], reverse=True)[:10]:
        w_pct = d["wins"] / d["trades"] * 100
        print(f"   • {s:<14}: {d['trades']:>2} İşlem | Win: %{w_pct:>4.1f} ({d['wins']}W / {d['losses']}L) | Net: {d['net_r']:>+6.2f} R")

    print("\n⚠️ OPTİMAL MODELDE EN ÇOK KAYBETTİREN 5 KOİN:")
    for s, d in sorted(sym_res.items(), key=lambda x: x[1]["net_r"])[:5]:
        w_pct = d["wins"] / d["trades"] * 100
        print(f"   • {s:<14}: {d['trades']:>2} İşlem | Win: %{w_pct:>4.1f} ({d['wins']}W / {d['losses']}L) | Net: {d['net_r']:>+6.2f} R")

if __name__ == "__main__":
    main()

