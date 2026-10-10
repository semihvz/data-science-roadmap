#include "simulator/config/CLIParser.hpp"
#include "simulator/data/SQLiteReader.hpp"
#include "simulator/data/CSVReader.hpp"
#include "simulator/validation/DataValidator.hpp"
#include "simulator/database/DatabaseManager.hpp"
#include "simulator/simulation/SimulationEngine.hpp"
#include "simulator/logging/Logger.hpp"
#include "simulator/utils/SystemInfo.hpp"
#include <iostream>
#include <filesystem>
#include <memory>

namespace fs = std::filesystem;
using namespace simulator;

int main(int argc, char* argv[]) {
    try {
        config::Config cfg = config::CLIParser::parse(argc, argv);
        logging::Logger::instance().info(cfg.symbol, "Starting Binance Futures Trade Simulator Engine v" + cfg.algorithm_version);

        // Ensure output directory exists
        fs::create_directories(cfg.output_dir);
        std::string finalDbPath = (fs::path(cfg.output_dir) / (cfg.symbol + ".sqlite")).string();

        // 1. Data Reading Stage
        logging::Logger::instance().info(cfg.symbol, "Loading input dataset from: " + cfg.input_path);
        std::unique_ptr<data::DataReader> reader;
        if (cfg.input_path.ends_with(".db") || cfg.input_path.ends_with(".sqlite")) {
            reader = std::make_unique<data::SQLiteReader>();
        } else {
            reader = std::make_unique<data::CSVReader>();
        }

        data::SoACandles candles = reader->loadSymbolData(cfg.input_path, cfg.symbol);
        std::string sourceHash = reader->getSourceDataHash();
        logging::Logger::instance().info(cfg.symbol, "Loaded " + std::to_string(candles.size()) + " candles. Source Hash: " + sourceHash);

        if (candles.size() == 0) {
            logging::Logger::instance().error(cfg.symbol, "Input dataset contains 0 candles. Exiting.");
            return 1;
        }

        // 2. Data Validation & Segmentation Stage
        logging::Logger::instance().info(cfg.symbol, "Validating dataset & detecting contiguous segments...");
        validation::ValidationReport valReport = validation::DataValidator::validateAndSegment(
            candles, 60, cfg.strict_validation, cfg.repair_order
        );

        if (!valReport.is_valid) {
            logging::Logger::instance().error(cfg.symbol, "Validation failed: " + valReport.error_message);
            return 1;
        }

        logging::Logger::instance().info(cfg.symbol, "Validation passed. Valid candles: " + std::to_string(valReport.valid_candles) +
                                                      ", Segments: " + std::to_string(valReport.segments.size()) +
                                                      ", Gaps: " + std::to_string(valReport.data_gaps));

        // 3. Database Initialization Stage
        std::string runId = "RUN_" + cfg.computeConfigHash().substr(0, 8);
        logging::Logger::instance().info(cfg.symbol, "Initializing SQLite database: " + finalDbPath + ".partial (Run ID: " + runId + ")");

        database::DatabaseManager dbManager(finalDbPath, cfg);
        dbManager.initializeSchema("schema/schema.sql");
        dbManager.recordRunStart(runId, sourceHash);
        dbManager.recordDataQuality(runId, valReport, sourceHash);
        dbManager.recordSegments(runId, valReport.segments);

        // 4. Optimized Simulation Stage
        logging::Logger::instance().info(cfg.symbol, "Executing multi-threaded simulation pipeline (" + std::to_string(cfg.threads) + " threads)...");
        simulation::SimulationEngine engine(cfg);
        simulation::SimulationStats stats = engine.run(candles, valReport, dbManager, runId);

        // 5. Finalization & Integrity Check
        logging::Logger::instance().info(cfg.symbol, "Simulation complete in " + std::to_string(stats.simulation_duration_sec) + " seconds. Verifying database integrity...");
        dbManager.finalizeRun(runId, true);

        if (!dbManager.checkIntegrity()) {
            logging::Logger::instance().error(cfg.symbol, "PRAGMA integrity_check failed for output database!");
            return 1;
        }

        dbManager.atomicRenameToFinal();
        logging::Logger::instance().info(cfg.symbol, "Database verified and atomically saved to: " + finalDbPath);
        logging::Logger::instance().info(cfg.symbol, "Peak RSS Memory: " + std::to_string(stats.peak_rss_mb) + " MB (Limit: " + std::to_string(cfg.memory_limit_mb) + " MB)");

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Fatal Error: " << ex.what() << std::endl;
        return 1;
    }
}
