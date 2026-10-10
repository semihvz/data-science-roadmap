# Domain Semantics & Simulation Invariants

## Critical Invariants

1. **No-Look-Ahead Rule**:
   - Trade for candle $i$ opens at `close[i]` at the candle close boundary.
   - Candle $i$ `high` and `low` are NEVER used for evaluating SL/TP of trade $i$. First evaluated bar is $i+1$.

2. **Intrabar Ambiguity Priority (`SL_FIRST`)**:
   - If both SL and TP thresholds are crossed in the same 1-minute candle $j$, default policy is `SL_FIRST`.
   - Recorded as `exit_reason = SL_AND_TP_SAME_BAR_SL_PRIORITY`, `same_bar_sl_tp = 1`, `intrabar_ambiguous = 1`.

3. **Bars Held**:
   - Defined as `exit_bar_index - entry_bar_index`. If exit is in bar $i+1$, `bars_held = 1`.

4. **Data Gaps**:
   - Timestamp differences $>60\text{s}$ mark segment boundaries.
   - Trades cannot search past segment boundaries. Unclosed trades at segment boundary are marked `status = UNRESOLVED_DUE_TO_GAP`, `exit_reason = DATA_GAP`.
