#include "simulator/simulation/ReferenceEngine.hpp"
#include "simulator/simulation/ExcursionCalculator.hpp"
#include <algorithm>
#include <limits>

namespace simulator::simulation {

data::TradeResult ReferenceEngine::simulateSingleEntry(
    const data::SoACandles& candles,
    const data::Segment& seg,
    int32_t i,
    data::PositionSide side,
    const config::Config& cfg
) {
    data::TradeResult tr;
    tr.entry_bar_index = i;
    tr.side = side;
    tr.data_segment_id = seg.segment_id;

    tr.entry_bar_open_time = candles.timestamps[i];
    // 1m candle close time boundary = open_time + 60 seconds
    tr.entry_time = candles.timestamps[i] + 60;

    tr.entry_price = candles.close[i];
    tr.sl_percent = cfg.sl_percent;
    tr.tp_percent = cfg.tp_percent;
    tr.risk_reward_ratio = cfg.risk_reward_ratio;
    tr.nominal_r = 1.0;

    tr.entry_candle_open = candles.open[i];
    tr.entry_candle_high = candles.high[i];
    tr.entry_candle_low = candles.low[i];
    tr.entry_candle_close = candles.close[i];
    tr.entry_candle_volume = candles.volume[i];

    if (side == data::PositionSide::LONG_SIDE) {
        tr.sl_price = tr.entry_price * (1.0 - cfg.sl_percent);
        tr.tp_price = tr.entry_price * (1.0 + cfg.tp_percent);
    } else {
        tr.sl_price = tr.entry_price * (1.0 + cfg.sl_percent);
        tr.tp_price = tr.entry_price * (1.0 - cfg.tp_percent);
    }

    // Critical Entry Rule: candle i high/low CANNOT be used for SL/TP! First checked candle is i + 1.
    int32_t searchStart = i + 1;
    int32_t searchEnd = seg.end_index;

    if (searchStart > searchEnd) {
        // Unresolved because segment ended immediately after entry
        tr.status = data::PositionStatus::OPEN_AT_END_OF_DATA;
        tr.exit_reason = data::ExitReason::END_OF_DATA;
        tr.last_available_price = candles.close[seg.end_index];
        tr.last_available_timestamp = candles.timestamps[seg.end_index];
        if (side == data::PositionSide::LONG_SIDE) {
            tr.unrealized_pnl_pct = (tr.last_available_price - tr.entry_price) / tr.entry_price;
        } else {
            tr.unrealized_pnl_pct = (tr.entry_price - tr.last_available_price) / tr.entry_price;
        }
        return tr;
    }

    bool closed = false;
    double maxHigh = -std::numeric_limits<double>::infinity();
    double minLow = std::numeric_limits<double>::infinity();

    for (int32_t j = searchStart; j <= searchEnd; ++j) {
        double barHigh = candles.high[j];
        double barLow = candles.low[j];

        if (barHigh > maxHigh) maxHigh = barHigh;
        if (barLow < minLow) minLow = barLow;

        bool tpHit = false;
        bool slHit = false;

        if (side == data::PositionSide::LONG_SIDE) {
            if (barHigh >= tr.tp_price) tpHit = true;
            if (barLow <= tr.sl_price) slHit = true;
        } else {
            if (barLow <= tr.tp_price) tpHit = true;
            if (barHigh >= tr.sl_price) slHit = true;
        }

        if (tpHit || slHit) {
            tr.status = data::PositionStatus::CLOSED;
            tr.exit_bar_index = j;
            tr.exit_bar_open_time = candles.timestamps[j];
            tr.bars_held = j - i;
            tr.duration_lower_bound_seconds = candles.timestamps[j] - tr.entry_time;
            tr.duration_upper_bound_seconds = (candles.timestamps[j] + 60) - tr.entry_time;
            tr.duration_minutes_approx = tr.bars_held;

            tr.exit_candle_open = candles.open[j];
            tr.exit_candle_high = candles.high[j];
            tr.exit_candle_low = candles.low[j];
            tr.exit_candle_close = candles.close[j];
            tr.exit_candle_volume = candles.volume[j];

            if (tpHit && slHit) {
                // Same bar SL & TP -> SL FIRST priority by default
                tr.exit_reason = data::ExitReason::SL_AND_TP_SAME_BAR_SL_PRIORITY;
                tr.same_bar_sl_tp = 1;
                tr.intrabar_ambiguous = 1;
                tr.exit_price = tr.sl_price;
                if (side == data::PositionSide::LONG_SIDE) {
                    tr.gross_pnl_percent = -cfg.sl_percent;
                    tr.gross_pnl_r = -1.0;
                } else {
                    tr.gross_pnl_percent = -cfg.sl_percent;
                    tr.gross_pnl_r = -1.0;
                }
            } else if (tpHit) {
                tr.exit_reason = data::ExitReason::TP;
                tr.exit_price = tr.tp_price;
                tr.gross_pnl_percent = cfg.tp_percent;
                tr.gross_pnl_r = cfg.risk_reward_ratio;
            } else {
                tr.exit_reason = data::ExitReason::SL;
                tr.exit_price = tr.sl_price;
                tr.gross_pnl_percent = -cfg.sl_percent;
                tr.gross_pnl_r = -1.0;
            }

            tr.net_pnl_percent = tr.gross_pnl_percent;
            tr.net_pnl_r = tr.gross_pnl_r;

            if (cfg.calculate_excursions) {
                ExcursionCalculator::calculateExcursions(tr, maxHigh, minLow);
            }

            closed = true;
            break;
        }
    }

    if (!closed) {
        // Trade reached end of segment without hitting SL/TP
        if (seg.end_index == static_cast<int32_t>(candles.size() - 1)) {
            tr.status = data::PositionStatus::OPEN_AT_END_OF_DATA;
            tr.exit_reason = data::ExitReason::END_OF_DATA;
        } else {
            tr.status = data::PositionStatus::UNRESOLVED_DUE_TO_GAP;
            tr.exit_reason = data::ExitReason::DATA_GAP;
        }
        tr.last_available_price = candles.close[seg.end_index];
        tr.last_available_timestamp = candles.timestamps[seg.end_index];
        if (side == data::PositionSide::LONG_SIDE) {
            tr.unrealized_pnl_pct = (tr.last_available_price - tr.entry_price) / tr.entry_price;
        } else {
            tr.unrealized_pnl_pct = (tr.entry_price - tr.last_available_price) / tr.entry_price;
        }
    }

    return tr;
}

std::vector<data::TradeResult> ReferenceEngine::runSimulation(
    const data::SoACandles& candles,
    const std::vector<data::Segment>& segments,
    const config::Config& cfg
) {
    std::vector<data::TradeResult> results;
    results.reserve(candles.size() * 2);

    for (const auto& seg : segments) {
        for (int32_t i = seg.start_index; i <= seg.end_index; ++i) {
            // Generate 1 LONG and 1 SHORT trade at each valid bar close
            results.push_back(simulateSingleEntry(candles, seg, i, data::PositionSide::LONG_SIDE, cfg));
            results.push_back(simulateSingleEntry(candles, seg, i, data::PositionSide::SHORT_SIDE, cfg));
        }
    }

    return results;
}

} // namespace simulator::simulation
