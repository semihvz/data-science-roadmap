import urllib.request
import json
import time

BASE_FAPI_URL = "https://fapi.binance.com/fapi/v1"

def fetch_symbol_flow(symbol: str, timeframe: str = "1h", limit: int = 1):
    """
    Fetches Kline data from Binance Futures and calculates Net Taker Capital Inflow.
    Formula:
        Taker Buy Volume = Aggressive buyer market order volume (USDT)
        Taker Sell Volume = Aggressive seller market order volume (USDT)
        Net Inflow = Taker Buy Volume - Taker Sell Volume
                   = 2 * Taker Buy Volume - Total Volume
    """
    url = f"{BASE_FAPI_URL}/klines?symbol={symbol}&interval={timeframe}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        
        if not data:
            return None

        # Aggregate across requested candles
        total_quote_vol = 0.0
        taker_buy_quote_vol = 0.0
        open_price = float(data[0][1])
        close_price = float(data[-1][4])

        for candle in data:
            total_quote_vol += float(candle[7])       # Total quote asset volume (USDT)
            taker_buy_quote_vol += float(candle[10])  # Taker buy quote asset volume (USDT)

        taker_sell_quote_vol = total_quote_vol - taker_buy_quote_vol
        net_inflow_usdt = taker_buy_quote_vol - taker_sell_quote_vol
        price_change_pct = ((close_price - open_price) / open_price) * 100.0 if open_price > 0 else 0.0
        inflow_ratio = (taker_buy_quote_vol / total_quote_vol * 100.0) if total_quote_vol > 0 else 50.0

        return {
            "symbol": symbol,
            "open_price": open_price,
            "close_price": close_price,
            "price_change_pct": price_change_pct,
            "total_volume_usdt": total_quote_vol,
            "taker_buy_usdt": taker_buy_quote_vol,
            "taker_sell_usdt": taker_sell_quote_vol,
            "net_inflow_usdt": net_inflow_usdt,
            "buy_ratio_pct": inflow_ratio,
            "timeframe": timeframe
        }
    except Exception as e:
        return None

def fetch_symbol_derivatives_info(symbol: str):
    """
    Fetches Open Interest and latest Funding Rate for a given symbol.
    """
    info = {"funding_rate_pct": 0.0, "open_interest_usdt": 0.0}
    try:
        # Funding rate
        prem_url = f"{BASE_FAPI_URL}/premiumIndex?symbol={symbol}"
        req_p = urllib.request.Request(prem_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_p, timeout=4) as r:
            p_data = json.loads(r.read().decode())
            info["funding_rate_pct"] = float(p_data.get("lastFundingRate", 0.0)) * 100.0

        # Open interest
        oi_url = f"{BASE_FAPI_URL}/openInterest?symbol={symbol}"
        req_oi = urllib.request.Request(oi_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_oi, timeout=4) as r:
            oi_data = json.loads(r.read().decode())
            info["open_interest"] = float(oi_data.get("openInterest", 0.0))
    except Exception:
        pass
    return info
