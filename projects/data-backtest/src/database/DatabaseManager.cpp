#include "simulator/database/DatabaseManager.hpp"
#include "simulator/utils/SystemInfo.hpp"
#include "simulator/logging/Logger.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <iostream>

namespace simulator::database {

DatabaseManager::DatabaseManager(const std::string& finalDbPath, const config::Config& cfg)
    : final_path_(finalDbPath), config_(cfg) {
    partial_path_ = finalDbPath + ".partial";
    openDatabase();
}

DatabaseManager::~DatabaseManager() {
    finalizeStatements();
    closeDatabase();
}

void DatabaseManager::openDatabase() {
    if (sqlite3_open_v2(partial_path_.c_str(), &db_, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE, nullptr) != SQLITE_OK) {
        std::string err = db_ ? sqlite3_errmsg(db_) : "Cannot open file";
        throw std::runtime_error("DatabaseManager open error: " + err);
    }

    if (config_.unsafe_fast_mode) {
        sqlite3_exec(db_, "PRAGMA synchronous = OFF; PRAGMA journal_mode = OFF;", nullptr, nullptr, nullptr);
    } else {
        sqlite3_exec(db_, "PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY;", nullptr, nullptr, nullptr);
    }
}

void DatabaseManager::closeDatabase() {
    if (db_) {
        sqlite3_close(db_);
        db_ = nullptr;
    }
}

void DatabaseManager::initializeSchema(const std::string& schemaSqlPath) {
    std::ifstream file(schemaSqlPath);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open schema file: " + schemaSqlPath);
    }
    std::string sql((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    file.close();

    char* errMsgs = nullptr;
    if (sqlite3_exec(db_, sql.c_str(), nullptr, nullptr, &errMsgs) != SQLITE_OK) {
        std::string err = errMsgs ? errMsgs : "Schema init error";
        sqlite3_free(errMsgs);
        throw std::runtime_error("Schema init failed: " + err);
    }

    prepareStatements();
}

void DatabaseManager::prepareStatements() {
    std::string sqlPos =
        "INSERT INTO positions ("
        "run_id, symbol, side, entry_bar_index, exit_bar_index, entry_bar_open_time, entry_time, exit_bar_open_time, "
        "entry_price, exit_price, tp_price, sl_price, sl_percent, tp_percent, risk_reward_ratio, status, exit_reason, "
        "bars_held, duration_lower_bound_seconds, duration_upper_bound_seconds, duration_minutes_approx, nominal_r, "
        "gross_pnl_percent, net_pnl_percent, gross_pnl_r, net_pnl_r, same_bar_sl_tp, intrabar_ambiguous, gap_through_barrier, "
        "data_segment_id, entry_candle_open, entry_candle_high, entry_candle_low, entry_candle_close, entry_candle_volume, "
        "exit_candle_open, exit_candle_high, exit_candle_low, exit_candle_close, exit_candle_volume, "
        "max_favorable_excursion_pct, max_adverse_excursion_pct, mfe_r, mae_r, last_available_price, last_available_timestamp, "
        "unrealized_pnl_pct, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);";

    if (sqlite3_prepare_v2(db_, sqlPos.c_str(), -1, &stmt_insert_pos_, nullptr) != SQLITE_OK) {
        throw std::runtime_error("Failed to prepare position statement: " + std::string(sqlite3_errmsg(db_)));
    }
}

void DatabaseManager::finalizeStatements() {
    if (stmt_insert_pos_) {
        sqlite3_finalize(stmt_insert_pos_);
        stmt_insert_pos_ = nullptr;
    }
}

void DatabaseManager::recordRunStart(const std::string& runId, const std::string& sourceDataHash) {
    current_run_id_ = runId;
    std::string sql = "INSERT OR REPLACE INTO runs (run_id, symbol, timeframe, sl_percent, risk_reward_ratio, tp_percent, "
                      "intrabar_policy, gap_execution_model, price_model, config_hash, source_data_hash, algorithm_version, "
                      "schema_version, compiler_info, build_type, created_at, status, simulation_complete) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);";

    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, runId.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, config_.symbol.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, config_.timeframe.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_double(stmt, 4, config_.sl_percent);
    sqlite3_bind_double(stmt, 5, config_.risk_reward_ratio);
    sqlite3_bind_double(stmt, 6, config_.tp_percent);
    sqlite3_bind_text(stmt, 7, "sl-first", -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 8, "barrier", -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 9, "DOUBLE_PRECISION", -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 10, config_.computeConfigHash().c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 11, sourceDataHash.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 12, config_.algorithm_version.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 13, config_.schema_version.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 14, "GCC 15.2.0", -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 15, "Release", -1, SQLITE_TRANSIENT);
    std::string nowStr = utils::SystemInfo::ISO8601Now();
    sqlite3_bind_text(stmt, 16, nowStr.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 17, "SIMULATING", -1, SQLITE_TRANSIENT);

    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}

void DatabaseManager::recordDataQuality(const std::string& runId, const validation::ValidationReport& report, const std::string& sourceDataHash) {
    std::string sql = "INSERT INTO data_quality (run_id, total_candles, valid_candles, invalid_candles, duplicate_timestamps, "
                      "out_of_order_timestamps, missing_candles, invalid_ohlc_count, segment_count, data_gaps, data_hash, validated_at) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, runId.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(stmt, 2, report.total_candles);
    sqlite3_bind_int64(stmt, 3, report.valid_candles);
    sqlite3_bind_int64(stmt, 4, report.invalid_candles);
    sqlite3_bind_int64(stmt, 5, report.duplicate_timestamps);
    sqlite3_bind_int64(stmt, 6, report.out_of_order_timestamps);
    sqlite3_bind_int64(stmt, 7, report.missing_candles);
    sqlite3_bind_int64(stmt, 8, report.invalid_ohlc_count);
    sqlite3_bind_int64(stmt, 9, report.segments.size());
    sqlite3_bind_int64(stmt, 10, report.data_gaps);
    sqlite3_bind_text(stmt, 11, sourceDataHash.c_str(), -1, SQLITE_TRANSIENT);
    std::string nowStr = utils::SystemInfo::ISO8601Now();
    sqlite3_bind_text(stmt, 12, nowStr.c_str(), -1, SQLITE_TRANSIENT);

    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}

void DatabaseManager::recordSegments(const std::string& runId, const std::vector<data::Segment>& segments) {
    sqlite3_exec(db_, "BEGIN TRANSACTION;", nullptr, nullptr, nullptr);
    std::string sql = "INSERT INTO segments (segment_id, run_id, start_bar_index, end_bar_index, candle_count, start_timestamp, end_timestamp) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?);";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr);

    for (const auto& seg : segments) {
        sqlite3_bind_int(stmt, 1, seg.segment_id);
        sqlite3_bind_text(stmt, 2, runId.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_int(stmt, 3, seg.start_index);
        sqlite3_bind_int(stmt, 4, seg.end_index);
        sqlite3_bind_int(stmt, 5, seg.length());
        sqlite3_bind_int64(stmt, 6, seg.start_timestamp);
        sqlite3_bind_int64(stmt, 7, seg.end_timestamp);
        sqlite3_step(stmt);
        sqlite3_reset(stmt);
    }
    sqlite3_finalize(stmt);
    sqlite3_exec(db_, "COMMIT;", nullptr, nullptr, nullptr);
}

void DatabaseManager::insertPositionsBatch(const std::vector<data::TradeResult>& trades) {
    if (trades.empty()) return;

    sqlite3_exec(db_, "BEGIN IMMEDIATE TRANSACTION;", nullptr, nullptr, nullptr);
    std::string nowStr = utils::SystemInfo::ISO8601Now();

    for (const auto& tr : trades) {
        sqlite3_reset(stmt_insert_pos_);

        // Bind parameters
        sqlite3_bind_text(stmt_insert_pos_, 1, current_run_id_.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_text(stmt_insert_pos_, 2, config_.symbol.c_str(), -1, SQLITE_TRANSIENT);
        sqlite3_bind_int(stmt_insert_pos_, 3, static_cast<int>(tr.side));
        sqlite3_bind_int(stmt_insert_pos_, 4, tr.entry_bar_index);
        if (tr.exit_bar_index >= 0) sqlite3_bind_int(stmt_insert_pos_, 5, tr.exit_bar_index);
        else sqlite3_bind_null(stmt_insert_pos_, 5);

        sqlite3_bind_int64(stmt_insert_pos_, 6, tr.entry_bar_open_time);
        sqlite3_bind_int64(stmt_insert_pos_, 7, tr.entry_time);
        if (tr.exit_bar_open_time > 0) sqlite3_bind_int64(stmt_insert_pos_, 8, tr.exit_bar_open_time);
        else sqlite3_bind_null(stmt_insert_pos_, 8);

        sqlite3_bind_double(stmt_insert_pos_, 9, tr.entry_price);
        if (tr.status == data::PositionStatus::CLOSED) sqlite3_bind_double(stmt_insert_pos_, 10, tr.exit_price);
        else sqlite3_bind_null(stmt_insert_pos_, 10);

        sqlite3_bind_double(stmt_insert_pos_, 11, tr.tp_price);
        sqlite3_bind_double(stmt_insert_pos_, 12, tr.sl_price);
        sqlite3_bind_double(stmt_insert_pos_, 13, tr.sl_percent);
        sqlite3_bind_double(stmt_insert_pos_, 14, tr.tp_percent);
        sqlite3_bind_double(stmt_insert_pos_, 15, tr.risk_reward_ratio);
        sqlite3_bind_int(stmt_insert_pos_, 16, static_cast<int>(tr.status));
        sqlite3_bind_int(stmt_insert_pos_, 17, static_cast<int>(tr.exit_reason));

        if (tr.status == data::PositionStatus::CLOSED) sqlite3_bind_int(stmt_insert_pos_, 18, tr.bars_held);
        else sqlite3_bind_null(stmt_insert_pos_, 18);

        sqlite3_bind_int64(stmt_insert_pos_, 19, tr.duration_lower_bound_seconds);
        sqlite3_bind_int64(stmt_insert_pos_, 20, tr.duration_upper_bound_seconds);
        sqlite3_bind_double(stmt_insert_pos_, 21, tr.duration_minutes_approx);
        sqlite3_bind_double(stmt_insert_pos_, 22, tr.nominal_r);
        sqlite3_bind_double(stmt_insert_pos_, 23, tr.gross_pnl_percent);
        sqlite3_bind_double(stmt_insert_pos_, 24, tr.net_pnl_percent);
        sqlite3_bind_double(stmt_insert_pos_, 25, tr.gross_pnl_r);
        sqlite3_bind_double(stmt_insert_pos_, 26, tr.net_pnl_r);
        sqlite3_bind_int(stmt_insert_pos_, 27, tr.same_bar_sl_tp);
        sqlite3_bind_int(stmt_insert_pos_, 28, tr.intrabar_ambiguous);
        sqlite3_bind_int(stmt_insert_pos_, 29, tr.gap_through_barrier);
        sqlite3_bind_int(stmt_insert_pos_, 30, tr.data_segment_id);

        sqlite3_bind_double(stmt_insert_pos_, 31, tr.entry_candle_open);
        sqlite3_bind_double(stmt_insert_pos_, 32, tr.entry_candle_high);
        sqlite3_bind_double(stmt_insert_pos_, 33, tr.entry_candle_low);
        sqlite3_bind_double(stmt_insert_pos_, 34, tr.entry_candle_close);
        sqlite3_bind_double(stmt_insert_pos_, 35, tr.entry_candle_volume);

        if (tr.status == data::PositionStatus::CLOSED) {
            sqlite3_bind_double(stmt_insert_pos_, 36, tr.exit_candle_open);
            sqlite3_bind_double(stmt_insert_pos_, 37, tr.exit_candle_high);
            sqlite3_bind_double(stmt_insert_pos_, 38, tr.exit_candle_low);
            sqlite3_bind_double(stmt_insert_pos_, 39, tr.exit_candle_close);
            sqlite3_bind_double(stmt_insert_pos_, 40, tr.exit_candle_volume);
        } else {
            for (int k = 36; k <= 40; ++k) sqlite3_bind_null(stmt_insert_pos_, k);
        }

        sqlite3_bind_double(stmt_insert_pos_, 41, tr.max_favorable_excursion_pct);
        sqlite3_bind_double(stmt_insert_pos_, 42, tr.max_adverse_excursion_pct);
        sqlite3_bind_double(stmt_insert_pos_, 43, tr.mfe_r);
        sqlite3_bind_double(stmt_insert_pos_, 44, tr.mae_r);

        if (tr.status != data::PositionStatus::CLOSED) {
            sqlite3_bind_double(stmt_insert_pos_, 45, tr.last_available_price);
            sqlite3_bind_int64(stmt_insert_pos_, 46, tr.last_available_timestamp);
            sqlite3_bind_double(stmt_insert_pos_, 47, tr.unrealized_pnl_pct);
        } else {
            sqlite3_bind_null(stmt_insert_pos_, 45);
            sqlite3_bind_null(stmt_insert_pos_, 46);
            sqlite3_bind_null(stmt_insert_pos_, 47);
        }

        sqlite3_bind_text(stmt_insert_pos_, 48, nowStr.c_str(), -1, SQLITE_TRANSIENT);

        sqlite3_step(stmt_insert_pos_);
    }

    sqlite3_exec(db_, "COMMIT;", nullptr, nullptr, nullptr);
}

void DatabaseManager::updateCheckpoint(const std::string& runId, int32_t lastCompletedEntryIndex, int64_t tradeCount) {
    std::string sql = "INSERT OR REPLACE INTO checkpoints (run_id, last_completed_entry_index, last_committed_entry_index, "
                      "last_committed_trade_id, committed_trade_count, checkpoint_time) VALUES (?, ?, ?, ?, ?, ?);";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, runId.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 2, lastCompletedEntryIndex);
    sqlite3_bind_int(stmt, 3, lastCompletedEntryIndex);
    sqlite3_bind_int64(stmt, 4, tradeCount);
    sqlite3_bind_int64(stmt, 5, tradeCount);
    std::string nowStr = utils::SystemInfo::ISO8601Now();
    sqlite3_bind_text(stmt, 6, nowStr.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}

int32_t DatabaseManager::getCheckpointEntryIndex(const std::string& runId) {
    std::string sql = "SELECT last_completed_entry_index FROM checkpoints WHERE run_id = ?;";
    sqlite3_stmt* stmt = nullptr;
    if (sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr) != SQLITE_OK) return -1;
    sqlite3_bind_text(stmt, 1, runId.c_str(), -1, SQLITE_TRANSIENT);
    int32_t idx = -1;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        idx = sqlite3_column_int(stmt, 0);
    }
    sqlite3_finalize(stmt);
    return idx;
}

void DatabaseManager::finalizeRun(const std::string& runId, bool success) {
    std::string statusStr = success ? "COMPLETED" : "FAILED";
    int completeVal = success ? 1 : 0;
    std::string sql = "UPDATE runs SET status = ?, simulation_complete = ? WHERE run_id = ?;";
    sqlite3_stmt* stmt = nullptr;
    sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, statusStr.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 2, completeVal);
    sqlite3_bind_text(stmt, 3, runId.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}

bool DatabaseManager::checkIntegrity() {
    sqlite3_stmt* stmt = nullptr;
    if (sqlite3_prepare_v2(db_, "PRAGMA integrity_check;", -1, &stmt, nullptr) != SQLITE_OK) {
        return false;
    }
    bool ok = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const char* res = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        if (res && std::string(res) == "ok") {
            ok = true;
        }
    }
    sqlite3_finalize(stmt);
    return ok;
}

void DatabaseManager::atomicRenameToFinal() {
    finalizeStatements();
    closeDatabase();
    if (std::rename(partial_path_.c_str(), final_path_.c_str()) != 0) {
        throw std::runtime_error("Atomic rename failed from " + partial_path_ + " to " + final_path_);
    }
}

} // namespace simulator::database
