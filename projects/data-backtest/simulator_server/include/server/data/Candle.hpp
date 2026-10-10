#pragma once

#include <vector>
#include <cstdint>
#include <string>
#include <memory>

namespace server::data {

struct Candle {
    int64_t timestamp;
    double open;
    double high;
    double low;
    double close;
    double volume;
};

struct SoACandles {
    std::vector<int64_t> timestamps;
    std::vector<double> open;
    std::vector<double> high;
    std::vector<double> low;
    std::vector<double> close;
    std::vector<double> volume;

    size_t size() const { return timestamps.size(); }
    void reserve(size_t n) {
        timestamps.reserve(n);
        open.reserve(n);
        high.reserve(n);
        low.reserve(n);
        close.reserve(n);
        volume.reserve(n);
    }
    void push_back(int64_t ts, double o, double h, double l, double c, double v) {
        timestamps.push_back(ts);
        open.push_back(o);
        high.push_back(h);
        low.push_back(l);
        close.push_back(c);
        volume.push_back(v);
    }
};

struct Segment {
    int32_t segment_id;
    int32_t start_index;
    int32_t end_index;
    int64_t start_timestamp;
    int64_t end_timestamp;

    int32_t length() const { return end_index - start_index + 1; }
};

enum class PositionSide : int8_t {
    LONG_SIDE = 1,
    SHORT_SIDE = -1
};

enum class PositionStatus : int8_t {
    CLOSED = 0,
    UNRESOLVED_DUE_TO_GAP = 1,
    OPEN_AT_END_OF_DATA = 2
};

enum class ExitReason : int8_t {
    TP = 0,
    SL = 1,
    SL_AND_TP_SAME_BAR_SL_PRIORITY = 2,
    DATA_GAP = 3,
    END_OF_DATA = 4
};

// POD struct containing all 48 trade fields
struct TradeResult {
    int64_t trade_id = 0;
    std::string run_id;
    std::string symbol;
    PositionSide side = PositionSide::LONG_SIDE;

    int32_t entry_bar_index = 0;
    int32_t exit_bar_index = -1;

    int64_t entry_bar_open_time = 0;
    int64_t entry_time = 0;
    int64_t exit_bar_open_time = 0;

    double entry_price = 0.0;
    double exit_price = 0.0;
    double tp_price = 0.0;
    double sl_price = 0.0;

    double sl_percent = 0.0;
    double tp_percent = 0.0;
    double risk_reward_ratio = 0.0;

    PositionStatus status = PositionStatus::CLOSED;
    ExitReason exit_reason = ExitReason::TP;

    int32_t bars_held = 0;
    int64_t duration_lower_bound_seconds = 0;
    int64_t duration_upper_bound_seconds = 0;
    double duration_minutes_approx = 0.0;

    double nominal_r = 0.0;
    double gross_pnl_percent = 0.0;
    double net_pnl_percent = 0.0;
    double gross_pnl_r = 0.0;
    double net_pnl_r = 0.0;

    uint8_t same_bar_sl_tp = 0;
    uint8_t intrabar_ambiguous = 0;
    uint8_t gap_through_barrier = 0;

    int32_t data_segment_id = 0;

    double entry_candle_open = 0.0;
    double entry_candle_high = 0.0;
    double entry_candle_low = 0.0;
    double entry_candle_close = 0.0;
    double entry_candle_volume = 0.0;

    double exit_candle_open = 0.0;
    double exit_candle_high = 0.0;
    double exit_candle_low = 0.0;
    double exit_candle_close = 0.0;
    double exit_candle_volume = 0.0;

    double max_favorable_excursion_pct = 0.0;
    double max_adverse_excursion_pct = 0.0;
    double mfe_r = 0.0;
    double mae_r = 0.0;

    double last_available_price = 0.0;
    int64_t last_available_timestamp = 0;
    double unrealized_pnl_pct = 0.0;
};

} // namespace server::data
