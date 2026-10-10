#pragma once

#include "simulator/data/Candle.hpp"
#include <vector>
#include <string>

namespace simulator::validation {

struct ValidationReport {
    size_t total_candles = 0;
    size_t valid_candles = 0;
    size_t invalid_candles = 0;
    size_t duplicate_timestamps = 0;
    size_t out_of_order_timestamps = 0;
    size_t missing_candles = 0;
    size_t invalid_ohlc_count = 0;
    size_t data_gaps = 0;
    std::vector<data::Segment> segments;
    bool is_valid = true;
    std::string error_message;
};

class DataValidator {
public:
    static ValidationReport validateAndSegment(
        const data::SoACandles& candles,
        int64_t timeframeSeconds = 60,
        bool strictMode = true,
        bool repairOrder = false
    );
};

} // namespace simulator::validation
