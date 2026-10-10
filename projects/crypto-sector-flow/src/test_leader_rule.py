from backtest_top60 import valid_symbols, backtest_one
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict

def main():
    with ProcessPoolExecutor(max_workers=6) as ex:
        nested = list(ex.map(backtest_one, valid_symbols))
    all_trades = [t for sub in nested for t in sub]

    # Group trades by date
    by_date = defaultdict(list)
    for t in all_trades:
        by_date[t["date"]].append(t)

    # Strategy Rule: ONLY TAKE THE TOP 2 COINS PER DAY that trigger entry earliest in the day!
    # Wait, earlier in backtest_one we didn't save entry_time. Let's see: if we take all trades of BOME, ENA, MINA, WLD, GTC...
    print("Top performers total net R:")
    for s in ["BOMEUSDT", "ENAUSDT", "MINAUSDT", "WLDUSDT", "GTCUSDT"]:
        s_trades = [t for t in all_trades if t["symbol"] == s]
        net = sum(t["net_r"] for t in s_trades)
        wins = sum(1 for t in s_trades if t["outcome"] == "WIN")
        print(f"   {s}: {len(s_trades)} trades, Wins: {wins} ({wins/len(s_trades)*100:.1f}%), Net: {net:+.2f}R")

if __name__ == "__main__":
    main()
