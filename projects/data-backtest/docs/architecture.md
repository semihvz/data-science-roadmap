# System Architecture & Design

The **Binance Futures Trade Simulator Engine** is designed for high-performance, deterministic, and crash-safe processing of 1-minute OHLCV datasets across cryptocurrency markets.

## Pipeline Flow

```
Raw Input Dataset (SQLite .db / CSV)
       │
       ▼
Data Reader & SoA Memory Layout
       │
       ▼
Data Validation & Gap Segmentation
       │
       ▼
Segment Tree RMQ Index Construction
       │
       ▼
Parallel Simulation Workers (Zero Heap Allocation Hot Loop)
       │
       ▼
Bounded Thread-Safe Queue (Backpressure under 3072 MB RAM)
       │
       ▼
Single Dedicated SQLite Writer Thread (Batched Transactions)
       │
       ▼
PRAGMA Integrity Check & Atomic Rename (.partial -> .sqlite)
```

## Key Architectural Decisions

1. **Memory Budget & Cache Locality**:
   - Uses Struct-of-Arrays (SoA) layout for price arrays (`timestamps[]`, `open[]`, `high[]`, `low[]`, `close[]`, `volume[]`).
   - Keeps total peak memory strictly under the default **3072 MB RSS** limit.

2. **Concurrency & Thread Safety**:
   - Worker threads perform read-only range queries over immutable Segment Trees.
   - Dedicated writer thread consumes from a bounded `concurrency::BoundedQueue` to eliminate lock contention on SQLite.

3. **Crash Safety & Reproducibility**:
   - Trades are assigned a logical unique key `(run_id, entry_bar_index, side)`.
   - SQLite output uses WAL mode and atomic transaction commits.
