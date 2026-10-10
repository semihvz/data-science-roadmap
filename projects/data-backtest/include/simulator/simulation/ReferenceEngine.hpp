#pragma once

#include "simulator/data/Candle.hpp"
#include "simulator/config/CLIParser.hpp"
#include "simulator/validation/DataValidator.hpp"
#include <vector>

namespace simulator::simulation {

class ReferenceEngine {
public:
    static std::vector<data::TradeResult> runSimulation(
        const data::SoACandles& candles,
        const std::vector<data::Segment>& segments,
        const config::Config& cfg
    );

private:
    static data::TradeResult simulateSingleEntry(
        const data::SoACandles& candles,
        const data::Segment& seg,
        int32_t entryBarIndex,
        data::PositionSide side,
        const config::Config& cfg
    );
};

} // namespace simulator::simulation
