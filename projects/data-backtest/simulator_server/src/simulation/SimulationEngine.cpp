#include "server/simulation/SimulationEngine.hpp"
#include "server/simulation/KNNMicrostructureEngine.hpp"
#include <thread>
#include <future>
#include <algorithm>
#include <cmath>
#include <limits>

namespace server::simulation {

static data::TradeResult simulateSingleEntry(
    const data::SoACandles& candles,
    const data::Segment& seg,
    const indexing::SegmentTree& segTree,
    int32_t i,
    data::PositionSide side,
    const SimParams& params
) {
    data::TradeResult tr;
    tr.entry_bar_index = i;
    tr.side = side;
    tr.data_segment_id = seg.segment_id;

    tr.entry_bar_open_time = candles.timestamps[i];
    tr.entry_time = candles.timestamps[i] + 60; // 1m close boundary

    tr.entry_price = candles.close[i];
    tr.sl_percent = params.sl_percent;
    tr.tp_percent = params.tp_percent;
    tr.risk_reward_ratio = params.risk_reward_ratio;
    tr.nominal_r = 1.0;

    tr.entry_candle_open = candles.open[i];
    tr.entry_candle_high = candles.high[i];
    tr.entry_candle_low = candles.low[i];
    tr.entry_candle_close = candles.close[i];
    tr.entry_candle_volume = candles.volume[i];

    if (side == data::PositionSide::LONG_SIDE) {
        tr.sl_price = tr.entry_price * (1.0 - params.sl_percent);
        tr.tp_price = tr.entry_price * (1.0 + params.tp_percent);
    } else {
        tr.sl_price = tr.entry_price * (1.0 + params.sl_percent);
        tr.tp_price = tr.entry_price * (1.0 - params.tp_percent);
    }

    int32_t searchStart = i + 1;
    int32_t searchEnd = seg.end_index;

    if (searchStart > searchEnd) {
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

    int32_t tpIdx = -1;
    int32_t slIdx = -1;

    if (side == data::PositionSide::LONG_SIDE) {
        tpIdx = segTree.findFirstHighGe(searchStart, searchEnd, tr.tp_price);
        slIdx = segTree.findFirstLowLe(searchStart, searchEnd, tr.sl_price);
    } else {
        tpIdx = segTree.findFirstLowLe(searchStart, searchEnd, tr.tp_price);
        slIdx = segTree.findFirstHighGe(searchStart, searchEnd, tr.sl_price);
    }

    if (tpIdx == -1 && slIdx == -1) {
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
        return tr;
    }

    int32_t exitIdx = -1;
    bool tpHit = false;
    bool slHit = false;

    if (tpIdx != -1 && slIdx != -1) {
        if (tpIdx < slIdx) {
            exitIdx = tpIdx;
            tpHit = true;
        } else if (slIdx < tpIdx) {
            exitIdx = slIdx;
            slHit = true;
        } else {
            exitIdx = slIdx;
            tpHit = true;
            slHit = true;
        }
    } else if (tpIdx != -1) {
        exitIdx = tpIdx;
        tpHit = true;
    } else {
        exitIdx = slIdx;
        slHit = true;
    }

    tr.status = data::PositionStatus::CLOSED;
    tr.exit_bar_index = exitIdx;
    tr.exit_bar_open_time = candles.timestamps[exitIdx];
    tr.bars_held = exitIdx - i;
    tr.duration_lower_bound_seconds = candles.timestamps[exitIdx] - tr.entry_time;
    tr.duration_upper_bound_seconds = (candles.timestamps[exitIdx] + 60) - tr.entry_time;
    tr.duration_minutes_approx = tr.bars_held;

    tr.exit_candle_open = candles.open[exitIdx];
    tr.exit_candle_high = candles.high[exitIdx];
    tr.exit_candle_low = candles.low[exitIdx];
    tr.exit_candle_close = candles.close[exitIdx];
    tr.exit_candle_volume = candles.volume[exitIdx];

    if (tpHit && slHit) {
        // Resolve same-bar SL/TP ambiguity using 1-second KNN Microstructure Engine
        static KNNMicrostructureEngine knnEngine;
        auto subBars = knnEngine.generate1SecondSubBars(
            candles.open[exitIdx], candles.high[exitIdx], candles.low[exitIdx], candles.close[exitIdx], candles.volume[exitIdx]
        );

        int16_t tpSec = -1;
        int16_t slSec = -1;

        for (int s = 0; s < 60; ++s) {
            int16_t sec = static_cast<int16_t>(s);
            if (side == data::PositionSide::LONG_SIDE) {
                if (tpSec == -1 && subBars[s].high >= tr.tp_price) tpSec = sec;
                if (slSec == -1 && subBars[s].low <= tr.sl_price) slSec = sec;
            } else {
                if (tpSec == -1 && subBars[s].low <= tr.tp_price) tpSec = sec;
                if (slSec == -1 && subBars[s].high >= tr.sl_price) slSec = sec;
            }
        }

        if (tpSec != -1 && (slSec == -1 || tpSec < slSec)) {
            tr.exit_reason = data::ExitReason::TP;
            tr.exit_price = tr.tp_price;
            tr.gross_pnl_percent = params.tp_percent;
            tr.gross_pnl_r = params.risk_reward_ratio;
            tr.same_bar_sl_tp = 0;
            tr.intrabar_ambiguous = 0;
            tr.duration_lower_bound_seconds += tpSec;
            tr.duration_upper_bound_seconds = tr.duration_lower_bound_seconds;
        } else {
            tr.exit_reason = data::ExitReason::SL_AND_TP_SAME_BAR_SL_PRIORITY;
            tr.same_bar_sl_tp = 1;
            tr.intrabar_ambiguous = 0;
            tr.exit_price = tr.sl_price;
            tr.gross_pnl_percent = -params.sl_percent;
            tr.gross_pnl_r = -1.0;
            if (slSec != -1) {
                tr.duration_lower_bound_seconds += slSec;
                tr.duration_upper_bound_seconds = tr.duration_lower_bound_seconds;
            }
        }
    } else if (tpHit) {
        tr.exit_reason = data::ExitReason::TP;
        tr.exit_price = tr.tp_price;
        tr.gross_pnl_percent = params.tp_percent;
        tr.gross_pnl_r = params.risk_reward_ratio;
    } else {
        tr.exit_reason = data::ExitReason::SL;
        tr.exit_price = tr.sl_price;
        tr.gross_pnl_percent = -params.sl_percent;
        tr.gross_pnl_r = -1.0;
    }

    tr.net_pnl_percent = tr.gross_pnl_percent;
    tr.net_pnl_r = tr.gross_pnl_r;

    if (params.calculate_excursions) {
        double maxHigh = segTree.queryMaxHigh(searchStart, exitIdx);
        double minLow = segTree.queryMinLow(searchStart, exitIdx);

        if (side == data::PositionSide::LONG_SIDE) {
            double mfeAbs = maxHigh - tr.entry_price;
            double maeAbs = tr.entry_price - minLow;
            tr.max_favorable_excursion_pct = mfeAbs / tr.entry_price;
            tr.max_adverse_excursion_pct = maeAbs / tr.entry_price;
            double stopDist = tr.entry_price * tr.sl_percent;
            if (stopDist > 0.0) {
                tr.mfe_r = mfeAbs / stopDist;
                tr.mae_r = maeAbs / stopDist;
            }
        } else {
            double mfeAbs = tr.entry_price - minLow;
            double maeAbs = maxHigh - tr.entry_price;
            tr.max_favorable_excursion_pct = mfeAbs / tr.entry_price;
            tr.max_adverse_excursion_pct = maeAbs / tr.entry_price;
            double stopDist = tr.entry_price * tr.sl_percent;
            if (stopDist > 0.0) {
                tr.mfe_r = mfeAbs / stopDist;
                tr.mae_r = maeAbs / stopDist;
            }
        }
    }

    return tr;
}

std::vector<data::TradeResult> SimulationEngine::runInMemorySimulation(
    const std::shared_ptr<cache::CachedSymbol>& cached,
    const SimParams& params
) {
    size_t totalCandles = cached->candles.size();
    std::vector<data::TradeResult> results(totalCandles * 2);

    uint32_t numThreads = params.threads;
    if (numThreads < 1) numThreads = 4;

    const auto& segments = cached->validation_report.segments;
    const auto& segTrees = cached->segment_trees;
    const auto& candles = cached->candles;

    std::vector<std::thread> workers;

    for (uint32_t t = 0; t < numThreads; ++t) {
        workers.emplace_back([&, t]() {
            for (size_t s = 0; s < segments.size(); ++s) {
                const auto& seg = segments[s];
                const auto& segTree = segTrees[s];

                int32_t totalBars = seg.length();
                int32_t barsPerThread = (totalBars + numThreads - 1) / numThreads;
                int32_t startOffset = static_cast<int32_t>(t * barsPerThread);
                int32_t endOffset = std::min(totalBars, static_cast<int32_t>((t + 1) * barsPerThread));

                for (int32_t offset = startOffset; offset < endOffset; ++offset) {
                    int32_t i = seg.start_index + offset;
                    size_t outIdx = static_cast<size_t>(i) * 2;

                    results[outIdx]     = simulateSingleEntry(candles, seg, segTree, i, data::PositionSide::LONG_SIDE, params);
                    results[outIdx].trade_id = static_cast<int64_t>(outIdx + 1);

                    results[outIdx + 1] = simulateSingleEntry(candles, seg, segTree, i, data::PositionSide::SHORT_SIDE, params);
                    results[outIdx + 1].trade_id = static_cast<int64_t>(outIdx + 2);
                }
            }
        });
    }

    for (auto& w : workers) {
        if (w.joinable()) w.join();
    }

    return results;
}

} // namespace server::simulation
