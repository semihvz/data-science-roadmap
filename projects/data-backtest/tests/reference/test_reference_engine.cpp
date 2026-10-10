#include "simulator/simulation/ReferenceEngine.hpp"
#include <cassert>
#include <iostream>

using namespace simulator;

int main() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 101.0, 99.0, 100.0, 10.0);
    candles.push_back(1060, 100.0, 104.0, 99.5, 102.0, 15.0);

    data::Segment seg{0, 0, 1, 1000, 1060};
    config::Config cfg;
    cfg.sl_percent = 0.01;
    cfg.tp_percent = 0.03;

    auto results = simulation::ReferenceEngine::runSimulation(candles, {seg}, cfg);
    assert(results.size() == 4); // 2 bars * 2 sides

    std::cout << "ReferenceEngine tests passed successfully!" << std::endl;
    return 0;
}
