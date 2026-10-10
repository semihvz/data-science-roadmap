#include "simulator/validation/DataValidator.hpp"
#include <cmath>
#include <sstream>

namespace simulator::validation {

ValidationReport DataValidator::validateAndSegment(
    const data::SoACandles& candles,
    int64_t timeframeSeconds,
    bool strictMode,
    bool repairOrder
) {
    ValidationReport report;
    report.total_candles = candles.size();

    if (candles.size() == 0) {
        report.is_valid = false;
        report.error_message = "Dataset is empty";
        return report;
    }

    int32_t segmentStart = 0;
    int32_t currentSegmentId = 0;

    for (size_t i = 0; i < candles.size(); ++i) {
        int64_t ts = candles.timestamps[i];
        double o = candles.open[i];
        double h = candles.high[i];
        double l = candles.low[i];
        double c = candles.close[i];
        double v = candles.volume[i];

        bool candleValid = true;

        // Check NaN / Infinity
        if (!std::isfinite(o) || !std::isfinite(h) || !std::isfinite(l) || !std::isfinite(c) || !std::isfinite(v)) {
            report.invalid_ohlc_count++;
            candleValid = false;
        }

        // Check OHLC bounds & positivity
        if (o <= 0.0 || h <= 0.0 || l <= 0.0 || c <= 0.0 || v < 0.0) {
            report.invalid_ohlc_count++;
            candleValid = false;
        }

        if (h < l || h < o || h < c || l > o || l > c) {
            report.invalid_ohlc_count++;
            candleValid = false;
        }

        if (i > 0) {
            int64_t prevTs = candles.timestamps[i - 1];
            if (ts == prevTs) {
                report.duplicate_timestamps++;
                candleValid = false;
            } else if (ts < prevTs) {
                report.out_of_order_timestamps++;
                candleValid = false;
            } else {
                int64_t gap = ts - prevTs;
                if (gap > timeframeSeconds) {
                    report.data_gaps++;
                    // Close previous segment
                    data::Segment seg;
                    seg.segment_id = currentSegmentId++;
                    seg.start_index = segmentStart;
                    seg.end_index = static_cast<int32_t>(i - 1);
                    seg.start_timestamp = candles.timestamps[segmentStart];
                    seg.end_timestamp = candles.timestamps[i - 1];
                    report.segments.push_back(seg);

                    segmentStart = static_cast<int32_t>(i);
                }
            }
        }

        if (candleValid) {
            report.valid_candles++;
        } else {
            report.invalid_candles++;
            if (strictMode) {
                report.is_valid = false;
                std::ostringstream ss;
                ss << "Data validation failed at index " << i << " ts=" << ts;
                report.error_message = ss.str();
                return report;
            }
        }
    }

    // Add final segment
    if (segmentStart < static_cast<int32_t>(candles.size())) {
        data::Segment seg;
        seg.segment_id = currentSegmentId++;
        seg.start_index = segmentStart;
        seg.end_index = static_cast<int32_t>(candles.size() - 1);
        seg.start_timestamp = candles.timestamps[segmentStart];
        seg.end_timestamp = candles.timestamps[candles.size() - 1];
        report.segments.push_back(seg);
    }

    return report;
}

} // namespace simulator::validation
