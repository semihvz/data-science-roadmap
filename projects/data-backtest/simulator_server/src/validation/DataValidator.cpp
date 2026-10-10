#include "server/validation/DataValidator.hpp"
#include <cmath>

namespace server::validation {

ValidationReport DataValidator::validateAndSegment(const data::SoACandles& candles, int64_t timeframeSeconds) {
    ValidationReport report;
    report.total_candles = candles.size();

    if (candles.size() == 0) {
        report.is_valid = false;
        report.error_message = "Empty dataset";
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

        bool candleValid = std::isfinite(o) && std::isfinite(h) && std::isfinite(l) && std::isfinite(c) && std::isfinite(v);
        if (candleValid && (o <= 0.0 || h <= 0.0 || l <= 0.0 || c <= 0.0 || v < 0.0)) candleValid = false;
        if (candleValid && (h < l || h < o || h < c || l > o || l > c)) candleValid = false;

        if (i > 0) {
            int64_t prevTs = candles.timestamps[i - 1];
            if (ts - prevTs > timeframeSeconds) {
                report.data_gaps++;
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

        if (candleValid) report.valid_candles++;
        else report.invalid_candles++;
    }

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

} // namespace server::validation
