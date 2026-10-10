#include "simulator/data/SQLiteReader.hpp"
#include "simulator/utils/Hash.hpp"
#include "sqlite3/sqlite3.h"
#include <stdexcept>
#include <ctime>
#include <sstream>
#include <iomanip>
#include <iostream>

namespace simulator::data {

int64_t SQLiteReader::parseTimestampToEpochSec(const std::string& tsStr) {
    if (tsStr.empty()) return 0;
    // Check if numeric string
    bool isNumeric = true;
    for (char c : tsStr) {
        if (!std::isdigit(c) && c != '-') {
            isNumeric = false;
            break;
        }
    }
    if (isNumeric) {
        int64_t val = std::stoll(tsStr);
        if (val > 1000000000000LL) {
            // milliseconds
            return val / 1000;
        }
        return val;
    }

    // Format: "YYYY-MM-DD HH:MM:SS"
    std::tm tm = {};
    std::istringstream ss(tsStr);
    ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
    if (ss.fail()) {
        // Try fallback format without seconds
        ss.clear();
        ss.str(tsStr);
        ss >> std::get_time(&tm, "%Y-%m-%d %H:%M");
    }
    #ifdef _WIN32
        return _mkgmtime(&tm);
    #else
        return timegm(&tm);
    #endif
}

SoACandles SQLiteReader::loadSymbolData(const std::string& dbPath, const std::string& symbol) {
    sqlite3* db = nullptr;
    if (sqlite3_open_v2(dbPath.c_str(), &db, SQLITE_OPEN_READONLY, nullptr) != SQLITE_OK) {
        std::string err = db ? sqlite3_errmsg(db) : "Cannot open file";
        if (db) sqlite3_close(db);
        throw std::runtime_error("SQLiteReader error opening " + dbPath + ": " + err);
    }

    // Query klines table
    std::string sql = "SELECT open_time, open, high, low, close, volume FROM klines ORDER BY open_time ASC;";
    sqlite3_stmt* stmt = nullptr;
    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) != SQLITE_OK) {
        // Try fallback table names
        sql = "SELECT open_time, open, high, low, close, volume FROM candles ORDER BY open_time ASC;";
        if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) != SQLITE_OK) {
            sqlite3_close(db);
            throw std::runtime_error("SQLiteReader query prepare error for " + dbPath + ": " + sqlite3_errmsg(db));
        }
    }

    SoACandles candles;
    uint64_t fnvHash = 14695981039346656037ULL;

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        const char* tsText = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        std::string tsStr = tsText ? tsText : "";
        int64_t ts = parseTimestampToEpochSec(tsStr);

        double o = sqlite3_column_double(stmt, 1);
        double h = sqlite3_column_double(stmt, 2);
        double l = sqlite3_column_double(stmt, 3);
        double c = sqlite3_column_double(stmt, 4);
        double v = sqlite3_column_double(stmt, 5);

        candles.push_back(ts, o, h, l, c, v);

        // Update hash computation
        fnvHash ^= static_cast<uint64_t>(ts);
        fnvHash *= 1099511628211ULL;
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);

    std::ostringstream ss;
    ss << std::hex << std::setw(16) << std::setfill('0') << fnvHash;
    source_hash_ = ss.str();

    return candles;
}

} // namespace simulator::data
