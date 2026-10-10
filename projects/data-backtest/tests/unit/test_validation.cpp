#include "simulator/validation/DataValidator.hpp"
#include <cassert>
#include <iostream>
#include <limits>

using namespace simulator;

void testBasicValidation() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 105.0, 95.0, 102.0, 10.0);
    candles.push_back(1060, 102.0, 108.0, 101.0, 106.0, 15.0);

    auto report = validation::DataValidator::validateAndSegment(candles, 60, true, false);
    assert(report.is_valid);
    assert(report.valid_candles == 2);
    assert(report.segments.size() == 1);
    std::cout << "[PASS] testBasicValidation" << std::endl;
}

void testGapDetection() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 105.0, 95.0, 102.0, 10.0);
    candles.push_back(1200, 102.0, 108.0, 101.0, 106.0, 15.0); // 140s gap > 60s

    auto report = validation::DataValidator::validateAndSegment(candles, 60, false, false);
    assert(report.data_gaps == 1);
    assert(report.segments.size() == 2);
    std::cout << "[PASS] testGapDetection" << std::endl;
}

void testInvalidOHLC() {
    data::SoACandles candles;
    candles.push_back(1000, 100.0, 90.0, 95.0, 102.0, 10.0); // High < Low!

    auto report = validation::DataValidator::validateAndSegment(candles, 60, true, false);
    assert(!report.is_valid);
    std::cout << "[PASS] testInvalidOHLC" << std::endl;
}

int main() {
    testBasicValidation();
    testGapDetection();
    testInvalidOHLC();
    std::cout << "All validation tests passed successfully!" << std::endl;
    return 0;
}
