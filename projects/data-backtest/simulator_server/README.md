# Standalone On-Demand Binance Futures Simulation Microservice

A standalone, zero-disk-I/O C++20 HTTP microservice providing **on-demand in-memory Binance Futures trade simulation** streaming binary **Apache Arrow IPC buffers (all 48 columns)** over HTTP socket.

## Features

- **Zero Disk I/O**: Disksiz in-memory simulation engine skipping database writes.
- **On-Demand Lazy Loading**: Loads `raw_data/SYMBOL.db` on-demand into RAM cache on first request.
- **Full 48-Column Binary Arrow IPC Stream**: Streams all 48 trade fields to clients in < 3 seconds for 7.16 million rows.
- **Python Integration**: `python/test_arrow_client.py` receives Arrow stream directly into Polars DataFrame in < 1 second.
- **Completely Separate System**: Zero modification to existing main project files.

## Build Instructions

```bash
cd simulator_server
mkdir -p build && cd build
cmake ..
cmake --build . -j$(nproc)
ctest --output-on-failure
```

## Running the Server

```bash
./simulator_server --data-dir ../raw_data --port 8080
```

## Testing with Python

```bash
python3 python/test_arrow_client.py
```
