#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace simulator::config {

enum class IntrabarPolicy {
    SL_FIRST,
    TP_FIRST,
    AMBIGUOUS_ONLY
};

enum class GapExecutionModel {
    BARRIER_PRICE_MODEL,
    CONSERVATIVE_GAP_MODEL
};

struct Config {
    std::string input_path;
    std::string output_dir = "./db";
    std::string symbol = "BTCUSDT";
    std::string timeframe = "1m";

    double sl_percent = 0.005;     // 0.5%
    double risk_reward_ratio = 3.0; // 3.0 (TP = 1.5%)
    double tp_percent = 0.015;      // sl_percent * RR

    uint32_t threads = 8;
    uint32_t batch_size = 10000;
    uint64_t memory_limit_mb = 3072;

    IntrabarPolicy intrabar_policy = IntrabarPolicy::SL_FIRST;
    GapExecutionModel gap_execution_model = GapExecutionModel::BARRIER_PRICE_MODEL;

    bool calculate_excursions = true;
    bool strict_validation = true;
    bool repair_order = false;
    bool unsafe_fast_mode = false;
    bool resume = true;

    double maker_fee = 0.0;
    double taker_fee = 0.0;
    double entry_slippage_bps = 0.0;
    double exit_slippage_bps = 0.0;

    double tick_size = 0.01; // default tick size
    std::string algorithm_version = "1.0.0";
    std::string schema_version = "1.0.0";

    std::string computeConfigHash() const;
    void validate() const;
};

class CLIParser {
public:
    static Config parse(int argc, char* argv[]);
    static void printUsage(const char* progName);
};

} // namespace simulator::config
