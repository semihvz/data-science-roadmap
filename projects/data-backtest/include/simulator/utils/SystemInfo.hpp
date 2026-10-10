#pragma once

#include <cstdint>
#include <string>
#include <fstream>
#include <chrono>
#include <sys/resource.h>
#include <unistd.h>

namespace simulator::utils {

class SystemInfo {
public:
    static double getPeakRSSMB() {
        struct rusage usage;
        if (getrusage(RUSAGE_SELF, &usage) == 0) {
            // ru_maxrss is in kilobytes on Linux
            return static_cast<double>(usage.ru_maxrss) / 1024.0;
        }
        return 0.0;
    }

    static double getCurrentRSSMB() {
        std::ifstream stat_stream("/proc/self/stat", std::ios_base::in);
        if (!stat_stream.is_open()) return 0.0;

        std::string pid, comm, state, ppid, pgrp, session, tty_nr, tpgid, flags;
        std::string minflt, cminflt, majflt, cmajflt, utime, stime, cutime, cstime;
        std::string priority, nice, num_threads, itrealvalue, starttime, vsize;
        long rss;

        stat_stream >> pid >> comm >> state >> ppid >> pgrp >> session >> tty_nr
                    >> tpgid >> flags >> minflt >> cminflt >> majflt >> cmajflt
                    >> utime >> stime >> cutime >> cstime >> priority >> nice
                    >> num_threads >> itrealvalue >> starttime >> vsize >> rss;

        stat_stream.close();
        long page_size_kb = sysconf(_SC_PAGE_SIZE) / 1024;
        return static_cast<double>(rss * page_size_kb) / 1024.0;
    }

    static int64_t getCurrentTimeMs() {
        return std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count();
    }

    static std::string ISO8601Now() {
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        char buf[32];
        std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&in_time_t));
        return std::string(buf);
    }
};

} // namespace simulator::utils
