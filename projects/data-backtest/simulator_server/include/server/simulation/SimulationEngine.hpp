#pragma once

#include "server/data/Candle.hpp"
#include "server/cache/SymbolCacheManager.hpp"
#include <vector>
#include <memory>

namespace server::simulation {

struct SimParams {
    double sl_percent = 0.005;
    double risk_reward_ratio = 3.0;
    double tp_percent = 0.015; // sl * RR
    uint32_t threads = 8;
    bool calculate_excursions = true;
    std::string resolution = "1m"; // "1m" or "1s_knn"
};

class SimulationEngine {
public:
    static std::vector<data::TradeResult> runInMemorySimulation(
        const std::shared_ptr<cache::CachedSymbol>& cachedSymbol,
        const SimParams& params
    );
};

} // namespace server::simulation
