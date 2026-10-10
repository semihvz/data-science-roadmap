#pragma once

#include "server/data/Candle.hpp"
#include <vector>
#include <array>
#include <string>
#include <memory>

namespace server::simulation {

struct MicroCandle1S {
    double open;
    double high;
    double low;
    double close;
    double volume;
};

struct KNNPattern {
    std::string name;
    double body_ratio;       // (close - open) / (high - low + eps)
    double upper_wick_ratio; // (high - max(open, close)) / (high - low + eps)
    double lower_wick_ratio; // (min(open, close) - low) / (high - low + eps)
    std::array<double, 60> trajectory; // 60 normalized points in [0.0, 1.0]
};

class KNNMicrostructureEngine {
public:
    KNNMicrostructureEngine();

    // Finds nearest pattern index using Euclidean distance in feature space
    size_t findNearestPatternIndex(double body_ratio, double upper_wick_ratio, double lower_wick_ratio) const;

    // Generates 60 1-second micro-bars for a 1-minute candle with optional stochastic seed and noise
    std::array<MicroCandle1S, 60> generate1SecondSubBars(
        double open, double high, double low, double close, double volume,
        uint32_t seed = 0, double noise_level = 0.0
    ) const;

    const std::vector<KNNPattern>& getPatterns() const { return patterns_; }

private:
    std::vector<KNNPattern> patterns_;
    void initializePatterns();
};

} // namespace server::simulation
