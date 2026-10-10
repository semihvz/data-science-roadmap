#include "simulator/simulation/SimulationEngine.hpp"
#include "simulator/simulation/ExcursionCalculator.hpp"
#include "simulator/utils/SystemInfo.hpp"
#include "simulator/logging/Logger.hpp"
#include <thread>
#include <future>
#include <chrono>
#include <iostream>

namespace simulator::simulation {

SimulationEngine::SimulationEngine(const config::Config& cfg) : config_(cfg) {}

data::TradeResult SimulationEngine::simulateSingleEntryOptimized(
    const data::SoACandles& candles,
    const data::Segment& seg,
    const indexing::SegmentTree& segTree,
    int32_t i,
    data::PositionSide side,
    const config::Config& cfg
) {
    data::TradeResult tr;
    tr.entry_bar_index = i;
    tr.side = side;
    tr.data_segment_id = seg.segment_id;

    tr.entry_bar_open_time = candles.timestamps[i];
    tr.entry_time = candles.timestamps[i] + 60; // 1m close boundary

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

    // Critical Rule: First search candle is i + 1
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
        // Did not hit either barrier within segment
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
            // Same bar exit -> default SL FIRST priority
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
        tr.exit_reason = data::ExitReason::SL_AND_TP_SAME_BAR_SL_PRIORITY;
        tr.same_bar_sl_tp = 1;
        tr.intrabar_ambiguous = 1;
        tr.exit_price = tr.sl_price;
        tr.gross_pnl_percent = -cfg.sl_percent;
        tr.gross_pnl_r = -1.0;
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
        double maxHigh = segTree.queryMaxHigh(searchStart, exitIdx);
        double minLow = segTree.queryMinLow(searchStart, exitIdx);
        ExcursionCalculator::calculateExcursions(tr, maxHigh, minLow);
    }

    return tr;
}

SimulationStats SimulationEngine::run(
    const data::SoACandles& candles,
    const validation::ValidationReport& report,
    database::DatabaseManager& dbManager,
    const std::string& runId
) {
    SimulationStats stats;
    stats.total_candles = report.total_candles;
    stats.valid_candles = report.valid_candles;
    stats.segment_count = report.segments.size();
    stats.data_gaps = report.data_gaps;

    auto totalStart = std::chrono::high_resolution_clock::now();

    // 1. Build Segment Trees
    auto indexStart = std::chrono::high_resolution_clock::now();
    std::vector<indexing::SegmentTree> segTrees(report.segments.size());

    for (size_t segIdx = 0; segIdx < report.segments.size(); ++segIdx) {
        const auto& seg = report.segments[segIdx];
        segTrees[segIdx].build(
            candles.high.data() + seg.start_index,
            candles.low.data() + seg.start_index,
            seg.length()
        );
    }
    auto indexEnd = std::chrono::high_resolution_clock::now();
    stats.index_build_duration_sec = std::chrono::duration<double>(indexEnd - indexStart).count();

    // 2. Multithreaded Simulation Pipeline with Bounded Queue & Single DB Writer
    auto simStart = std::chrono::high_resolution_clock::now();

    size_t queueCapacity = config_.batch_size * 4;
    concurrency::BoundedQueue<std::vector<data::TradeResult>> queue(queueCapacity);

    // Launch Consumer Writer Thread
    auto writerFuture = std::async(std::launch::async, [&]() {
        uint64_t totalWritten = 0;
        std::vector<data::TradeResult> batch;
        while (queue.pop(batch)) {
            dbManager.insertPositionsBatch(batch);
            totalWritten += batch.size();
        }
        return totalWritten;
    });

    // Launch Worker Producer Threads
    uint32_t numThreads = config_.threads;
    std::vector<std::thread> workers;

    for (uint32_t t = 0; t < numThreads; ++t) {
        workers.emplace_back([&, t]() {
            std::vector<data::TradeResult> localBatch;
            localBatch.reserve(config_.batch_size);

            for (size_t s = 0; s < report.segments.size(); ++s) {
                const auto& seg = report.segments[s];
                const auto& segTree = segTrees[s];

                int32_t totalBars = seg.length();
                int32_t barsPerThread = (totalBars + numThreads - 1) / numThreads;
                int32_t startOffset = static_cast<int32_t>(t * barsPerThread);
                int32_t endOffset = std::min(totalBars, static_cast<int32_t>((t + 1) * barsPerThread));

                for (int32_t offset = startOffset; offset < endOffset; ++offset) {
                    int32_t i = seg.start_index + offset;

                    // LONG trade
                    data::TradeResult longTr = simulateSingleEntryOptimized(candles, seg, segTree, i, data::PositionSide::LONG_SIDE, config_);
                    localBatch.push_back(longTr);

                    // SHORT trade
                    data::TradeResult shortTr = simulateSingleEntryOptimized(candles, seg, segTree, i, data::PositionSide::SHORT_SIDE, config_);
                    localBatch.push_back(shortTr);

                    if (localBatch.size() >= config_.batch_size) {
                        queue.push(std::move(localBatch));
                        localBatch.clear();
                        localBatch.reserve(config_.batch_size);
                    }
                }
            }

            if (!localBatch.empty()) {
                queue.push(std::move(localBatch));
            }
        });
    }

    // Join workers and close queue
    for (auto& w : workers) {
        if (w.joinable()) w.join();
    }
    queue.close();

    uint64_t totalTradesWritten = writerFuture.get();
    auto simEnd = std::chrono::high_resolution_clock::now();
    stats.simulation_duration_sec = std::chrono::duration<double>(simEnd - simStart).count();

    auto totalEnd = std::chrono::high_resolution_clock::now();
    stats.total_duration_sec = std::chrono::duration<double>(totalEnd - totalStart).count();
    stats.peak_rss_mb = utils::SystemInfo::getPeakRSSMB();
    stats.total_entries = candles.size();
    stats.total_long_positions = candles.size();
    stats.total_short_positions = candles.size();

    return stats;
}

} // namespace simulator::simulation
