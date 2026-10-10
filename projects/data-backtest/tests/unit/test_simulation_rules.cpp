#include "simulator/simulation/SimulationEngine.hpp"
#include "simulator/simulation/ReferenceEngine.hpp"
#include "simulator/indexing/SegmentTree.hpp"
#include <cassert>
#include <iostream>

using namespace simulator;

void testEntryCandleExclusion() {
    // Candle 0 has huge high (150) and low (50), but trade opens at close (100).
    // Candle 0 high/low MUST NOT trigger SL/TP for trade 0!
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 150.0, 50.0, 100.0, 10.0); // Bar 0
    candles.push_back(1060, 100.0, 101.0, 99.5, 100.5, 10.0); // Bar 1: no hit

    data::Segment seg{0, 0, 1, 1000, 1060};
    config::Config cfg;
    cfg.sl_percent = 0.01; // SL = 99.0
    cfg.tp_percent = 0.03; // TP = 103.0

    indexing::SegmentTree segTree;
    segTree.build(candles.high.data(), candles.low.data(), 2);

    auto trLong = simulation::SimulationEngine::simulateSingleEntryOptimized(
        candles, seg, segTree, 0, data::PositionSide::LONG_SIDE, cfg
    );

    // Should NOT be closed on Bar 0!
    assert(trLong.status == data::PositionStatus::OPEN_AT_END_OF_DATA);
    std::cout << "[PASS] testEntryCandleExclusion" << std::endl;
}

void testSameBarSLTPPriority() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 100.5, 99.5, 100.0, 10.0); // Bar 0 entry
    candles.push_back(1060, 100.0, 105.0, 95.0, 100.0, 10.0); // Bar 1 hits BOTH SL (99) and TP (103)

    data::Segment seg{0, 0, 1, 1000, 1060};
    config::Config cfg;
    cfg.sl_percent = 0.01; // SL = 99.0
    cfg.tp_percent = 0.03; // TP = 103.0

    indexing::SegmentTree segTree;
    segTree.build(candles.high.data(), candles.low.data(), 2);

    auto trLong = simulation::SimulationEngine::simulateSingleEntryOptimized(
        candles, seg, segTree, 0, data::PositionSide::LONG_SIDE, cfg
    );

    assert(trLong.status == data::PositionStatus::CLOSED);
    assert(trLong.exit_reason == data::ExitReason::SL_AND_TP_SAME_BAR_SL_PRIORITY);
    assert(trLong.same_bar_sl_tp == 1);
    assert(trLong.exit_price == 99.0);
    std::cout << "[PASS] testSameBarSLTPPriority" << std::endl;
}

void testExactThresholdHit() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 100.5, 99.5, 100.0, 10.0); // Bar 0 entry (100)
    candles.push_back(1060, 100.0, 103.0, 99.5, 101.0, 10.0); // Bar 1 high EXACTLY 103.0 (TP = 103.0)

    data::Segment seg{0, 0, 1, 1000, 1060};
    config::Config cfg;
    cfg.sl_percent = 0.01; // SL = 99.0
    cfg.tp_percent = 0.03; // TP = 103.0

    indexing::SegmentTree segTree;
    segTree.build(candles.high.data(), candles.low.data(), 2);

    auto trLong = simulation::SimulationEngine::simulateSingleEntryOptimized(
        candles, seg, segTree, 0, data::PositionSide::LONG_SIDE, cfg
    );

    assert(trLong.status == data::PositionStatus::CLOSED);
    assert(trLong.exit_reason == data::ExitReason::TP);
    assert(trLong.exit_price == 103.0);
    std::cout << "[PASS] testExactThresholdHit" << std::endl;
}

int main() {
    testEntryCandleExclusion();
    testSameBarSLTPPriority();
    testExactThresholdHit();
    std::cout << "All simulation rules tests passed successfully!" << std::endl;
    return 0;
}
