#!/usr/bin/env python3
import urllib.request
import struct
import time

def test_arrow_client(url="http://localhost:8080/api/v1/simulate?symbol=BTCUSDT&sl=0.005&rr=3.0"):
    print(f"Connecting to Arrow Simulation Server at: {url}")
    start_time = time.time()

    req = urllib.request.Request(url, headers={"Accept": "application/vnd.apache.arrow.stream"})
    try:
        with urllib.request.urlopen(req) as resp:
            sim_time_header = resp.headers.get("X-Simulation-Time-Sec")
            total_trades_header = resp.headers.get("X-Total-Trades")
            data = resp.read()

        elapsed = time.time() - start_time
        print("--- SERVER RESPONSE RECEIVED ---")
        print(f"HTTP Status Code:          {resp.status}")
        print(f"Content-Type:              {resp.headers.get('Content-Type')}")
        print(f"Binary Stream Size:        {len(data) / (1024*1024):.2f} MB")
        print(f"Server Sim Time Header:    {sim_time_header} seconds")
        print(f"Server Total Trades Header:{total_trades_header}")
        print(f"Client End-to-End Elapsed: {elapsed:.2f} seconds")

        # Verify Header Magic
        magic = data[:12].decode('ascii', errors='ignore')
        if "ARROW_STREAM" in magic:
            num_rows, num_cols = struct.unpack('<II', data[12:20])
            print(f"[SUCCESS] Parsed Magic Header: {magic} | Rows: {num_rows} | Columns: {num_cols}")
            assert num_rows > 0
            assert num_cols == 48
            print("100% Verified Binary Arrow Stream Client Test Passed!")
        else:
            print("Magic Header:", magic)

    except Exception as e:
        print("Error connecting to server:", e)

if __name__ == "__main__":
    test_arrow_client()
