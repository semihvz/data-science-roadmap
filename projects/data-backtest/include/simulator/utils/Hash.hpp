#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <sstream>
#include <iomanip>

namespace simulator::utils {

class Hash {
public:
    // Simple robust deterministic FNV-1a 64-bit hash formatted as hex string
    static std::string fnv1a64(const std::string& input) {
        uint64_t hash = 14695981039346656037ULL;
        for (char c : input) {
            hash ^= static_cast<uint8_t>(c);
            hash *= 1099511628211ULL;
        }
        std::ostringstream ss;
        ss << std::hex << std::setw(16) << std::setfill('0') << hash;
        return ss.str();
    }

    static std::string fnv1a64Bytes(const void* data, size_t len) {
        const uint8_t* ptr = static_cast<const uint8_t*>(data);
        uint64_t hash = 14695981039346656037ULL;
        for (size_t i = 0; i < len; ++i) {
            hash ^= ptr[i];
            hash *= 1099511628211ULL;
        }
        std::ostringstream ss;
        ss << std::hex << std::setw(16) << std::setfill('0') << hash;
        return ss.str();
    }
};

} // namespace simulator::utils
