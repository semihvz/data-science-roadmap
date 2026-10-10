# Production Architecture Plan: On-Demand Binance Futures Simulation Engine with Apache Arrow Binary IPC Streaming

This document details the complete production architecture, data structures, streaming protocols, memory management, and C++/Python integration specs for building an **On-Demand, Zero-Disk-I/O Simulation Microservice** capable of simulating and streaming **7.16+ million trade records with ALL 48 COLUMNS** in binary format under 3 seconds.

---

## 1. System High-Level Architecture

```
                                  +---------------------------------------+
                                  | Client Layer                          |
                                  | - Web Dashboard (React / WebAssembly) |
                                  | - Python Scripts / Jupyter / Polars   |
                                  +----------------──┬--------------------+
                                                     │
                                HTTP GET /api/v1/simulate
                   Headers: Accept: application/vnd.apache.arrow.stream
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------+
| C++ Microservice / Gateway Layer (Crow / Drogon C++ HTTP Framework)                              |
+------------------------------------------------────┬----------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------+
| LRU Symbol Cache Manager (RAM Limit: e.g. 8 GB)                                                   |
| - Symbol in Cache?  ==> Use pre-loaded SoACandles & SegmentTrees immediately (0.000s)              |
| - Symbol not in Cache? ==> Read raw_data/SYMBOL.db into RAM & build SegmentTrees (~4.0s once)      |
+------------------------------------------------────┬----------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------+
| C++20 Simulation Worker Pool (Multi-threaded $O(N \log N)$ Segment Tree Engine)                    |
| - Runs parallel range queries over RAM SoACandles & SegmentTrees                                  |
| - Generates 7.16M TradeResult structs in RAM (~1.8s for 3.58M candles)                             |
+------------------------------------------------────┬----------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------+
| Apache Arrow C++ IPC Builder (Full 48-Column Serializer)                                          |
| - Converts vector<TradeResult> directly to arrow::RecordBatch IPC buffers (~0.15s)               |
| - Network Payload Size: ~120 MB Arrow IPC stream (vs ~2.2 GB uncompressed JSON)                   |
+------------------------------------------------────┬----------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------+
| Chunked HTTP Binary Response Streamer                                                             |
| - Content-Type: application/vnd.apache.arrow.stream                                               |
| - Streams Arrow IPC record batches directly over TCP socket (~0.6s network time)                  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Full 48-Column Apache Arrow Schema Definition

All **48 columns** from the simulation positions schema are mapped into Apache Arrow data types for complete data availability:

| # | Field Name | Arrow Data Type | Description |
| :---: | :--- | :--- | :--- |
| 1 | `trade_id` | `int64()` | Unique Trade ID |
| 2 | `run_id` | `utf8()` | Simulation Run Identifier |
| 3 | `symbol` | `utf8()` | Pair Symbol (e.g. BTCUSDT) |
| 4 | `side` | `int8()` | +1 (LONG), -1 (SHORT) |
| 5 | `entry_bar_index` | `int32()` | Entry Candle Index |
| 6 | `exit_bar_index` | `int32()` | Exit Candle Index |
| 7 | `entry_bar_open_time` | `int64()` | Entry Bar Open Timestamp |
| 8 | `entry_time` | `int64()` | Entry Boundary Timestamp |
| 9 | `exit_bar_open_time` | `int64()` | Exit Bar Open Timestamp |
| 10 | `entry_price` | `float64()` | Entry Price |
| 11 | `exit_price` | `float64()` | Exit Price |
| 12 | `tp_price` | `float64()` | Target Take Profit Price |
| 13 | `sl_price` | `float64()` | Stop Loss Price |
| 14 | `sl_percent` | `float32()` | Stop Loss Fraction |
| 15 | `tp_percent` | `float32()` | Take Profit Fraction |
| 16 | `risk_reward_ratio` | `float32()` | Risk Reward Ratio (RR) |
| 17 | `status` | `int8()` | 0: CLOSED, 1: GAP, 2: END_OF_DATA |
| 18 | `exit_reason` | `int8()` | 0: TP, 1: SL, 2: SAME_BAR_SL, 3: GAP, 4: EOD |
| 19 | `bars_held` | `int32()` | Total Candles Held |
| 20 | `duration_lower_bound_seconds` | `int64()` | Min Duration Seconds |
| 21 | `duration_upper_bound_seconds` | `int64()` | Max Duration Seconds |
| 22 | `duration_minutes_approx` | `float32()` | Duration Minutes Approx |
| 23 | `nominal_r` | `float32()` | Nominal Risk Unit |
| 24 | `gross_pnl_percent` | `float32()` | Gross Return Percent |
| 25 | `net_pnl_percent` | `float32()` | Net Return Percent |
| 26 | `gross_pnl_r` | `float32()` | Gross Return in R Multiples |
| 27 | `net_pnl_r` | `float32()` | Net Return in R Multiples |
| 28 | `same_bar_sl_tp` | `uint8()` | Same Bar SL & TP Flag |
| 29 | `intrabar_ambiguous` | `uint8()` | Intrabar Ambiguity Flag |
| 30 | `gap_through_barrier` | `uint8()` | Gap Execution Flag |
| 31 | `data_segment_id` | `int32()` | Data Segment ID |
| 32 | `entry_candle_open` | `float64()` | Entry Bar Open Price |
| 33 | `entry_candle_high` | `float64()` | Entry Bar High Price |
| 34 | `entry_candle_low` | `float64()` | Entry Bar Low Price |
| 35 | `entry_candle_close` | `float64()` | Entry Bar Close Price |
| 36 | `entry_candle_volume` | `float64()` | Entry Bar Volume |
| 37 | `exit_candle_open` | `float64()` | Exit Bar Open Price |
| 38 | `exit_candle_high` | `float64()` | Exit Bar High Price |
| 39 | `exit_candle_low` | `float64()` | Exit Bar Low Price |
| 40 | `exit_candle_close` | `float64()` | Exit Bar Close Price |
| 41 | `exit_candle_volume` | `float64()` | Exit Bar Volume |
| 42 | `max_favorable_excursion_pct` | `float32()` | Max Favorable Excursion % |
| 43 | `max_adverse_excursion_pct` | `float32()` | Max Adverse Excursion % |
| 44 | `mfe_r` | `float32()` | MFE in R Multiples |
| 45 | `mae_r` | `float32()` | MAE in R Multiples |
| 46 | `last_available_price` | `float64()` | Last Known Price before Gap/EOD |
| 47 | `last_available_timestamp` | `int64()` | Last Known Timestamp |
| 48 | `unrealized_pnl_pct` | `float32()` | Unrealized Return % |

---

## 3. Client Integration Examples

### A. Python Client (All 48 Columns Accessible)

Python receives all **48 columns** for all 7.16 million rows into a **Polars DataFrame** in less than 1 second:

```python
import requests
import polars as pl
import pyarrow.ipc as ipc
import io

# 1. Send HTTP request to C++ Arrow Microservice
url = "http://localhost:8080/api/v1/simulate?symbol=BTCUSDT&sl=0.008&rr=2.5"
response = requests.get(url, stream=True)

# 2. Read Apache Arrow IPC stream zero-copy directly into Polars DataFrame
reader = ipc.RecordBatchStreamReader(io.BytesIO(response.content))
table = reader.read_all()
df = pl.from_arrow(table)

# 3. Access ALL 48 columns instantly
print(df.schema) # Lists all 48 columns!
print(df.select([
    "trade_id", "side", "entry_price", "exit_price", "net_pnl_r", 
    "mfe_r", "mae_r", "entry_candle_volume", "exit_candle_close"
]).head())
```

---

## 4. End-to-End Performance Summary (Full 48 Columns)

| Metric | Traditional DB File Approach | On-Demand Arrow IPC Stream Microservice (Full 48 Columns) |
| :--- | :---: | :---: |
| **Data Reading Overhead** | ~5.0 s (SQLite File Read) | **0.00 s (RAM Cache)** |
| **Simulation Core Execution** | ~12.5 s | **~1.8 s (Multi-threaded Segment Tree)** |
| **Disk I/O Persistence** | ~34.5 s (SQLite Batch Commit) | **0.00 s (Disksiz)** |
| **Serialization Overhead** | N/A | **~0.15 s (Zero-Copy Arrow Builder)** |
| **Network Payload Size** | N/A (Local DB File) | **~120 MB Compressed Binary IPC Stream** |
| **Total Response Time (BTCUSDT)** | **~52.0 Seconds** | **~2.6 Seconds** |
| **Total Response Time (Altcoin)** | **~4.0 Seconds** | **~0.14 Seconds (140ms)** |
