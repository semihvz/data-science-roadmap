#!/usr/bin/env python3
"""
Binance Futures On-Demand Simulation Engine - Python Client
-----------------------------------------------------------
Connects to the C++ Binary Simulation Microservice over HTTP and
loads 7.16+ million simulated trade positions directly into a Polars DataFrame.
"""

import requests
import polars as pl
import numpy as np
import struct
import io
import time

# Polars terminal goruntuleme ayarlari: Terminal genisligi ne olursa olsun tum 48 sutunu eksiksiz goster ve i64/f64 veri tipi satirini gizle
pl.Config.set_tbl_cols(-1)
pl.Config.set_tbl_width_chars(10000)
pl.Config.set_tbl_hide_column_data_types(True)



class BinanceSimulatorClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def get_available_symbols(self) -> list:
        """
        Returns the list of available dataset symbols from the simulation server.
        """
        url = f"{self.base_url}/api/v1/symbols"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass

        # Fallback: scan local raw_data directory if accessible
        import glob, os
        raw_dir = "/home/smhvz/Desktop/data-backtest/raw_data"
        if os.path.exists(raw_dir):
            db_files = glob.glob(os.path.join(raw_dir, "*.db")) + glob.glob(os.path.join(raw_dir, "*.sqlite"))
            return sorted(list(set(os.path.basename(f).replace(".db", "").replace(".sqlite", "") for f in db_files)))

        return []

    # Alias for convenience
    list_symbols = get_available_symbols



    def simulate(
        self,
        symbol: str = "BTCUSDT",
        sl: float = 0.005,
        rr: float = 3.0,
        start_date: str = None,
        end_date: str = None,
        resolution: str = "1m"
    ) -> pl.DataFrame:
        """
        Runs on-demand in-memory C++ simulation for the specified symbol & parameters.
        Args:
            symbol: Dataset symbol name (e.g. 'ETHUSDT', 'BTCUSDT', 'SOLUSDT')
            sl: Stop Loss percentage (e.g. 0.04 for 4%)
            rr: Risk-Reward ratio (e.g. 10.0)
            start_date: Optional start date string 'YYYY-MM-DD'
            end_date: Optional end date string 'YYYY-MM-DD'
            resolution: Simulation resolution ('1m' or '1s_knn' for KNN 1s microstructure pattern matching)
        Returns:
            polars.DataFrame containing ALL 48 trade columns.
        """
        date_str = ""
        if start_date or end_date:
            date_str = f" [{start_date or 'BEGIN'} -> {end_date or 'END'}]"
        url = f"{self.base_url}/api/v1/simulate?symbol={symbol}&sl={sl}&rr={rr}&resolution={resolution}"
        print(f"--> Requesting simulation for {symbol} (SL={sl*100:.2f}%, RR={rr}, Resolution={resolution}){date_str}...")


        t0 = time.time()

        response = requests.get(url, headers={"Accept": "application/vnd.apache.arrow.stream"}, stream=True)
        if response.status_code != 200:
            raise RuntimeError(f"Simulation API error ({response.status_code}): {response.text}")

        sim_time = response.headers.get("X-Simulation-Time-Sec")
        total_trades = response.headers.get("X-Total-Trades")

        data_bytes = response.content
        t_download = time.time() - t0

        magic = data_bytes[:12].decode("ascii", errors="ignore")
        if "ARROW_STREAM" not in magic:
            raise ValueError(f"Invalid stream magic: {magic}")

        num_rows, num_cols = struct.unpack("<II", data_bytes[12:20])
        print(f"<-- Simulation completed in {sim_time}s (Total HTTP Transfer: {t_download:.2f}s)")
        print(f"    Payload: {len(data_bytes)/(1024*1024):.2f} MB binary stream ({num_rows:,} rows, {num_cols} columns).")

        t_parse_start = time.time()
        offset = 20

        # Unpack all 48 binary column buffers with zero-copy NumPy views
        trade_id = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        side = np.frombuffer(data_bytes, dtype=np.int8, count=num_rows, offset=offset); offset += num_rows * 1
        entry_bar_index = np.frombuffer(data_bytes, dtype=np.int32, count=num_rows, offset=offset); offset += num_rows * 4
        exit_bar_index = np.frombuffer(data_bytes, dtype=np.int32, count=num_rows, offset=offset); offset += num_rows * 4
        entry_bar_open_time = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        entry_time = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        exit_bar_open_time = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8

        entry_price = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        exit_price = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        tp_price = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        sl_price = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        sl_percent = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        tp_percent = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        risk_reward_ratio = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        status = np.frombuffer(data_bytes, dtype=np.int8, count=num_rows, offset=offset); offset += num_rows * 1
        exit_reason = np.frombuffer(data_bytes, dtype=np.int8, count=num_rows, offset=offset); offset += num_rows * 1
        bars_held = np.frombuffer(data_bytes, dtype=np.int32, count=num_rows, offset=offset); offset += num_rows * 4

        duration_lower_bound_seconds = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        duration_upper_bound_seconds = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        duration_minutes_approx = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        nominal_r = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        gross_pnl_percent = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        net_pnl_percent = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        gross_pnl_r = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        net_pnl_r = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        same_bar_sl_tp = np.frombuffer(data_bytes, dtype=np.uint8, count=num_rows, offset=offset); offset += num_rows * 1
        intrabar_ambiguous = np.frombuffer(data_bytes, dtype=np.uint8, count=num_rows, offset=offset); offset += num_rows * 1
        gap_through_barrier = np.frombuffer(data_bytes, dtype=np.uint8, count=num_rows, offset=offset); offset += num_rows * 1
        data_segment_id = np.frombuffer(data_bytes, dtype=np.int32, count=num_rows, offset=offset); offset += num_rows * 4

        entry_candle_open = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        entry_candle_high = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        entry_candle_low = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        entry_candle_close = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        entry_candle_volume = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        exit_candle_open = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        exit_candle_high = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        exit_candle_low = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        exit_candle_close = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        exit_candle_volume = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        max_favorable_excursion_pct = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        max_adverse_excursion_pct = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        mfe_r = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        mae_r = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        last_available_price = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        last_available_timestamp = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        unrealized_pnl_pct = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        reserved_1 = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        reserved_2 = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8

        # Construct Polars DataFrame with ALL EXACT 48 COLUMNS in < 0.05s
        df = pl.DataFrame({
            "trade_id": trade_id,
            "side": side,
            "entry_bar_index": entry_bar_index,
            "exit_bar_index": exit_bar_index,
            "entry_bar_open_time": entry_bar_open_time,
            "entry_time": entry_time,
            "exit_bar_open_time": exit_bar_open_time,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "sl_percent": sl_percent,
            "tp_percent": tp_percent,
            "risk_reward_ratio": risk_reward_ratio,
            "status": status,
            "exit_reason": exit_reason,
            "bars_held": bars_held,
            "duration_lower_bound_seconds": duration_lower_bound_seconds,
            "duration_upper_bound_seconds": duration_upper_bound_seconds,
            "duration_minutes_approx": duration_minutes_approx,
            "nominal_r": nominal_r,
            "gross_pnl_percent": gross_pnl_percent,
            "net_pnl_percent": net_pnl_percent,
            "gross_pnl_r": gross_pnl_r,
            "net_pnl_r": net_pnl_r,
            "same_bar_sl_tp": same_bar_sl_tp,
            "intrabar_ambiguous": intrabar_ambiguous,
            "gap_through_barrier": gap_through_barrier,
            "data_segment_id": data_segment_id,
            "entry_candle_open": entry_candle_open,
            "entry_candle_high": entry_candle_high,
            "entry_candle_low": entry_candle_low,
            "entry_candle_close": entry_candle_close,
            "entry_candle_volume": entry_candle_volume,
            "exit_candle_open": exit_candle_open,
            "exit_candle_high": exit_candle_high,
            "exit_candle_low": exit_candle_low,
            "exit_candle_close": exit_candle_close,
            "exit_candle_volume": exit_candle_volume,
            "max_favorable_excursion_pct": max_favorable_excursion_pct,
            "max_adverse_excursion_pct": max_adverse_excursion_pct,
            "mfe_r": mfe_r,
            "mae_r": mae_r,
            "last_available_price": last_available_price,
            "last_available_timestamp": last_available_timestamp,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "reserved_1": reserved_1,
            "reserved_2": reserved_2,
        })

        t_parse = time.time() - t_parse_start
        print(f"    Converted binary stream to Polars DataFrame with ALL {len(df.columns)} COLUMNS in {t_parse:.3f} seconds!")

        if start_date or end_date:
            df = self.filter_by_date_range(df, start_date=start_date, end_date=end_date)
            print(f"    Filtered by date range ({start_date or 'BEGIN'} -> {end_date or 'END'}): {len(df):,} trades remaining.")

        return df

    def get_1s_candles(
        self,
        symbol: str = "BTCUSDT",
        max_candles: int = 1000,
        start_date: str = None,
        end_date: str = None,
        seed: int = 0,
        noise: float = 0.0
    ) -> pl.DataFrame:
        """
        Fetches or reconstructs 1-second synthetic OHLCV candles for the specified symbol.
        Args:
            symbol: Dataset symbol name (e.g. 'ETHUSDT', 'SOLUSDT')
            max_candles: Max 1m candles to expand to 1s (default: 1000 => 60,000 1s candles. Set 0 for all)
            start_date: Optional start date string 'YYYY-MM-DD'
            end_date: Optional end date string 'YYYY-MM-DD'
            seed: Random seed integer for stochastic variation (Monte Carlo sampling)
            noise: Stochastic noise magnitude (e.g. 0.03 for 3% stochastic variation)
        Returns:
            polars.DataFrame containing 1-second OHLCV candles [timestamp, open, high, low, close, volume]
        """
        from datetime import datetime

        url_params = [f"symbol={symbol}"]
        date_str = ""
        if start_date or end_date:
            date_str = f" [{start_date or 'BEGIN'} -> {end_date or 'END'}]"
            if start_date:
                fmt = "%Y-%m-%d %H:%M:%S" if " " in start_date else "%Y-%m-%d"
                start_ts = int(datetime.strptime(start_date, fmt).timestamp())
                url_params.append(f"start_ts={start_ts}")
            if end_date:
                fmt = "%Y-%m-%d %H:%M:%S" if " " in end_date else "%Y-%m-%d"
                if " " not in end_date:
                    end_date_str = end_date + " 23:59:59"
                    fmt = "%Y-%m-%d %H:%M:%S"
                else:
                    end_date_str = end_date
                end_ts = int(datetime.strptime(end_date_str, fmt).timestamp())
                url_params.append(f"end_ts={end_ts}")
        else:
            url_params.append(f"max_candles={max_candles}")

        if seed > 0:
            url_params.append(f"seed={seed}")
        if noise > 0.0:
            url_params.append(f"noise={noise}")

        query_str = "&".join(url_params)
        url = f"{self.base_url}/api/v1/candles1s?{query_str}"
        print(f"--> Requesting 1-second synthetic OHLCV candles for {symbol}{date_str}...")
        t0 = time.time()

        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise RuntimeError(f"1s Candles API error ({response.status_code}): {response.text}")

        data_bytes = response.content
        num_rows, num_cols = struct.unpack("<II", data_bytes[12:20])

        offset = 20
        ts = np.frombuffer(data_bytes, dtype=np.int64, count=num_rows, offset=offset); offset += num_rows * 8
        op = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        hi = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        lo = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        cl = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8
        vo = np.frombuffer(data_bytes, dtype=np.float64, count=num_rows, offset=offset); offset += num_rows * 8

        df = pl.DataFrame({
            "timestamp": ts,
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl,
            "volume": vo
        })

        if start_date or end_date:
            df = self.filter_by_date_range(df, start_date=start_date, end_date=end_date, time_col="timestamp")

        t_elapsed = time.time() - t0
        print(f"    Loaded {len(df):,} 1-second OHLCV candles in {t_elapsed:.3f} seconds!")
        return df

    # Aliases
    get_1s_ohlcv = get_1s_candles
    generate_1s_ohlcv = get_1s_candles



    def get_sequential_trades(
        self,
        df: pl.DataFrame,
        side: int = 1
    ) -> pl.DataFrame:
        """
        Filters non-overlapping sequential trades (where a new trade opens only after 
        the previous trade on the same side has closed).
        Args:
            df: Simulation DataFrame returned by simulate()
            side: 1 for LONG, -1 for SHORT
        Returns:
            Polars DataFrame containing only non-overlapping sequential trades.
        """
        filtered_df = df.filter(pl.col("side") == side)
        if filtered_df.height == 0:
            return filtered_df

        entry_bars = filtered_df["entry_bar_index"].to_numpy()
        exit_bars = filtered_df["exit_bar_index"].to_numpy()
        # Handle open/unresolved positions (-1 exit bar index) by setting exit bar to infinity
        exit_bars = np.where(exit_bars == -1, 999_999_999, exit_bars)

        selected_indices = []
        next_allowed_bar = 0

        for i in range(len(entry_bars)):
            if entry_bars[i] >= next_allowed_bar:
                selected_indices.append(i)
                next_allowed_bar = exit_bars[i] + 1

        return filtered_df[selected_indices]

    def filter_by_date_range(
        self,
        df: pl.DataFrame,
        start_date: str = None,
        end_date: str = None,
        time_col: str = "entry_time"
    ) -> pl.DataFrame:
        """
        Filters DataFrame between start_date and end_date.
        Args:
            df: Polars DataFrame
            start_date: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' string (e.g. '2023-01-01')
            end_date: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' string (e.g. '2023-12-31')
            time_col: Column name containing Unix timestamp in seconds (default: 'entry_time')
        Returns:
            Filtered Polars DataFrame
        """
        from datetime import datetime

        filtered_df = df
        if start_date:
            fmt = "%Y-%m-%d %H:%M:%S" if " " in start_date else "%Y-%m-%d"
            start_ts = int(datetime.strptime(start_date, fmt).timestamp())
            filtered_df = filtered_df.filter(pl.col(time_col) >= start_ts)

        if end_date:
            fmt = "%Y-%m-%d %H:%M:%S" if " " in end_date else "%Y-%m-%d"
            # If date only, include the full end day up to 23:59:59
            if " " not in end_date:
                end_date += " 23:59:59"
                fmt = "%Y-%m-%d %H:%M:%S"
            end_ts = int(datetime.strptime(end_date, fmt).timestamp())
            filtered_df = filtered_df.filter(pl.col(time_col) <= end_ts)

        return filtered_df

    def sync_present_data(
        self,
        symbols: list = None,
        raw_data_dir: str = "/home/smhvz/Desktop/data-backtest/raw_data",
        max_symbols: int = None,
        show_progress: bool = True
    ) -> dict:
        """
        Fetches missing 1-minute klines from Binance Futures REST API for all symbols
        (or a specified list of symbols) from the last recorded timestamp up to present,
        and updates the SQLite databases in raw_data.

        Args:
            symbols: Optional list of symbols (e.g. ['BTCUSDT', 'ETHUSDT']). If None, scans raw_data_dir for all *.db files.
            raw_data_dir: Path to raw_data directory containing SQLite databases.
            max_symbols: Optional int to limit number of processed symbols.
            show_progress: Whether to print progress info.
        
        Returns:
            dict with summary statistics: {'total_symbols': int, 'updated_symbols': int, 'total_klines_added': int}
        """
        import os
        import glob
        import sqlite3
        import time
        from datetime import datetime, timezone

        if symbols is None or len(symbols) == 0:
            if os.path.exists(raw_data_dir):
                db_files = sorted(glob.glob(os.path.join(raw_data_dir, "*.db")) + glob.glob(os.path.join(raw_data_dir, "*.sqlite")))
                symbols = [os.path.basename(f).replace(".db", "").replace(".sqlite", "") for f in db_files]
            else:
                symbols = self.get_available_symbols()

        if max_symbols and len(symbols) > max_symbols:
            symbols = symbols[:max_symbols]

        total_symbols = len(symbols)
        if show_progress:
            print(f"--> Starting data sync for {total_symbols} symbol(s) up to present time...")

        updated_symbols = 0
        total_klines_added = 0
        binance_url = "https://fapi.binance.com/fapi/v1/klines"

        for idx, sym in enumerate(symbols, 1):
            db_path = os.path.join(raw_data_dir, f"{sym}.db")
            if not os.path.exists(db_path):
                db_path = os.path.join(raw_data_dir, f"{sym}.sqlite")
                if not os.path.exists(db_path):
                    if show_progress:
                        print(f"    [{idx}/{total_symbols}] {sym}: File not found, skipping.")
                    continue

            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                cursor = conn.cursor()

                # Get latest open_time from klines table using rowid index for instant 3ms scan
                cursor.execute("SELECT open_time FROM klines ORDER BY rowid DESC LIMIT 1")
                row = cursor.fetchone()
                if not row or not row[0]:
                    if show_progress:
                        print(f"    [{idx}/{total_symbols}] {sym}: No existing kline records found, skipping.")
                    conn.close()
                    continue

                last_open_time_str = row[0]
                dt = datetime.strptime(last_open_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                last_open_ms = int(dt.timestamp() * 1000)
                # Re-fetch last_open_ms as well to repair/overwrite any previously saved incomplete candle
                start_time_ms = last_open_ms

                now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

                # Check if we need updates (if last candle is older than 60s or needs re-checking)
                if start_time_ms >= now_ms - 5000:
                    if show_progress and total_symbols <= 10:
                        print(f"    [{idx}/{total_symbols}] {sym}: Already up-to-date (Last: {last_open_time_str})")
                    conn.close()
                    continue

                sym_klines_added = 0
                current_fetch_start = start_time_ms

                while current_fetch_start < now_ms - 5000:
                    params = {
                        "symbol": sym,
                        "interval": "1m",
                        "startTime": current_fetch_start,
                        "limit": 1500
                    }

                    res = requests.get(binance_url, params=params, timeout=10)
                    if res.status_code == 429:
                        if show_progress:
                            print("    [RATE LIMIT] Waiting 5s...")
                        time.sleep(5)
                        continue
                    elif res.status_code != 200:
                        if show_progress:
                            print(f"    [{idx}/{total_symbols}] {sym}: API HTTP error {res.status_code}")
                        break

                    data = res.json()
                    if not data or not isinstance(data, list):
                        break

                    records_to_insert = []
                    for k in data:
                        o_time_ms = k[0]
                        c_time_ms = k[6]
                        
                        # Tamamlanmamış (halen devam eden canlı) mumu ekleme: Sadece kapanış süresi geçmiş (tamamlanmış) mumları kaydet
                        if c_time_ms > now_ms:
                            continue

                        o_str = datetime.fromtimestamp(o_time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        c_str = datetime.fromtimestamp(c_time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                        records_to_insert.append((
                            sym,
                            "1m",
                            o_str,
                            float(k[1]), # open
                            float(k[2]), # high
                            float(k[3]), # low
                            float(k[4]), # close
                            float(k[5]), # volume
                            c_str,
                            float(k[7]), # quote_volume
                            int(k[8])    # trades_count
                        ))

                    cursor.executemany(
                        "INSERT OR REPLACE INTO klines (symbol, interval, open_time, open, high, low, close, volume, close_time, quote_volume, trades_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        records_to_insert
                    )
                    conn.commit()

                    fetched_count = len(records_to_insert)
                    sym_klines_added += fetched_count
                    
                    last_fetched_ms = data[-1][0]
                    if fetched_count < 1500 or last_fetched_ms >= now_ms - 120000:
                        break

                    current_fetch_start = last_fetched_ms + 60000
                    time.sleep(0.05)

                conn.close()

                if sym_klines_added > 0:
                    updated_symbols += 1
                    total_klines_added += sym_klines_added
                    if show_progress:
                        cursor_end_str = datetime.fromtimestamp(last_fetched_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if 'last_fetched_ms' in locals() else 'present'
                        print(f"    [{idx}/{total_symbols}] {sym}: Added +{sym_klines_added:,} candles ({last_open_time_str} -> {cursor_end_str})")

            except Exception as e:
                if show_progress:
                    print(f"    [{idx}/{total_symbols}] {sym}: Error during sync: {e}")

        summary = {
            "total_symbols": total_symbols,
            "updated_symbols": updated_symbols,
            "total_klines_added": total_klines_added
        }

        if show_progress:
            print(f"<-- Data sync finished! Updated {updated_symbols}/{total_symbols} symbols, added total {total_klines_added:,} new 1m candles.")

        return summary

    # Convenience Aliases
    get_all_present_data = sync_present_data
    fetch_all_present_data = sync_present_data
    sync_all_present_data = sync_present_data

    def get_marked_candles(
        self,
        start_date: str,
        symbols: list = None,
        raw_data_dir: str = "/home/smhvz/Desktop/data-backtest/raw_data",
        max_symbols: int = None,
        show_progress: bool = True
    ) -> dict:
        """
        Fetches all 1-minute klines for USDT pairs starting from start_date up to the last completed candle today.
        If a candle already exists for any timestamp >= start_date, it is REPLACED/OVERWRITTEN with the freshly fetched candle from Binance.

        Args:
            start_date: Starting date string, e.g. '2024-01-01' or '2024-01-01 00:00:00'.
            symbols: Optional list of USDT symbols. If None, scans raw_data_dir for all *USDT.db files.
            raw_data_dir: Path to raw data folder.
            max_symbols: Optional int to limit symbol count.
            show_progress: Print step-by-step progress info.

        Returns:
            dict: Summary dictionary with execution statistics.
        """
        import os
        import glob
        import sqlite3
        import time
        from datetime import datetime, timezone

        fmt = "%Y-%m-%d %H:%M:%S" if " " in start_date else "%Y-%m-%d"
        dt_start = datetime.strptime(start_date, fmt).replace(tzinfo=timezone.utc)
        start_time_ms = int(dt_start.timestamp() * 1000)

        if symbols is None or len(symbols) == 0:
            if os.path.exists(raw_data_dir):
                db_files = sorted(glob.glob(os.path.join(raw_data_dir, "*USDT.db")) + glob.glob(os.path.join(raw_data_dir, "*USDT.sqlite")))
                symbols = [os.path.basename(f).replace(".db", "").replace(".sqlite", "") for f in db_files]
            else:
                symbols = [s for s in self.get_available_symbols() if s.endswith("USDT")]

        if max_symbols and len(symbols) > max_symbols:
            symbols = symbols[:max_symbols]

        total_symbols = len(symbols)
        if show_progress:
            print(f"--> [get_marked_candles] Fetching/updating USDT pairs from {start_date} up to present last closed candle...")

        updated_symbols = 0
        total_klines_fetched = 0
        binance_url = "https://fapi.binance.com/fapi/v1/klines"

        for idx, sym in enumerate(symbols, 1):
            db_path = os.path.join(raw_data_dir, f"{sym}.db")
            if not os.path.exists(db_path):
                db_path = os.path.join(raw_data_dir, f"{sym}.sqlite")
                if not os.path.exists(db_path):
                    if show_progress:
                        print(f"    [{idx}/{total_symbols}] {sym}: File not found, skipping.")
                    continue

            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                cursor = conn.cursor()

                # Ensure table schema exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS klines (
                        symbol TEXT NOT NULL,
                        interval TEXT NOT NULL,
                        open_time TEXT NOT NULL,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume REAL,
                        close_time TEXT,
                        quote_volume REAL,
                        trades_count INTEGER,
                        PRIMARY KEY (symbol, interval, open_time)
                    )
                """)

                now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
                current_fetch_start = start_time_ms
                sym_klines_count = 0

                while current_fetch_start < now_ms - 5000:
                    params = {
                        "symbol": sym,
                        "interval": "1m",
                        "startTime": current_fetch_start,
                        "limit": 1500
                    }

                    res = requests.get(binance_url, params=params, timeout=10)
                    if res.status_code == 429:
                        if show_progress:
                            print("    [RATE LIMIT] Waiting 5s...")
                        time.sleep(5)
                        continue
                    elif res.status_code != 200:
                        if show_progress:
                            print(f"    [{idx}/{total_symbols}] {sym}: API HTTP error {res.status_code}")
                        break

                    data = res.json()
                    if not data or not isinstance(data, list):
                        break

                    records_to_insert = []
                    for k in data:
                        o_time_ms = k[0]
                        c_time_ms = k[6]

                        # Tamamlanmamış canlı mumu atla
                        if c_time_ms > now_ms:
                            continue

                        o_str = datetime.fromtimestamp(o_time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        c_str = datetime.fromtimestamp(c_time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                        records_to_insert.append((
                            sym,
                            "1m",
                            o_str,
                            float(k[1]),
                            float(k[2]),
                            float(k[3]),
                            float(k[4]),
                            float(k[5]),
                            c_str,
                            float(k[7]),
                            int(k[8])
                        ))

                    if records_to_insert:
                        cursor.executemany(
                            "INSERT OR REPLACE INTO klines (symbol, interval, open_time, open, high, low, close, volume, close_time, quote_volume, trades_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            records_to_insert
                        )
                        conn.commit()

                    fetched_count = len(records_to_insert)
                    sym_klines_count += fetched_count

                    last_fetched_ms = data[-1][0]
                    if len(data) < 1500 or last_fetched_ms >= now_ms - 120000:
                        break

                    current_fetch_start = last_fetched_ms + 60000
                    time.sleep(0.05)

                conn.close()

                if sym_klines_count > 0:
                    updated_symbols += 1
                    total_klines_fetched += sym_klines_count
                    if show_progress:
                        print(f"    [{idx}/{total_symbols}] {sym}: Fetched & updated {sym_klines_count:,} candles starting from {start_date}")

            except Exception as e:
                if show_progress:
                    print(f"    [{idx}/{total_symbols}] {sym}: Error: {e}")

        summary = {
            "start_date": start_date,
            "total_symbols": total_symbols,
            "updated_symbols": updated_symbols,
            "total_klines_fetched": total_klines_fetched
        }

        if show_progress:
            print(f"<-- [get_marked_candles] Finished! Processed {updated_symbols}/{total_symbols} USDT symbols, updated {total_klines_fetched:,} candles.")

        return summary

    # Convenience Aliases
    fetch_marked_candles = get_marked_candles
    sync_marked_candles = get_marked_candles







if __name__ == "__main__":
    client = BinanceSimulatorClient()
    df = client.simulate(symbol="BTCUSDT", sl=0.005, rr=3.0)
    
    print(f"\n--- ALL {len(df.columns)} COLUMNS IN DATAFRAME ---")
    print(df.columns)

    print("\n--- SAMPLE TRADES (First 5 Rows) ---")
    print(df.head(5).to_pandas().to_string(index=False))

    print("\n--- STATISTICAL SUMMARY ---")
    closed_df = df.filter(pl.col("status") == 0)
    tp_count = closed_df.filter(pl.col("exit_reason") == 0).height
    sl_count = closed_df.filter(pl.col("exit_reason") == 1).height
    win_rate = (tp_count / closed_df.height) * 100 if closed_df.height > 0 else 0.0
    total_net_r = df["net_pnl_r"].sum()

    print(f"Total Closed Trades: {closed_df.height:,}")
    print(f"Take Profit Count:   {tp_count:,}")
    print(f"Stop Loss Count:     {sl_count:,}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Total Net R Return:  {total_net_r:,.2f} R")
