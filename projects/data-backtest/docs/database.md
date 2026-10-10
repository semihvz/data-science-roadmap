# Database Schema & Durability Strategy

## SQLite Output File Structure

Each symbol produces an independent SQLite database (`output_dir/SYMBOL.sqlite`). During simulation, output is written to `SYMBOL.sqlite.partial` and atomically renamed to `SYMBOL.sqlite` upon successful run completion and integrity verification.

## Schema Architecture

1. `runs`: High-level run parameters, hashes (`config_hash`, `source_data_hash`), algorithm version, compiler flags, timestamp, and status.
2. `data_quality`: Audit metrics on dataset validation, gap counts, valid vs invalid candles.
3. `segments`: Contiguous candle index ranges separated by timestamp gaps (>60s).
4. `positions`: Trade level detail table containing entry/exit prices, timestamps, OHLC snapshot, bars held, nominal R, gross/net PnL, MFE/MAE excursions.
5. `checkpoints`: Atomic state checkpoints for crash-recovery.
6. `simulation_statistics`: Final execution statistics, duration breakdown, candles/sec, trades/sec, peak RSS.
