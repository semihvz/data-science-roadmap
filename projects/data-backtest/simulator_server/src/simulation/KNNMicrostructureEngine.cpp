#include "server/simulation/KNNMicrostructureEngine.hpp"
#include <cmath>
#include <algorithm>
#include <limits>
#include <iostream>
#include <functional>
#include <random>

namespace server::simulation {

KNNMicrostructureEngine::KNNMicrostructureEngine() {
    initializePatterns();
}

void KNNMicrostructureEngine::initializePatterns() {
    patterns_.clear();

    // Helper to generate smooth normalized trajectory from control points
    auto createPattern = [this](const std::string& name, double open_r, double upper_w, double lower_w,
                                const std::function<double(double)>& pathFunc) {
        KNNPattern p;
        p.name = name;
        p.body_ratio = open_r;
        p.upper_wick_ratio = upper_w;
        p.lower_wick_ratio = lower_w;

        double minVal = 1e9, maxVal = -1e9;
        for (int i = 0; i < 60; ++i) {
            double t = static_cast<double>(i) / 59.0;
            p.trajectory[i] = pathFunc(t);
            minVal = std::min(minVal, p.trajectory[i]);
            maxVal = std::max(maxVal, p.trajectory[i]);
        }
        // Normalize trajectory to exact [0.0, 1.0] range
        double range = (maxVal - minVal > 1e-9) ? (maxVal - minVal) : 1.0;
        for (int i = 0; i < 60; ++i) {
            p.trajectory[i] = (p.trajectory[i] - minVal) / range;
        }
        patterns_.push_back(p);
    };

    // 1. Strong Bullish Marubozu (0.9 body, 0.05 upper, 0.05 lower)
    createPattern("Bullish_Marubozu", 0.9, 0.05, 0.05, [](double t) {
        return 0.05 + 0.9 * t + 0.02 * std::sin(t * 4.0 * M_PI);
    });

    // 2. Strong Bearish Marubozu (-0.9 body, 0.05 upper, 0.05 lower)
    createPattern("Bearish_Marubozu", -0.9, 0.05, 0.05, [](double t) {
        return 0.95 - 0.9 * t + 0.02 * std::sin(t * 4.0 * M_PI);
    });

    // 3. Bullish Reversal Hammer (0.3 body, 0.05 upper, 0.65 lower)
    createPattern("Bullish_Hammer", 0.3, 0.05, 0.65, [](double t) {
        if (t < 0.4) return 0.7 - 0.7 * (t / 0.4); // Drop to Low
        return (t - 0.4) / 0.6;                    // Rally to Close
    });

    // 4. Bearish Shooting Star (-0.3 body, 0.65 upper, 0.05 lower)
    createPattern("Bearish_Shooting_Star", -0.3, 0.65, 0.05, [](double t) {
        if (t < 0.4) return 0.3 + 0.7 * (t / 0.4); // Spike to High
        return 1.0 - 1.0 * ((t - 0.4) / 0.6);      // Crash to Close
    });

    // 5. Classic Doji (0.0 body, 0.5 upper, 0.5 lower)
    createPattern("Classic_Doji", 0.0, 0.5, 0.5, [](double t) {
        return 0.5 + 0.5 * std::sin(t * 2.0 * M_PI);
    });

    // 6. Bullish W-Shape Double Bottom (0.5 body, 0.1 upper, 0.4 lower)
    createPattern("Bullish_W_Shape", 0.5, 0.1, 0.4, [](double t) {
        return 0.5 + 0.4 * std::cos(t * 3.0 * M_PI);
    });

    // 7. Bearish M-Shape Double Top (-0.5 body, 0.4 upper, 0.1 lower)
    createPattern("Bearish_M_Shape", -0.5, 0.4, 0.1, [](double t) {
        return 0.5 - 0.4 * std::cos(t * 3.0 * M_PI);
    });

    // 8. Steady Bullish Trend (0.6 body, 0.2 upper, 0.2 lower)
    createPattern("Bullish_Steady", 0.6, 0.2, 0.2, [](double t) {
        if (t < 0.2) return 0.2 - 0.2 * (t / 0.2); // Initial dip to Low
        if (t < 0.8) return (t - 0.2) / 0.6;       // Steady rise to High
        return 1.0 - 0.2 * ((t - 0.8) / 0.2);      // Small retracement
    });

    // 9. Steady Bearish Trend (-0.6 body, 0.2 upper, 0.2 lower)
    createPattern("Bearish_Steady", -0.6, 0.2, 0.2, [](double t) {
        if (t < 0.2) return 0.8 + 0.2 * (t / 0.2); // Initial pop to High
        if (t < 0.8) return 1.0 - (t - 0.2) / 0.6; // Steady drop to Low
        return 0.0 + 0.2 * ((t - 0.8) / 0.2);      // Small bounce
    });

    // 10. High Volatility Consolidation (0.1 body, 0.45 upper, 0.45 lower)
    createPattern("Volatile_Consolidation", 0.1, 0.45, 0.45, [](double t) {
        return 0.5 + 0.45 * std::sin(t * 6.0 * M_PI) * std::exp(-t * 0.5);
    });
}

size_t KNNMicrostructureEngine::findNearestPatternIndex(double body_ratio, double upper_wick_ratio, double lower_wick_ratio) const {
    size_t bestIdx = 0;
    double minDistance = std::numeric_limits<double>::max();

    for (size_t i = 0; i < patterns_.size(); ++i) {
        const auto& p = patterns_[i];
        // Weighted Euclidean distance in normalized feature space
        double dBody = p.body_ratio - body_ratio;
        double dUpper = p.upper_wick_ratio - upper_wick_ratio;
        double dLower = p.lower_wick_ratio - lower_wick_ratio;

        double dist = (2.0 * dBody * dBody) + (1.0 * dUpper * dUpper) + (1.0 * dLower * dLower);
        if (dist < minDistance) {
            minDistance = dist;
            bestIdx = i;
        }
    }
    return bestIdx;
}

std::array<MicroCandle1S, 60> KNNMicrostructureEngine::generate1SecondSubBars(
    double open, double high, double low, double close, double volume,
    uint32_t seed, double noise_level
) const {
    std::array<MicroCandle1S, 60> subBars;
    double range = high - low;
    if (range < 1e-9) {
        // Flat candle
        for (int i = 0; i < 60; ++i) {
            subBars[i] = {open, open, open, open, volume / 60.0};
        }
        return subBars;
    }

    double body_ratio = (close - open) / range;
    double upper_wick_ratio = (high - std::max(open, close)) / range;
    double lower_wick_ratio = (std::min(open, close) - low) / range;

    size_t patIdx = findNearestPatternIndex(body_ratio, upper_wick_ratio, lower_wick_ratio);
    const auto& pattern = patterns_[patIdx];

    // Rescale pattern trajectory to match exact (Open, High, Low, Close)
    std::array<double, 60> rawPrices;
    for (int i = 0; i < 60; ++i) {
        rawPrices[i] = low + pattern.trajectory[i] * range;
    }

    // Apply stochastic noise variation if seed or noise_level is set
    if (seed > 0 || noise_level > 0.0) {
        std::mt19937 rng(seed > 0 ? seed : 12345);
        double activeNoise = (noise_level > 0.0) ? noise_level : 0.03;
        std::normal_distribution<double> dist(0.0, range * activeNoise);

        for (int i = 1; i < 59; ++i) {
            rawPrices[i] += dist(rng);
            rawPrices[i] = std::clamp(rawPrices[i], low, high);
        }
    }

    // Force exact boundary alignment
    rawPrices[0] = open;
    rawPrices[59] = close;

    double subVol = volume / 60.0;

    for (int i = 0; i < 60; ++i) {
        double pStart = rawPrices[i];
        double pEnd = (i < 59) ? rawPrices[i + 1] : close;

        double cOpen = pStart;
        double cClose = pEnd;
        double cHigh = std::max(cOpen, cClose);
        double cLow = std::min(cOpen, cClose);

        // Sub-second Micro Noise
        double stepNoise = range * 0.01 * std::sin((i + seed) * 0.5);
        cHigh = std::min(high, std::max(cHigh, cHigh + std::abs(stepNoise)));
        cLow = std::max(low, std::min(cLow, cLow - std::abs(stepNoise)));

        subBars[i] = {cOpen, cHigh, cLow, cClose, subVol};
    }

    return subBars;
}

} // namespace server::simulation
