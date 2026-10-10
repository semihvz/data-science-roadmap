#pragma once

#include "server/data/Candle.hpp"
#include <string>

namespace server::data {

class SQLiteReader {
public:
    static SoACandles loadSymbolData(const std::string& dbPath);
};

} // namespace server::data
