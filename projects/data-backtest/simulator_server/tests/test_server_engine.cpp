#include "server/data/Candle.hpp"
#include "server/simulation/SimulationEngine.hpp"
#include "server/arrow/ArrowIPCBuilder.hpp"
#include <cassert>
#include <iostream>

using namespace server;

int main() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 101.0, 99.0, 100.0, 10.0);
    candles.push_back(1060, 100.0, 104.0, 99.5, 102.0, 15.0);

    data::Segment seg{0, 0, 1, 1000, 1060};
    validation::ValidationReport valReport;
    valReport.segments = {seg};

    auto cached = std::make_shared<cache::CachedSymbol>();
    cached->symbol = "TEST";
    cached->candles = candles;
    cached->validation_report = valReport;
    cached->segment_trees.resize(1);
    cached->segment_trees[0].build(candles.high.data(), candles.low.data(), 2);

    simulation::SimParams params;
    params.sl_percent = 0.005;
    params.risk_reward_ratio = 3.0;

    auto trades = simulation::SimulationEngine::runInMemorySimulation(cached, params);
    assert(trades.size() == 4);

    std::string arrowStream = arrow::ArrowIPCBuilder::serializeToBinaryIPCStream(trades);
    assert(!arrowStream.empty());

    std::cout << "[PASS] test_server_engine passed successfully!" << std::endl;
    return 0;
}
