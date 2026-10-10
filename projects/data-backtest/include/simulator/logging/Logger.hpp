#pragma once

#include <string>
#include <mutex>
#include <iostream>

namespace simulator::logging {

enum class LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3
};

class Logger {
public:
    static Logger& instance() {
        static Logger inst;
        return inst;
    }

    void setLevel(LogLevel lvl) {
        level_ = lvl;
    }

    void log(LogLevel lvl, const std::string& symbol, const std::string& msg);

    void info(const std::string& symbol, const std::string& msg) { log(LogLevel::INFO, symbol, msg); }
    void warn(const std::string& symbol, const std::string& msg) { log(LogLevel::WARNING, symbol, msg); }
    void error(const std::string& symbol, const std::string& msg) { log(LogLevel::ERROR, symbol, msg); }
    void debug(const std::string& symbol, const std::string& msg) { log(LogLevel::DEBUG, symbol, msg); }

private:
    Logger() : level_(LogLevel::INFO) {}
    LogLevel level_;
    std::mutex mutex_;
};

} // namespace simulator::logging
