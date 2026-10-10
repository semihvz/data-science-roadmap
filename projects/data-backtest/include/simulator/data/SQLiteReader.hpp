#pragma once

#include "simulator/data/DataReader.hpp"

namespace simulator::data {

class SQLiteReader : public DataReader {
public:
    SQLiteReader() = default;
    SoACandles loadSymbolData(const std::string& path, const std::string& symbol) override;
    std::string getSourceDataHash() const override { return source_hash_; }

private:
    std::string source_hash_;
    int64_t parseTimestampToEpochSec(const std::string& tsStr);
};

} // namespace simulator::data
