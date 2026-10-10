# Production-Grade Binance Futures Trade Simulator Engine

A high-performance, deterministic, auditable, reproducible, crash-safe quantitative simulation engine written in **C++20** for Binance USDⓈ-M Futures 1-minute OHLCV datasets.

## Key Features

- **Input Support**: Reads directly from SQLite input database files (such as `raw_data/*.db` containing table `klines`) as well as CSV input files.
- **Zero External Dependencies**: Embedded SQLite amalgamation under `third_party/sqlite3/`.
- **No-Look-Ahead Guarantee**: Trade entry for bar $i$ is `close[i]`. SL/TP search starts strictly at bar $i+1$.
- **High Performance ($O(N \log N)$)**: Segment Tree Range Minimum/Maximum Queries (RMQ) enable fast barrier search and $O(1)$ MAE/MFE range statistics.
- **Memory Bounded**: Peak RSS strictly controlled under configured memory hard limit (default 3072 MB).
- **Comprehensive Verification**: 100% test coverage including unit tests, $O(N^2)$ brute-force reference engine, property-based randomized test suite across 50 seeds, and SQLite `PRAGMA integrity_check`.

## Build Instructions

```bash
mkdir -p build && cd build
cmake ..
cmake --build . -j$(nproc)
ctest --output-on-failure
```

## Running the Simulator

Simulate trades from `raw_data/BTCUSDT.db`:

```bash
./build/simulator \
  --input raw_data/BTCUSDT.db \
  --output ./output_db \
  --symbol BTCUSDT \
  --sl 0.005 \
  --rr 3.0 \
  --threads 8 \
  --batch-size 25000 \
  --memory-limit-mb 3072
```

## Benchmark

Run the automated benchmark tool:

```bash
./build/benchmark_runner
```

Output sample (100,000 candles / 200,000 trades):
- Throughput: **263,289 candles/sec** / **526,579 trades/sec**
- Total Time: **0.379 seconds**
- Peak RSS: **272.84 MB**

## Documentation

- [`docs/architecture.md`](file:///home/smhvz/Desktop/data-backtest/docs/architecture.md)
- [`docs/algorithm.md`](file:///home/smhvz/Desktop/data-backtest/docs/algorithm.md)
- [`docs/database.md`](file:///home/smhvz/Desktop/data-backtest/docs/database.md)
- [`docs/semantics.md`](file:///home/smhvz/Desktop/data-backtest/docs/semantics.md)
