# Market Microstructure, Volume Spikes & Stop Hunt Detection Guide
------------------------------------------------------------------

This document provides a comprehensive guide to understanding **Market Microstructure**, **Volume Spikes**, **Orderbook Absorption**, and **Stop Hunt / Liquidity Sweep Detection** using 1-minute OHLCV klines data and SQL analytics in the simulation engine.

---

## 1. Market Microstructure & Core Concepts

### 1.1 Volume Spike (Hacim Patlaması)
A **Volume Spike** occurs when the traded volume (base volume or USDT quote volume) in a single 1-minute bar dramatically exceeds historical baseline averages (e.g. 5x - 50x higher than the 20-period moving average).

**Causes**:
- **Institutional Market Orders**: Large funds executing aggressive market orders.
- **Liquidation Cascades**: Automated futures margin call cascades triggering thousands of stop orders in milliseconds.
- **News / Catalyst Breakouts**: Macroeconomic announcements (CPI, FOMC) or technical structure breaks.

### 1.2 Wyckoff Law of Effort vs. Result & Absorption
High volume does **not** always produce large price moves:
- **Effort**: Volume / Traded Capital.
- **Result**: Net Price Delta (`close - open`).

When volume is massive but price movement is near zero (`(close - open) / open ≈ 0%`), **Absorption** is taking place:
- **Limit Wall / Iceberg Order Absorption**: A Market Maker or whale has set a massive Iceberg limit order on the book. As retail traders execute aggressive market orders (creating a Volume Spike), the limit order absorbs all execution without allowing price to move.
- **Reversal Signal**: A High-Volume Doji candle at a key structural level is one of the strongest reversal signals in market microstructure.

---

## 2. Stop Hunt & Liquidity Sweep Detection

### 2.1 Mechanics of a Stop Hunt
Retail traders routinely place Stop-Loss orders immediately above recent Swing Highs (Equal Highs - EQH) or below Swing Lows (Equal Lows - EQL).

Market Makers / Smart Money drive prices beyond these key levels to trigger clusters of stop orders:
1. **Sweep**: Price spikes past the Swing High/Low.
2. **Volume Surge**: Stop orders convert to market orders, causing a sudden spike in `quote_volume` and `trades_count`.
3. **Rejection**: Smart Money absorbs the liquidity and drives price back **inside** the previous range, creating a long candle wick.

### 2.2 Mathematical Detection Rules (1m OHLCV)
A Stop Hunt is identified using 4 quantitative conditions:
1. **Extreme Breach**: `high > MAX(high_50)` or `low < MIN(low_50)` (Breaching 50-bar swing extremes).
2. **Close Rejection**: `close < MAX(high_50)` (for Short Stop Hunt) or `close > MIN(low_50)` (for Long Stop Hunt).
3. **Wick Ratio**: Upper or lower wick is at least 2x larger than the real candle body.
4. **Volume Anomaly**: `quote_volume > 3 * AVG(quote_volume_20)`.

---

## 3. SQL Analytics Queries for Detection

### 3.1 Detecting Relative Volume Spikes (RVOL)
```sql
WITH HacimOrtalamalari AS (
    SELECT 
        symbol,
        open_time,
        open,
        close,
        quote_volume,
        AVG(quote_volume) OVER (
            PARTITION BY symbol 
            ORDER BY open_time 
            ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS ortalama_20m_hacim
    FROM klines
)
SELECT 
    symbol,
    open_time,
    open,
    close,
    ROUND(quote_volume, 2) AS mum_hacmi,
    ROUND(ortalama_20m_hacim, 2) AS ort_hacim,
    ROUND(quote_volume / ortalama_20m_hacim, 2) AS hacim_katlayicisi
FROM HacimOrtalamalari
WHERE ortalama_20m_hacim > 0
ORDER BY hacim_katlayicisi DESC
LIMIT 10;
```

### 3.2 Detecting Iceberg / Absorption Candles (High Vol + Small Body)
```sql
SELECT 
    symbol,
    open_time,
    open,
    close,
    ROUND(quote_volume / 1e6, 2) AS usdt_vol_millions,
    trades_count,
    ROUND(quote_volume / trades_count, 2) AS avg_trade_size_usdt,
    ROUND(ABS((close - open) / open) * 100.0, 3) AS body_pct
FROM klines
WHERE quote_volume > 200000000 AND trades_count > 0
ORDER BY (quote_volume / (ABS((close - open)/open) + 0.001)) DESC
LIMIT 10;
```

### 3.3 Detecting Stop Hunt / Liquidity Sweeps
```sql
WITH PrevExtremes AS (
    SELECT 
        symbol, open_time, open, high, low, close, quote_volume, trades_count,
        MAX(high) OVER (PARTITION BY symbol ORDER BY open_time ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING) AS prev_50_high,
        MIN(low) OVER (PARTITION BY symbol ORDER BY open_time ROWS BETWEEN 50 PRECEDING AND 1 PRECEDING) AS prev_50_low,
        AVG(quote_volume) OVER (PARTITION BY symbol ORDER BY open_time ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS avg_vol
    FROM klines
)
SELECT 
    symbol, open_time, open, high, low, close,
    ROUND((high - prev_50_high) / prev_50_high * 100.0, 2) AS sweep_pct,
    ROUND(quote_volume / 1e6, 2) AS usdt_vol_m,
    CASE 
        WHEN high > prev_50_high AND close < prev_50_high THEN 'BULLISH_STOP_HUNT (Bearish Reversal)'
        WHEN low < prev_50_low AND close > prev_50_low THEN 'BEARISH_STOP_HUNT (Bullish Reversal)'
    END AS stop_hunt_type
FROM PrevExtremes
WHERE (high > prev_50_high AND close < prev_50_high AND (high - MAX(open, close)) > (MAX(open, close) - MIN(open, close)) * 2 AND quote_volume > avg_vol * 3)
ORDER BY quote_volume DESC
LIMIT 10;
```

---

## 4. Live Trading Execution & Bot Integration

### 4.1 Turtle Soup Reversal Strategy
- **Trigger**: 1m bar breaches a key 50-period Swing High/Low and closes back inside the range.
- **Entry**: Immediate Market order on candle close in the direction of rejection (SHORT if high was swept, LONG if low was swept).
- **Stop-Loss**: Just beyond the extreme wick tip (`wick_tip * 1.001`).
- **Take-Profit**: 1:3 Risk-Reward Ratio or opposite liquidity pool.

### 4.2 Python Live Trading Signal Implementation
```python
def check_stop_hunt_signal(df_live):
    """
    Checks the last completed candle for a Liquidity Sweep / Stop Hunt signal.
    """
    last_candle = df_live.iloc[-1]
    prev_50_high = df_live['high'].iloc[-51:-1].max()
    prev_50_low = df_live['low'].iloc[-51:-1].min()
    avg_volume = df_live['volume'].iloc[-21:-1].mean()
    
    # Bearish Reversal (Short Stop Hunt)
    if (last_candle['high'] > prev_50_high and 
        last_candle['close'] < prev_50_high and 
        last_candle['volume'] > avg_volume * 2.5):
        
        return {
            "action": "ENTER_SHORT",
            "entry_price": last_candle['close'],
            "stop_loss": last_candle['high'] * 1.001,
            "take_profit": last_candle['close'] - (last_candle['high'] - last_candle['close']) * 3.0
        }
        
    # Bullish Reversal (Long Stop Hunt)
    if (last_candle['low'] < prev_50_low and 
        last_candle['close'] > prev_50_low and 
        last_candle['volume'] > avg_volume * 2.5):
        
        return {
            "action": "ENTER_LONG",
            "entry_price": last_candle['close'],
            "stop_loss": last_candle['low'] * 0.999,
            "take_profit": last_candle['close'] + (last_candle['close'] - last_candle['low']) * 3.0
        }

    return None
```
