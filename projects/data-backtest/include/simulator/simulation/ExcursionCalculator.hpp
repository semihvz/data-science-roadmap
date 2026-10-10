#pragma once

#include "simulator/data/Candle.hpp"

namespace simulator::simulation {

class ExcursionCalculator {
public:
    static inline void calculateExcursions(
        data::TradeResult& trade,
        double maxHighInRange,
        double minLowInRange
    ) {
        if (trade.side == data::PositionSide::LONG_SIDE) {
            double mfeAbs = maxHighInRange - trade.entry_price;
            double maeAbs = trade.entry_price - minLowInRange;

            trade.max_favorable_excursion_pct = mfeAbs / trade.entry_price;
            trade.max_adverse_excursion_pct = maeAbs / trade.entry_price;

            double stopDistance = trade.entry_price * trade.sl_percent;
            if (stopDistance > 0.0) {
                trade.mfe_r = mfeAbs / stopDistance;
                trade.mae_r = maeAbs / stopDistance;
            }
        } else {
            double mfeAbs = trade.entry_price - minLowInRange;
            double maeAbs = maxHighInRange - trade.entry_price;

            trade.max_favorable_excursion_pct = mfeAbs / trade.entry_price;
            trade.max_adverse_excursion_pct = maeAbs / trade.entry_price;

            double stopDistance = trade.entry_price * trade.sl_percent;
            if (stopDistance > 0.0) {
                trade.mfe_r = mfeAbs / stopDistance;
                trade.mae_r = maeAbs / stopDistance;
            }
        }
    }
};

} // namespace simulator::simulation
