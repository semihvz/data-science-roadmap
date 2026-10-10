#include "simulator/simulation/SimulationEngine.hpp"
#include "simulator/simulation/ReferenceEngine.hpp"
#include "simulator/indexing/SegmentTree.hpp"
#include <cassert>
#include <iostream>
#include <random>

using namespace simulator;

data::SoACandles generateRandomCandles(uint32_t seed, size_t count) {
    std::mt19937 gen(seed);
    std::uniform_real_distribution<double> retDist(-0.005, 0.005);
    std::uniform_real_distribution<double> spanDist(0.001, 0.01);

    data::SoACandles candles;
    double currentClose = 100.0;
    int64_t currentTs = 1600000000;

    for (size_t i = 0; i < count; ++i) {
        double open = currentClose;
        double change = currentClose * retDist(gen);
        double close = open + change;
        double span = currentClose * spanDist(gen);

        double high = std::max(open, close) + span * 0.5;
        double low = std::min(open, close) - span * 0.5;
        double volume = 10.0 + std::abs(change) * 100.0;

        candles.push_back(currentTs, open, high, low, close, volume);
        currentClose = close;
        currentTs += 60;
    }
    return candles;
}

void testRandomSeed(uint32_t seed, size_t candleCount) {
    data::SoACandles candles = generateRandomCandles(seed, candleCount);
    data::Segment seg{0, 0, static_cast<int32_t>(candleCount - 1), candles.timestamps.front(), candles.timestamps.back()};

    config::Config cfg;
    cfg.sl_percent = 0.008;
    cfg.risk_reward_ratio = 2.5;
    cfg.tp_percent = cfg.sl_percent * cfg.risk_reward_ratio;

    // 1. Reference Engine Run
    auto refResults = simulation::ReferenceEngine::runSimulation(candles, {seg}, cfg);

    // 2. Optimized Engine Run
    indexing::SegmentTree segTree;
    segTree.build(candles.high.data(), candles.low.data(), static_cast<int32_t>(candleCount));

    std::vector<data::TradeResult> optResults;
    optResults.reserve(candleCount * 2);

    for (int32_t i = 0; i < static_cast<int32_t>(candleCount); ++i) {
        optResults.push_back(simulation::SimulationEngine::simulateSingleEntryOptimized(candles, seg, segTree, i, data::PositionSide::LONG_SIDE, cfg));
        optResults.push_back(simulation::SimulationEngine::simulateSingleEntryOptimized(candles, seg, segTree, i, data::PositionSide::SHORT_SIDE, cfg));
    }

    assert(refResults.size() == optResults.size());

    for (size_t k = 0; k < refResults.size(); ++k) {
        const auto& r = refResults[k];
        const auto& o = optResults[k];

        if (r.status != o.status || r.exit_reason != o.exit_reason || r.exit_bar_index != o.exit_bar_index) {
            std::cerr << "Mismatch found at seed " << seed << " trade index " << k << std::endl;
            std::cerr << "Ref: status=" << (int)r.status << " exitReason=" << (int)r.exit_reason << " exitBar=" << r.exit_bar_index << std::endl;
            std::cerr << "Opt: status=" << (int)o.status << " exitReason=" << (int)o.exit_reason << " exitBar=" << o.exit_bar_index << std::endl;
            assert(false);
        }
    }
}

int main() {
    std::cout << "Running randomized property tests across 50 seeds..." << std::endl;
    for (uint32_t s = 1; s <= 50; ++s) {
        testRandomSeed(s, 200);
    }
    std::cout << "[PASS] All 50 randomized equivalence seeds passed 100% matching results!" << std::endl;
    return 0;
}
