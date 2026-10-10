-- Schema definition for per-symbol Binance Futures trade simulation database

PRAGMA foreign_keys = ON;

-- 1. Simulation Runs
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    sl_percent REAL NOT NULL,
    risk_reward_ratio REAL NOT NULL,
    tp_percent REAL NOT NULL,
    intrabar_policy TEXT NOT NULL,
    gap_execution_model TEXT NOT NULL,
    price_model TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    source_data_hash TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    compiler_info TEXT NOT NULL,
    build_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL, -- CREATED, VALIDATING, INDEXING, SIMULATING, FINALIZING, COMPLETED, FAILED, INTERRUPTED
    simulation_complete INTEGER NOT NULL DEFAULT 0
);

-- 2. Data Quality & Data Validation Audit
CREATE TABLE IF NOT EXISTS data_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    total_candles INTEGER NOT NULL,
    valid_candles INTEGER NOT NULL,
    invalid_candles INTEGER NOT NULL,
    duplicate_timestamps INTEGER NOT NULL,
    out_of_order_timestamps INTEGER NOT NULL,
    missing_candles INTEGER NOT NULL,
    invalid_ohlc_count INTEGER NOT NULL,
    segment_count INTEGER NOT NULL,
    data_gaps INTEGER NOT NULL,
    data_hash TEXT NOT NULL,
    validated_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

-- 3. Data Segments
CREATE TABLE IF NOT EXISTS segments (
    segment_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    start_bar_index INTEGER NOT NULL,
    end_bar_index INTEGER NOT NULL,
    candle_count INTEGER NOT NULL,
    start_timestamp INTEGER NOT NULL,
    end_timestamp INTEGER NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

-- 4. Simulated Trade Positions
CREATE TABLE IF NOT EXISTS positions (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side INTEGER NOT NULL, -- +1 for LONG, -1 for SHORT
    entry_bar_index INTEGER NOT NULL,
    exit_bar_index INTEGER, -- NULL if open/unresolved
    entry_bar_open_time INTEGER NOT NULL,
    entry_time INTEGER NOT NULL, -- candle close boundary time
    exit_bar_open_time INTEGER,
    entry_price REAL NOT NULL,
    exit_price REAL,
    tp_price REAL NOT NULL,
    sl_price REAL NOT NULL,
    sl_percent REAL NOT NULL,
    tp_percent REAL NOT NULL,
    risk_reward_ratio REAL NOT NULL,
    status INTEGER NOT NULL, -- 0: CLOSED, 1: UNRESOLVED_DUE_TO_GAP, 2: OPEN_AT_END_OF_DATA
    exit_reason INTEGER NOT NULL, -- 0: TP, 1: SL, 2: SL_AND_TP_SAME_BAR_SL_PRIORITY, 3: DATA_GAP, 4: END_OF_DATA
    bars_held INTEGER,
    duration_lower_bound_seconds INTEGER,
    duration_upper_bound_seconds INTEGER,
    duration_minutes_approx REAL,
    nominal_r REAL NOT NULL,
    gross_pnl_percent REAL,
    net_pnl_percent REAL,
    gross_pnl_r REAL,
    net_pnl_r REAL,
    same_bar_sl_tp INTEGER DEFAULT 0,
    intrabar_ambiguous INTEGER DEFAULT 0,
    gap_through_barrier INTEGER DEFAULT 0,
    data_segment_id INTEGER NOT NULL,
    entry_candle_open REAL NOT NULL,
    entry_candle_high REAL NOT NULL,
    entry_candle_low REAL NOT NULL,
    entry_candle_close REAL NOT NULL,
    entry_candle_volume REAL NOT NULL,
    exit_candle_open REAL,
    exit_candle_high REAL,
    exit_candle_low REAL,
    exit_candle_close REAL,
    exit_candle_volume REAL,
    max_favorable_excursion_pct REAL,
    max_adverse_excursion_pct REAL,
    mfe_r REAL,
    mae_r REAL,
    last_available_price REAL,
    last_available_timestamp INTEGER,
    unrealized_pnl_pct REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_unique ON positions(run_id, entry_bar_index, side);

-- 5. Simulation Checkpoints (Atomic crash-recovery)
CREATE TABLE IF NOT EXISTS checkpoints (
    run_id TEXT PRIMARY KEY,
    last_completed_entry_index INTEGER NOT NULL,
    last_committed_entry_index INTEGER NOT NULL,
    last_committed_trade_id INTEGER NOT NULL,
    committed_trade_count INTEGER NOT NULL,
    checkpoint_time TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

-- 6. Simulation Statistics
CREATE TABLE IF NOT EXISTS simulation_statistics (
    run_id TEXT PRIMARY KEY,
    total_candles INTEGER NOT NULL,
    valid_candles INTEGER NOT NULL,
    segment_count INTEGER NOT NULL,
    data_gaps INTEGER NOT NULL,
    total_entries INTEGER NOT NULL,
    total_long_positions INTEGER NOT NULL,
    total_short_positions INTEGER NOT NULL,
    tp_count INTEGER NOT NULL,
    sl_count INTEGER NOT NULL,
    same_bar_sl_tp_count INTEGER NOT NULL,
    end_of_data_count INTEGER NOT NULL,
    data_gap_count INTEGER NOT NULL,
    average_bars_held REAL,
    median_bars_held REAL,
    min_bars_held INTEGER,
    max_bars_held INTEGER,
    tp_rate REAL,
    sl_rate REAL,
    average_nominal_r REAL,
    average_gross_r REAL,
    average_net_r REAL,
    average_mae REAL,
    average_mfe REAL,
    index_build_duration_sec REAL,
    simulation_duration_sec REAL,
    db_write_duration_sec REAL,
    validation_duration_sec REAL,
    total_duration_sec REAL,
    candles_per_sec REAL,
    trades_per_sec REAL,
    sqlite_rows_per_sec REAL,
    sqlite_mb_per_sec REAL,
    peak_rss_mb REAL,
    db_size_bytes INTEGER,
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

-- 7. Key-Value Metadata
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
