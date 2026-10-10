#include "server/cache/SymbolCacheManager.hpp"
#include "server/data/SQLiteReader.hpp"
#include <filesystem>
#include <iostream>
#include <stdexcept>

namespace server::cache {

namespace fs = std::filesystem;

SymbolCacheManager::SymbolCacheManager(const std::string& rawDataDir, size_t maxCachedSymbols)
    : raw_data_dir_(rawDataDir), max_cached_symbols_(maxCachedSymbols) {}

std::shared_ptr<CachedSymbol> SymbolCacheManager::getOrLoadSymbol(const std::string& symbol) {
    std::lock_guard<std::mutex> lock(mutex_);

    // Check if in cache
    auto it = cache_map_.find(symbol);
    if (it != cache_map_.end()) {
        // Move to front of LRU list
        lru_list_.remove(symbol);
        lru_list_.push_front(symbol);
        return it->second;
    }

    // Lazy load from disk
    fs::path dbPath = fs::path(raw_data_dir_) / (symbol + ".db");
    if (!fs::exists(dbPath)) {
        dbPath = fs::path(raw_data_dir_) / (symbol + ".sqlite");
        if (!fs::exists(dbPath)) {
            throw std::runtime_error("Symbol dataset file not found: " + dbPath.string());
        }
    }

    std::cout << "[CACHE] Loading " << symbol << " on-demand from " << dbPath.string() << " into RAM..." << std::endl;
    auto cached = std::make_shared<CachedSymbol>();
    cached->symbol = symbol;
    cached->candles = data::SQLiteReader::loadSymbolData(dbPath.string());
    cached->validation_report = validation::DataValidator::validateAndSegment(cached->candles);

    // Build Segment Trees
    cached->segment_trees.resize(cached->validation_report.segments.size());
    for (size_t s = 0; s < cached->validation_report.segments.size(); ++s) {
        const auto& seg = cached->validation_report.segments[s];
        cached->segment_trees[s].build(
            cached->candles.high.data() + seg.start_index,
            cached->candles.low.data() + seg.start_index,
            seg.length()
        );
    }

    // Evict LRU if full
    if (cache_map_.size() >= max_cached_symbols_) {
        std::string lruSymbol = lru_list_.back();
        lru_list_.pop_back();
        cache_map_.erase(lruSymbol);
        std::cout << "[CACHE] Evicted LRU symbol from RAM: " << lruSymbol << std::endl;
    }

    cache_map_[symbol] = cached;
    lru_list_.push_front(symbol);
    std::cout << "[CACHE] Symbol " << symbol << " (" << cached->candles.size() << " candles) successfully loaded in RAM!" << std::endl;

    return cached;
}

std::vector<std::string> SymbolCacheManager::getAvailableSymbols() const {
    std::vector<std::string> symbols;
    if (fs::exists(raw_data_dir_)) {
        for (const auto& entry : fs::directory_iterator(raw_data_dir_)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                if (ext == ".db" || ext == ".sqlite") {
                    symbols.push_back(entry.path().stem().string());
                }
            }
        }
    }
    std::sort(symbols.begin(), symbols.end());
    return symbols;
}

} // namespace server::cache

