#include "simulator/logging/Logger.hpp"
#include "simulator/utils/SystemInfo.hpp"
#include <iostream>

namespace simulator::logging {

void Logger::log(LogLevel lvl, const std::string& symbol, const std::string& msg) {
    if (lvl < level_) return;

    std::lock_guard<std::mutex> lock(mutex_);
    const char* lvlStr = "INFO";
    switch (lvl) {
        case LogLevel::DEBUG: lvlStr = "DEBUG"; break;
        case LogLevel::INFO: lvlStr = "INFO"; break;
        case LogLevel::WARNING: lvlStr = "WARN"; break;
        case LogLevel::ERROR: lvlStr = "ERROR"; break;
    }

    std::string timeStr = utils::SystemInfo::ISO8601Now();
    std::cout << "[" << timeStr << "] [" << lvlStr << "]";
    if (!symbol.empty()) {
        std::cout << " [" << symbol << "]";
    }
    std::cout << " " << msg << std::endl;
}

} // namespace simulator::logging
