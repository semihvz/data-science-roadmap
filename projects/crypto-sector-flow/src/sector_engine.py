import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from flow_calculator import fetch_symbol_flow

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "sectors.json")

class SectorFlowEngine:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.sectors = self._load_config()

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def scan_all_sectors(self, timeframe="1h", limit=1):
        """
        Scans all configured sectors concurrently and computes aggregated sector flows.
        """
        # Collect all unique symbols to minimize redundant requests
        all_symbols = set()
        for sec, info in self.sectors.items():
            for s in info["symbols"]:
                all_symbols.add(s)

        # Concurrently fetch symbol flows
        def task(s):
            return s, fetch_symbol_flow(s, timeframe=timeframe, limit=limit)

        with ThreadPoolExecutor(max_workers=25) as executor:
            symbol_results = dict(executor.map(lambda s: task(s), all_symbols))

        sector_summary = []

        for sector_name, info in self.sectors.items():
            symbols = info["symbols"]
            sec_total_vol = 0.0
            sec_taker_buy = 0.0
            sec_taker_sell = 0.0
            sec_net_inflow = 0.0
            price_changes = []
            
            valid_symbols_data = []

            for sym in symbols:
                res = symbol_results.get(sym)
                if res:
                    sec_total_vol += res["total_volume_usdt"]
                    sec_taker_buy += res["taker_buy_usdt"]
                    sec_taker_sell += res["taker_sell_usdt"]
                    sec_net_inflow += res["net_inflow_usdt"]
                    price_changes.append(res["price_change_pct"])
                    valid_symbols_data.append(res)

            if not valid_symbols_data:
                continue

            avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0.0
            overall_buy_ratio = (sec_taker_buy / sec_total_vol * 100.0) if sec_total_vol > 0 else 50.0

            # Find MVP (Top Inflow) and Laggard (Top Outflow)
            valid_symbols_data.sort(key=lambda x: x["net_inflow_usdt"], reverse=True)
            mvp_token = valid_symbols_data[0]
            laggard_token = valid_symbols_data[-1]

            # Determine Flow Sentiment
            if sec_net_inflow > 1_000_000:
                sentiment = "GÜÇLÜ GİRİŞ 🚀"
            elif sec_net_inflow > 0:
                sentiment = "ILIMLI GİRİŞ 🟢"
            elif sec_net_inflow < -1_000_000:
                sentiment = "GÜÇLÜ ÇIKIŞ 💥"
            else:
                sentiment = "ILIMLI ÇIKIŞ 🔴"

            sector_summary.append({
                "sector": sector_name,
                "description": info["description"],
                "total_volume_usdt": sec_total_vol,
                "net_inflow_usdt": sec_net_inflow,
                "buy_ratio_pct": overall_buy_ratio,
                "avg_price_change_pct": avg_price_change,
                "sentiment": sentiment,
                "mvp_symbol": mvp_token["symbol"],
                "mvp_net_inflow": mvp_token["net_inflow_usdt"],
                "mvp_price_change": mvp_token["price_change_pct"],
                "laggard_symbol": laggard_token["symbol"],
                "laggard_net_inflow": laggard_token["net_inflow_usdt"],
                "symbols_count": len(valid_symbols_data),
                "symbols_details": valid_symbols_data
            })

        # Rank sectors by net inflow descending
        sector_summary.sort(key=lambda x: x["net_inflow_usdt"], reverse=True)
        return sector_summary

if __name__ == "__main__":
    import sys
    print("Testing SectorFlowEngine...")
    engine = SectorFlowEngine()
    results = engine.scan_all_sectors(timeframe="1h")
    for r in results:
        print(f"[{r['sector']:<24}] Net Inflow: ${r['net_inflow_usdt']:>13,.0f} | Fiyat: {r['avg_price_change_pct']:>6.2f}% | Lider: {r['mvp_symbol']} ({r['sentiment']})")
