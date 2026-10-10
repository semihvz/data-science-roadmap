#pragma once

#include <cmath>
#include <cstdint>
#include <string>
#include <iomanip>
#include <sstream>

namespace simulator::utils {

enum class PriceModel {
    DOUBLE_PRECISION = 0,
    FIXED_POINT_TICKS = 1
};

class PriceUtils {
public:
    static inline double roundToTick(double price, double tick_size) {
        if (tick_size <= 0.0) return price;
        return std::round(price / tick_size) * tick_size;
    }

    static inline int64_t toTicks(double price, double tick_size) {
        if (tick_size <= 0.0) return static_cast<int64_t>(std::round(price * 1e8));
        return static_cast<int64_t>(std::round(price / tick_size));
    }

    static inline double fromTicks(int64_t ticks, double tick_size) {
        if (tick_size <= 0.0) return static_cast<double>(ticks) / 1e8;
        return static_cast<double>(ticks) * tick_size;
    }

    static inline std::string formatCanonicalDouble(double val) {
        std::ostringstream ss;
        ss << std::setprecision(10) << std::fixed << val;
        std::string s = ss.str();
        // Remove trailing zeros
        s.erase(s.find_last_not_of('0') + 1, std::string::npos);
        if (s.back() == '.') s.pop_back();
        return s;
    }
};

} // namespace simulator::utils
