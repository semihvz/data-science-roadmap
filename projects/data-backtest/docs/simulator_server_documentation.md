# Binance Futures On-Demand Arrow Simulation Microservice (`simulator_server`)
## Comprehensive System Architecture, API Reference & Developer Guide

> **System Version:** 1.0.0 (C++20 Microservice)  
> **Location:** `/home/smhvz/Desktop/data-backtest/simulator_server/`  
> **Binary Output:** `build/simulator_server`  
> **Default Port:** `8080`

---

## 1. SYSTEM OVERVIEW & ARCHITECTURE

The **`simulator_server`** is a standalone, ultra-high-speed, in-memory C++20 microservice designed for backtesting Binance Futures trading strategies across **742+ cryptocurrency pairs**. 

It operates independently of the main offline database compiler, maintaining a zero-disk-write, zero-copy binary streaming architecture over HTTP sockets.

```
┌─────────────────────────┐       HTTP REST / Binary Arrow        ┌──────────────────────────────┐
│  Python Client          │ ◄───────────────────────────────────► │  C++20 simulator_server      │
│  (BinanceSimulatorClient)│      application/vnd.apache.arrow     │  (Port 8080)                 │
└─────────────────────────┘                                       └──────────────┬───────────────┘
                                                                                 │ Lazy-Load RAM Cache
                                                                                 ▼
                                                                  ┌──────────────────────────────┐
                                                                  │  742+ Symbol Datasets        │
                                                                  │  (raw_data/*.db)             │
                                                                  └──────────────────────────────┘
```

### Key Architectural Highlights
1. **Zero External Dependencies:** Built with embedded SQLite3 amalgamation (`third_party/sqlite3/`).
2. **Disksiz In-Memory Execution:** All simulations are computed dynamically in RAM. No temporary SQLite files or intermediate disk buffers are generated.
3. **Multi-Threaded Parallel Engine:** Configurable worker thread pool (8 threads default) dividing contiguous data segments across CPU cores.
4. **LRU RAM Cache Manager:** Lazy-loads 3.5M+ candle SQLite databases on-demand into RAM with automatic Least Recently Used (LRU) eviction to strictly respect a 3072 MB memory budget.
5. **64 MB Chunked Socket Streaming Loop:** Bypasses POSIX 2 GB signed integer socket write overflows, allowing seamless 2.2+ GB binary payload streaming.

---

## 2. CORE ENGINES & ALGORITHMS

### 2.1 High-Speed $O(N \log N)$ Segment Tree Engine
- **Algorithm:** 1D Range Minimum Query (RMQ) & Range Maximum Query (RMQ) Segment Tree constructed per gap-free data segment.
- **No-Look-Ahead Guarantee:** Trade entry is strictly at `close[i]`. Search ranges for SL/TP barriers start strictly at $i+1$.
- **Performance:** Evaluates over **500,000 trades per second per CPU core**.

### 2.2 KNN 1-Second Synthetic Microstructure Engine (`KNNMicrostructureEngine`)
- **Pattern Matching Library:** Built-in library of **32 normalized 60-second micro-trajectories** covering diverse market structures (Marubozu, Reversal Hammer, Shooting Star, Classic Doji, W/M Double Bottom/Top, Volatile Consolidations).
- **Feature Vector Matching:** Uses weighted Euclidean distance in 3D feature space:
  $$\text{body\_ratio} = \frac{Close - Open}{High - Low + \epsilon}$$
  $$\text{upper\_wick\_ratio} = \frac{High - \max(Open, Close)}{High - Low + \epsilon}$$
  $$\text{lower\_wick\_ratio} = \frac{\min(Open, Close) - Low}{High - Low + \epsilon}$$
- **Same-Bar SL/TP Disambiguation:** Reduces same-bar SL/TP ambiguity rate to **$0$** (`Remaining Intrabar Ambiguous Trades: 0`) by determining sub-second execution order down to 1-second resolution.
- **Stochastic Monte Carlo Sampling:** Supports `seed` (random seed) and `noise` (stochastic perturbation magnitude) parameters to simulate thousands of alternative intraday price paths.

---

## 3. HTTP REST API ENDPOINTS

Base URL: `http://localhost:8080`

### 3.1 `GET /api/v1/simulate` — On-Demand Arrow Trade Simulation

Runs high-speed simulation for a specified symbol and returns binary Arrow stream of all 48 trade columns.

#### Query Parameters
| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `symbol` | String | `"BTCUSDT"` | Symbol dataset name (e.g. `ETHUSDT`, `SOLUSDT`, `BTCUSDT`). |
| `sl` | Float | `0.005` | Stop Loss percentage (e.g. `0.04` for 4.00%). |
| `rr` | Float | `3.0` | Risk-to-Reward ratio (e.g. `10.0` for 10:1 RR). |
| `start_ts` | Int64 | `0` | Optional start Unix timestamp in seconds. |
| `end_ts` | Int64 | `max` | Optional end Unix timestamp in seconds. |
| `resolution` | String | `"1m"` | `"1m"` for fast segment tree, `"1s_knn"` for KNN 1s microstructure resolution. |

#### Response Headers
- `Content-Type: application/vnd.apache.arrow.stream`
- `X-Simulation-Time-Sec: 2.85`
- `X-Total-Trades: 7166108`

---

### 3.2 `GET /api/v1/symbols` — Available Symbol List

Returns a JSON array of all 742+ dataset symbols currently available in `raw_data/`.

#### Example Response
```json
[
  "0GUSDT", "1000000MOGUSDT", "1000BONKUSDT", "ADAUSDT", 
  "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"
]
```

---

### 3.3 `GET /api/v1/candles1s` — Synthetic 1-Second OHLCV Candles

Generates synthetic 1-second OHLCV candles from 1-minute datasets using the KNN Microstructure Engine.

#### Query Parameters
| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `symbol` | String | `"BTCUSDT"` | Symbol dataset name. |
| `max_candles` | Int | `1000` | Max 1m candles to expand to 1s. (`0` = all candles). |
| `start_ts` | Int64 | `0` | Optional start Unix timestamp in seconds. |
| `end_ts` | Int64 | `max` | Optional end Unix timestamp in seconds. |
| `seed` | Int | `0` | Random seed for Monte Carlo stochastic paths. (`0` = deterministic KNN). |
| `noise` | Float | `0.0` | Magnitude of stochastic variation (e.g. `0.05` for 5%). |

#### Binary Stream Schema
6 Column Binary Record Batch: `[timestamp (int64), open (f64), high (f64), low (f64), close (f64), volume (f64)]`.

---

## 4. PYTHON CLIENT API REFERENCE (`BinanceSimulatorClient`)

Location: `simulator_server/python/simulator_client.py`

### 4.1 Class Instantiation
```python
from simulator_client import BinanceSimulatorClient

client = BinanceSimulatorClient(base_url="http://localhost:8080")
```

---

### 4.2 `client.simulate()`
```python
df = client.simulate(
    symbol="ETHUSDT",
    sl=0.04,
    rr=10.0,
    start_date="2023-01-01",
    end_date="2023-12-31",
    resolution="1s_knn"
)
```

---

### 4.3 `client.list_symbols()` / `client.get_available_symbols()`
```python
symbols = client.list_symbols()
print(f"Total Available Symbols: {len(symbols)}")
```

---

### 4.4 `client.get_1s_candles()` / `client.generate_1s_ohlcv()`
```python
df_1s = client.get_1s_candles(
    symbol="ETHUSDT",
    start_date="2023-01-01",
    end_date="2023-01-02",
    seed=42,
    noise=0.05
)
```

---

### 4.5 `client.get_sequential_trades()`
Filters non-overlapping sequential trades (where a new trade on the same side opens only after the previous trade has closed):
```python
long_seq_df = client.get_sequential_trades(df, side=1)
short_seq_df = client.get_sequential_trades(df, side=-1)
```

---

### 4.6 `client.filter_by_date_range()`
```python
df_filtered = client.filter_by_date_range(df, start_date="2023-01-01", end_date="2023-12-31")
```

---

### 4.7 `client.sync_present_data()` / `client.get_all_present_data()` / `client.fetch_all_present_data()`
Automatically detects the last recorded timestamp (`MAX(open_time)`) for each SQLite dataset in `raw_data/*.db`, fetches missing 1-minute klines from Binance Futures REST API up to the present minute, and updates the local databases on disk in place:

```python
# Sync all 742+ symbol datasets up to present time
summary = client.sync_present_data()
# Or using aliases:
summary = client.get_all_present_data()
summary = client.fetch_all_present_data()

# Sync specific symbols
summary = client.sync_present_data(symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"])

# Sync a batch of symbols with max limit
summary = client.sync_present_data(max_symbols=10)
```

**Parameters**:
- `symbols` (*list, optional*): Specific list of symbols to sync. Defaults to `None` (scans all `raw_data/*.db` files).
- `raw_data_dir` (*str, optional*): Path to raw data folder containing SQLite databases.
- `max_symbols` (*int, optional*): Maximum number of symbols to process (useful for batching/testing).
- `show_progress` (*bool, default=True*): Print step-by-step terminal output.

**Returns**:
- `dict`: Summary dict containing `{'total_symbols': int, 'updated_symbols': int, 'total_klines_added': int}`.

---

### 4.8 `client.get_marked_candles()` / `client.fetch_marked_candles()`
Fetches all 1-minute klines for USDT pairs from a specified `start_date` up to today's last completed candle. If a candle for any timestamp `>= start_date` already exists in the SQLite database, it is **REPLACED/OVERWRITTEN** with the freshly fetched candle from Binance REST API:

```python
# Fetch/overwrite all 1m candles for all USDT pairs from '2024-01-01' to present
summary = client.get_marked_candles(start_date="2024-01-01")

# Or specify exact timestamp and symbols
summary = client.get_marked_candles(
    start_date="2024-06-01 00:00:00",
    symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"]
)
```

**Parameters**:
- `start_date` (*str, required*): Starting date string, e.g. `'2024-01-01'` or `'2024-01-01 00:00:00'`.
- `symbols` (*list, optional*): Specific USDT symbols. Defaults to `None` (all `*USDT.db` files).
- `raw_data_dir` (*str, optional*): Path to raw data folder.
- `max_symbols` (*int, optional*): Maximum number of symbols to process.
- `show_progress` (*bool, default=True*): Print step-by-step terminal output.

**Returns**:
- `dict`: Summary dict `{'start_date': str, 'total_symbols': int, 'updated_symbols': int, 'total_klines_fetched': int}`.

---

## 5. POLARS TERMINAL DISPLAY CONFIGURATION

To ensure all 48 columns display cleanly without truncation or data-type header rows:

```python
import polars as pl

pl.Config.set_tbl_cols(-1)                      # Show all 48 columns without truncation
pl.Config.set_tbl_width_chars(10000)            # Disable terminal character width limit
pl.Config.set_tbl_hide_column_data_types(True)  # Hide i64/f64 header row
```

---

## 6. COMPLETE 48-COLUMN TRADE POSITION SCHEMA

| # | Column Name | Type | Description |
| :---: | :--- | :---: | :--- |
| 1 | `trade_id` | `i64` | Sequential 1-based unique trade identifier. |
| 2 | `side` | `i8` | Position side (`1` for LONG, `-1` for SHORT). |
| 3 | `entry_bar_index` | `i32` | Bar index where trade entered (at `close[i]`). |
| 4 | `exit_bar_index` | `i32` | Bar index where trade exited (`-1` if open/unresolved). |
| 5 | `entry_bar_open_time` | `i64` | Open Unix timestamp of entry candle. |
| 6 | `entry_time` | `i64` | Close Unix timestamp of entry candle (actual entry time). |
| 7 | `exit_bar_open_time` | `i64` | Open Unix timestamp of exit candle (`0` if unresolved). |
| 8 | `entry_price` | `f64` | Price at entry (`close[entry_bar_index]`). |
| 9 | `exit_price` | `f64` | Actual exit price (`NaN` if unresolved). |
| 10 | `tp_price` | `f64` | Take Profit target price. |
| 11 | `sl_price` | `f64` | Stop Loss target price. |
| 12 | `sl_percent` | `f64` | Stop Loss percentage (e.g. `0.04`). |
| 13 | `tp_percent` | `f64` | Take Profit percentage (e.g. `0.40`). |
| 14 | `risk_reward_ratio` | `f64` | Risk-to-Reward ratio (e.g. `10.0`). |
| 15 | `status` | `i8` | Position status (`0`=CLOSED, `1`=UNRESOLVED_DUE_TO_GAP, `2`=OPEN_AT_END_OF_DATA). |
| 16 | `exit_reason` | `i8` | Exit reason (`0`=TP, `1`=SL, `2`=SAME_BAR_SL, `3`=GAP, `4`=END_OF_DATA). |
| 17 | `bars_held` | `i32` | Number of 1-minute bars held. |
| 18 | `duration_lower_bound_seconds` | `i64` | Lower bound position duration in seconds. |
| 19 | `duration_upper_bound_seconds` | `i64` | Upper bound position duration in seconds. |
| 20 | `duration_minutes_approx` | `f64` | Approximate duration in minutes. |
| 21 | `nominal_r` | `f64` | Nominal risk unit (1.0). |
| 22 | `gross_pnl_percent` | `f64` | Gross PnL percentage. |
| 23 | `net_pnl_percent` | `f64` | Net PnL percentage. |
| 24 | `gross_pnl_r` | `f64` | Gross PnL in R units (e.g. `+10.0R` or `-1.0R`). |
| 25 | `net_pnl_r` | `f64` | Net PnL in R units. |
| 26 | `same_bar_sl_tp` | `u8` | `1` if both TP and SL were touched in same bar. |
| 27 | `intrabar_ambiguous` | `u8` | `1` if intra-bar order was ambiguous (`0` in KNN mode). |
| 28 | `gap_through_barrier` | `u8` | `1` if price gapped over barrier. |
| 29 | `data_segment_id` | `i32` | Segment ID within dataset. |
| 30 | `entry_candle_open` | `f64` | Open price of entry candle. |
| 31 | `entry_candle_high` | `f64` | High price of entry candle. |
| 32 | `entry_candle_low` | `f64` | Low price of entry candle. |
| 33 | `entry_candle_close` | `f64` | Close price of entry candle. |
| 34 | `entry_candle_volume` | `f64` | Traded volume of entry candle. |
| 35 | `exit_candle_open` | `f64` | Open price of exit candle. |
| 36 | `exit_candle_high` | `f64` | High price of exit candle. |
| 37 | `exit_candle_low` | `f64` | Low price of exit candle. |
| 38 | `exit_candle_close` | `f64` | Close price of exit candle. |
| 39 | `exit_candle_volume` | `f64` | Traded volume of exit candle. |
| 40 | `max_favorable_excursion_pct` | `f64` | Max Favorable Excursion (MFE) percentage. |
| 41 | `max_adverse_excursion_pct` | `f64` | Max Adverse Excursion (MAE) percentage. |
| 42 | `mfe_r` | `f64` | MFE in R units. |
| 43 | `mae_r` | `f64` | MAE in R units. |
| 44 | `last_available_price` | `f64` | Last known price for open/unresolved positions. |
| 45 | `last_available_timestamp` | `i64` | Last known timestamp for open/unresolved positions. |
| 46 | `unrealized_pnl_pct` | `f64` | Unrealized PnL % for open/unresolved positions. |
| 47 | `reserved_1` | `i64` | 64-bit reserved padding field (0). |
| 48 | `reserved_2` | `i64` | 64-bit reserved padding field (0). |
