#include "simulator/config/CLIParser.hpp"
#include "simulator/utils/Hash.hpp"
#include "simulator/utils/FixedPoint.hpp"
#include <iostream>
#include <stdexcept>
#include <thread>
#include <sstream>

namespace simulator::config {

std::string Config::computeConfigHash() const {
    std::ostringstream ss;
    ss << "symbol=" << symbol << ";"
       << "tf=" << timeframe << ";"
       << "sl=" << utils::PriceUtils::formatCanonicalDouble(sl_percent) << ";"
       << "rr=" << utils::PriceUtils::formatCanonicalDouble(risk_reward_ratio) << ";"
       << "tp=" << utils::PriceUtils::formatCanonicalDouble(tp_percent) << ";"
       << "intrabar=" << (intrabar_policy == IntrabarPolicy::SL_FIRST ? "sl-first" : (intrabar_policy == IntrabarPolicy::TP_FIRST ? "tp-first" : "ambiguous-only")) << ";"
       << "gap_exec=" << (gap_execution_model == GapExecutionModel::BARRIER_PRICE_MODEL ? "barrier" : "conservative") << ";"
       << "excursions=" << (calculate_excursions ? "true" : "false") << ";"
       << "algo_v=" << algorithm_version << ";"
       << "schema_v=" << schema_version;
    return utils::Hash::fnv1a64(ss.str());
}

void Config::validate() const {
    if (input_path.empty()) {
        throw std::invalid_argument("--input parameter is required");
    }
    if (sl_percent <= 0.0 || sl_percent >= 1.0) {
        throw std::invalid_argument("Stop loss percentage must satisfy: 0 < SL < 1");
    }
    if (risk_reward_ratio <= 0.0) {
        throw std::invalid_argument("Risk reward ratio must satisfy: RR > 0");
    }
    if (threads < 1) {
        throw std::invalid_argument("Threads must be >= 1");
    }
    if (batch_size < 1) {
        throw std::invalid_argument("Batch size must be >= 1");
    }
    if (memory_limit_mb == 0) {
        throw std::invalid_argument("Memory limit must be > 0 MB");
    }
}

void CLIParser::printUsage(const char* progName) {
    std::cout << "Usage: " << progName << " [options]\n"
              << "Options:\n"
              << "  --input <path>               Input CSV file, SQLite db, or directory (required)\n"
              << "  --output <dir>               Output SQLite directory (default: ./db)\n"
              << "  --symbol <symbol>            Target symbol (default: BTCUSDT)\n"
              << "  --timeframe <tf>             Timeframe (default: 1m)\n"
              << "  --sl <percent>               Stop loss fraction (default: 0.005)\n"
              << "  --rr <ratio>                 Risk reward ratio (default: 3.0)\n"
              << "  --threads <n>                Number of worker threads (default: hardware concurrency)\n"
              << "  --batch-size <n>             SQLite batch transaction size (default: 10000)\n"
              << "  --memory-limit-mb <mb>       Memory hard limit MB (default: 3072)\n"
              << "  --intrabar-policy <p>        sl-first, tp-first, ambiguous-only (default: sl-first)\n"
              << "  --gap-execution-model <m>    barrier, conservative (default: barrier)\n"
              << "  --calculate-excursions <bool> true|false (default: true)\n"
              << "  --strict-validation <bool>   true|false (default: true)\n"
              << "  --repair-order <bool>        true|false (default: false)\n"
              << "  --unsafe-fast-mode <bool>    true|false (default: false)\n"
              << "  --resume <bool>              true|false (default: true)\n";
}

Config CLIParser::parse(int argc, char* argv[]) {
    Config cfg;
    cfg.threads = std::thread::hardware_concurrency();
    if (cfg.threads < 1) cfg.threads = 4;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if ((arg == "--help" || arg == "-h")) {
            printUsage(argv[0]);
            exit(0);
        } else if (arg == "--input" && i + 1 < argc) {
            cfg.input_path = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            cfg.output_dir = argv[++i];
        } else if (arg == "--symbol" && i + 1 < argc) {
            cfg.symbol = argv[++i];
        } else if (arg == "--timeframe" && i + 1 < argc) {
            cfg.timeframe = argv[++i];
        } else if (arg == "--sl" && i + 1 < argc) {
            cfg.sl_percent = std::stod(argv[++i]);
        } else if (arg == "--rr" && i + 1 < argc) {
            cfg.risk_reward_ratio = std::stod(argv[++i]);
        } else if (arg == "--threads" && i + 1 < argc) {
            cfg.threads = static_cast<uint32_t>(std::stoul(argv[++i]));
        } else if (arg == "--batch-size" && i + 1 < argc) {
            cfg.batch_size = static_cast<uint32_t>(std::stoul(argv[++i]));
        } else if (arg == "--memory-limit-mb" && i + 1 < argc) {
            cfg.memory_limit_mb = std::stoull(argv[++i]);
        } else if (arg == "--intrabar-policy" && i + 1 < argc) {
            std::string p = argv[++i];
            if (p == "sl-first") cfg.intrabar_policy = IntrabarPolicy::SL_FIRST;
            else if (p == "tp-first") cfg.intrabar_policy = IntrabarPolicy::TP_FIRST;
            else if (p == "ambiguous-only") cfg.intrabar_policy = IntrabarPolicy::AMBIGUOUS_ONLY;
            else throw std::invalid_argument("Unknown intrabar-policy: " + p);
        } else if (arg == "--gap-execution-model" && i + 1 < argc) {
            std::string m = argv[++i];
            if (m == "barrier") cfg.gap_execution_model = GapExecutionModel::BARRIER_PRICE_MODEL;
            else if (m == "conservative") cfg.gap_execution_model = GapExecutionModel::CONSERVATIVE_GAP_MODEL;
            else throw std::invalid_argument("Unknown gap-execution-model: " + m);
        } else if (arg == "--calculate-excursions" && i + 1 < argc) {
            std::string v = argv[++i];
            cfg.calculate_excursions = (v == "true" || v == "1");
        } else if (arg == "--strict-validation" && i + 1 < argc) {
            std::string v = argv[++i];
            cfg.strict_validation = (v == "true" || v == "1");
        } else if (arg == "--repair-order" && i + 1 < argc) {
            std::string v = argv[++i];
            cfg.repair_order = (v == "true" || v == "1");
        } else if (arg == "--unsafe-fast-mode" && i + 1 < argc) {
            std::string v = argv[++i];
            cfg.unsafe_fast_mode = (v == "true" || v == "1");
        } else if (arg == "--resume" && i + 1 < argc) {
            std::string v = argv[++i];
            cfg.resume = (v == "true" || v == "1");
        }
    }

    cfg.tp_percent = cfg.sl_percent * cfg.risk_reward_ratio;
    cfg.validate();
    return cfg;
}

} // namespace simulator::config
