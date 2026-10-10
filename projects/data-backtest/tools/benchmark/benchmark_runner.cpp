#include "simulator/simulation/SimulationEngine.hpp"
#include "simulator/database/DatabaseManager.hpp"
#include "simulator/utils/SystemInfo.hpp"
#include <iostream>
#include <random>
#include <chrono>
#include <filesystem>

using namespace simulator;

data::SoACandles generateSyntheticBenchmarkCandles(size_t count) {
    std::mt19937 gen(42);
    std::uniform_real_distribution<double> retDist(-0.003, 0.003);

    data::SoACandles candles;
    candles.reserve(count);
    double close = 100.0;
    int64_t ts = 1600000000;

    for (size_t i = 0; i < count; ++i) {
        double open = close;
        close = open * (1.0 + retDist(gen));
        double high = std::max(open, close) + 0.1;
        double low = std::min(open, close) - 0.1;
        candles.push_back(ts, open, high, low, close, 50.0);
        ts += 60;
    }
    return candles;
}

int main() {
    std::cout << "Starting Binance Futures Trade Simulator Benchmark Tool..." << std::endl;
    size_t candleCount = 100000; // 100k candles -> 200k trades

    data::SoACandles candles = generateSyntheticBenchmarkCandles(candleCount);
    data::Segment seg{0, 0, static_cast<int32_t>(candleCount - 1), candles.timestamps.front(), candles.timestamps.back()};

    validation::ValidationReport valReport;
    valReport.total_candles = candleCount;
    valReport.valid_candles = candleCount;
    valReport.segments = {seg};

    config::Config cfg;
    cfg.input_path = "synthetic";
    cfg.output_dir = "./db_benchmark";
    cfg.symbol = "BENCHMARK";
    cfg.threads = 8;
    cfg.batch_size = 10000;

    std::filesystem::create_directories(cfg.output_dir);
    std::string dbPath = cfg.output_dir + "/BENCHMARK.sqlite";

    database::DatabaseManager dbManager(dbPath, cfg);
    dbManager.initializeSchema("schema/schema.sql");
    dbManager.recordRunStart("BENCH_1", "BENCH_HASH");

    simulation::SimulationEngine engine(cfg);
    auto start = std::chrono::high_resolution_clock::now();
    auto stats = engine.run(candles, valReport, dbManager, "BENCH_1");
    auto end = std::chrono::high_resolution_clock::now();

    double totalSec = std::chrono::duration<double>(end - start).count();
    uint64_t totalTrades = candleCount * 2;

    std::cout << "---------------- BENCHMARK RESULTS ----------------" << std::endl;
    std::cout << "Total Candles Processed: " << candleCount << std::endl;
    std::cout << "Total Trades Generated: " << totalTrades << std::endl;
    std::cout << "Total Time Elapsed:     " << totalSec << " seconds" << std::endl;
    std::cout << "Throughput Candles/Sec: " << (candleCount / totalSec) << std::endl;
    std::cout << "Throughput Trades/Sec:  " << (totalTrades / totalSec) << std::endl;
    std::cout << "Peak RSS Memory:        " << utils::SystemInfo::getPeakRSSMB() << " MB" << std::endl;
    std::cout << "---------------------------------------------------" << std::endl;

    dbManager.finalizeRun("BENCH_1", true);
    dbManager.atomicRenameToFinal();
    return 0;
}
