#include "server/data/SQLiteReader.hpp"
#include "sqlite3/sqlite3.h"
#include <stdexcept>
#include <ctime>
#include <sstream>
#include <iomanip>
#include <cctype>

namespace server::data {

static int64_t parseTimestampToEpochSec(const std::string& tsStr) {
    if (tsStr.empty()) return 0;
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
            return val / 1000;
        }
        return val;
    }

    std::tm tm = {};
    std::istringstream ss(tsStr);
    ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
    if (ss.fail()) {
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

SoACandles SQLiteReader::loadSymbolData(const std::string& dbPath) {
    sqlite3* db = nullptr;
    if (sqlite3_open_v2(dbPath.c_str(), &db, SQLITE_OPEN_READONLY, nullptr) != SQLITE_OK) {
        std::string err = db ? sqlite3_errmsg(db) : "Cannot open file";
        if (db) sqlite3_close(db);
        throw std::runtime_error("SQLiteReader error opening " + dbPath + ": " + err);
    }

    std::string sql = "SELECT open_time, open, high, low, close, volume FROM klines ORDER BY open_time ASC;";
    sqlite3_stmt* stmt = nullptr;
    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) != SQLITE_OK) {
        sql = "SELECT open_time, open, high, low, close, volume FROM candles ORDER BY open_time ASC;";
        if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) != SQLITE_OK) {
            sqlite3_close(db);
            throw std::runtime_error("SQLiteReader prepare error for " + dbPath + ": " + sqlite3_errmsg(db));
        }
    }

    SoACandles candles;
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
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return candles;
}

} // namespace server::data
