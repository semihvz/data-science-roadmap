#pragma once

#include "simulator/data/Candle.hpp"
#include "simulator/config/CLIParser.hpp"
#include "simulator/validation/DataValidator.hpp"
#include "simulator/indexing/SegmentTree.hpp"
#include "simulator/concurrency/BoundedQueue.hpp"
#include "simulator/database/DatabaseManager.hpp"
#include <vector>
#include <memory>
#include <string>

namespace simulator::simulation {

struct SimulationStats {
    uint64_t total_candles = 0;
    uint64_t valid_candles = 0;
    uint64_t segment_count = 0;
    uint64_t data_gaps = 0;
    uint64_t total_entries = 0;
    uint64_t total_long_positions = 0;
    uint64_t total_short_positions = 0;
    uint64_t tp_count = 0;
    uint64_t sl_count = 0;
    uint64_t same_bar_sl_tp_count = 0;
    uint64_t end_of_data_count = 0;
    uint64_t data_gap_count = 0;
    double index_build_duration_sec = 0.0;
    double simulation_duration_sec = 0.0;
    double db_write_duration_sec = 0.0;
    double total_duration_sec = 0.0;
    double peak_rss_mb = 0.0;
};

class SimulationEngine {
public:
    SimulationEngine(const config::Config& cfg);

    SimulationStats run(
        const data::SoACandles& candles,
        const validation::ValidationReport& report,
        database::DatabaseManager& dbManager,
        const std::string& runId
    );

    static data::TradeResult simulateSingleEntryOptimized(
        const data::SoACandles& candles,
        const data::Segment& seg,
        const indexing::SegmentTree& segTree,
        int32_t entryBarIndex,
        data::PositionSide side,
        const config::Config& cfg
    );

private:
    config::Config config_;
};

} // namespace simulator::simulation
