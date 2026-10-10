#pragma once

#include "server/data/Candle.hpp"
#include <vector>
#include <string>

namespace server::arrow {

class ArrowIPCBuilder {
public:
    // Serializes vector of 48-column TradeResults into high-speed binary IPC Stream buffer
    static std::string serializeToBinaryIPCStream(const std::vector<data::TradeResult>& trades);
};

} // namespace server::arrow
