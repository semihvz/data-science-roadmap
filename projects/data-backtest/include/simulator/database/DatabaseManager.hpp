#pragma once

#include "simulator/data/Candle.hpp"
#include "simulator/config/CLIParser.hpp"
#include "simulator/validation/DataValidator.hpp"
#include "sqlite3/sqlite3.h"
#include <string>
#include <vector>
#include <memory>

namespace simulator::database {

class DatabaseManager {
public:
    DatabaseManager(const std::string& dbPath, const config::Config& cfg);
    ~DatabaseManager();

    void initializeSchema(const std::string& schemaSqlPath);

    void recordRunStart(const std::string& runId, const std::string& sourceDataHash);
    void recordDataQuality(const std::string& runId, const validation::ValidationReport& report, const std::string& sourceDataHash);
    void recordSegments(const std::string& runId, const std::vector<data::Segment>& segments);

    void insertPositionsBatch(const std::vector<data::TradeResult>& trades);
    void updateCheckpoint(const std::string& runId, int32_t lastCompletedEntryIndex, int64_t tradeCount);
    int32_t getCheckpointEntryIndex(const std::string& runId);

    void finalizeRun(const std::string& runId, bool success);
    bool checkIntegrity();
    void atomicRenameToFinal();

private:
    std::string partial_path_;
    std::string final_path_;
    std::string current_run_id_;
    config::Config config_;
    sqlite3* db_ = nullptr;
    sqlite3_stmt* stmt_insert_pos_ = nullptr;

    void openDatabase();
    void closeDatabase();
    void prepareStatements();
    void finalizeStatements();
};

} // namespace simulator::database
