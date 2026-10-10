#pragma once

#include "simulator/data/Candle.hpp"
#include <string>

namespace simulator::data {

class DataReader {
public:
    virtual ~DataReader() = default;
    virtual SoACandles loadSymbolData(const std::string& path, const std::string& symbol) = 0;
    virtual std::string getSourceDataHash() const = 0;
};

} // namespace simulator::data
