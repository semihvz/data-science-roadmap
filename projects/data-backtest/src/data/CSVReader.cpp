#include "simulator/data/CSVReader.hpp"
#include "simulator/utils/Hash.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <ctime>
#include <iomanip>

namespace simulator::data {

int64_t CSVReader::parseTimestampToEpochSec(const std::string& tsStr) {
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

SoACandles CSVReader::loadSymbolData(const std::string& csvPath, const std::string& symbol) {
    std::ifstream file(csvPath);
    if (!file.is_open()) {
        throw std::runtime_error("CSVReader: cannot open " + csvPath);
    }

    SoACandles candles;
    std::string line;
    bool headerChecked = false;
    uint64_t fnvHash = 14695981039346656037ULL;

    while (std::getline(file, line)) {
        if (line.empty()) continue;
        // Skip header if line starts with letters like open_time or timestamp
        if (!headerChecked) {
            headerChecked = true;
            if (line.find("time") != std::string::npos || line.find("open") != std::string::npos || line.find("Timestamp") != std::string::npos) {
                continue;
            }
        }

        std::stringstream ss(line);
        std::string col;
        std::vector<std::string> tokens;
        while (std::getline(ss, col, ',')) {
            tokens.push_back(col);
        }

        if (tokens.size() < 6) continue;

        // Standard CSV format: timestamp, open, high, low, close, volume
        int64_t ts = parseTimestampToEpochSec(tokens[0]);
        double o = std::stod(tokens[1]);
        double h = std::stod(tokens[2]);
        double l = std::stod(tokens[3]);
        double c = std::stod(tokens[4]);
        double v = std::stod(tokens[5]);

        candles.push_back(ts, o, h, l, c, v);

        fnvHash ^= static_cast<uint64_t>(ts);
        fnvHash *= 1099511628211ULL;
    }

    file.close();
    std::ostringstream hss;
    hss << std::hex << std::setw(16) << std::setfill('0') << fnvHash;
    source_hash_ = hss.str();

    return candles;
}

} // namespace simulator::data
