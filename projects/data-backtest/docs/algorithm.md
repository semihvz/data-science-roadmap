# Search Algorithm & Complexity Analysis

## Algorithm Selection: Segment Tree RMQ

To avoid $O(N^2)$ brute-force iteration over future candles for every entry, the engine constructs a Segment Tree (Range Minimum / Maximum Query) per contiguous dataset segment.

### Search Execution
For entry bar $i$ in segment:
- Search range: $[i+1, \text{segment\_end}]$ (Critical No-Look-Ahead Rule).
- `findFirstHighGe(i+1, end, TP)` returns smallest index $k \ge i+1$ where $\text{high}[k] \ge \text{TP}$ in $O(\log N)$ time.
- `findFirstLowLe(i+1, end, SL)` returns smallest index $k \ge i+1$ where $\text{low}[k] \le \text{SL}$ in $O(\log N)$ time.
- Exit bar $j = \min(tp\_idx, sl\_idx)$. If equal, apply default `SL_FIRST` priority.

### MAE / MFE Range Query
- Range: $[i+1, j]$.
- `queryMaxHigh(i+1, j)` and `queryMinLow(i+1, j)` compute maximum high and minimum low in $O(\log N)$ time without linear re-scan.

## Complexity Proof

| Component | Time Complexity | Memory Complexity |
| :--- | :--- | :--- |
| SoA Data Loading | $O(N)$ | $O(N)$ |
| Segment Tree Build | $O(N)$ | $O(N)$ |
| Trade Simulation (per trade) | $O(\log N)$ | $O(1)$ |
| Total Engine Execution | $O(N \log N)$ | $O(N)$ |
| $O(N^2)$ Brute Force (Reference Engine) | $O(N^2)$ | $O(1)$ |
