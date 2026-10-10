#pragma once

#include "server/data/Candle.hpp"
#include "server/validation/DataValidator.hpp"
#include "server/indexing/SegmentTree.hpp"
#include <string>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <list>

namespace server::cache {

struct CachedSymbol {
    std::string symbol;
    data::SoACandles candles;
    validation::ValidationReport validation_report;
    std::vector<indexing::SegmentTree> segment_trees;
};

class SymbolCacheManager {
public:
    explicit SymbolCacheManager(const std::string& rawDataDir, size_t maxCachedSymbols = 5);

    std::shared_ptr<CachedSymbol> getOrLoadSymbol(const std::string& symbol);
    std::vector<std::string> getAvailableSymbols() const;


private:
    std::string raw_data_dir_;
    size_t max_cached_symbols_;
    std::mutex mutex_;
    std::unordered_map<std::string, std::shared_ptr<CachedSymbol>> cache_map_;
    std::list<std::string> lru_list_;
};

} // namespace server::cache
