cmake_minimum_required(VERSION 3.20)
project(binance_futures_trade_simulator VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Optimization and warning flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wconversion -Wshadow -O3)
endif()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)

# Third-party SQLite amalgamation
add_library(sqlite3_static STATIC third_party/sqlite3/sqlite3.c)
target_include_directories(sqlite3_static PUBLIC third_party/sqlite3)
target_compile_options(sqlite3_static PRIVATE -w)

# Core Simulator Library
add_library(simulator_core STATIC
    src/config/CLIParser.cpp
    src/data/SQLiteReader.cpp
    src/data/CSVReader.cpp
    src/validation/DataValidator.cpp
    src/indexing/SegmentTree.cpp
    src/database/DatabaseManager.cpp
    src/simulation/ReferenceEngine.cpp
    src/simulation/SimulationEngine.cpp
    src/logging/Logger.cpp
)
target_link_libraries(simulator_core PUBLIC sqlite3_static)

# Main Executable
add_executable(simulator src/main.cpp)
target_link_libraries(simulator PRIVATE simulator_core)

# Enable Testing
enable_testing()

add_executable(test_validation tests/unit/test_validation.cpp)
target_link_libraries(test_validation PRIVATE simulator_core)
add_test(NAME test_validation COMMAND test_validation)

add_executable(test_segment_tree tests/unit/test_segment_tree.cpp)
target_link_libraries(test_segment_tree PRIVATE simulator_core)
add_test(NAME test_segment_tree COMMAND test_segment_tree)

add_executable(test_simulation_rules tests/unit/test_simulation_rules.cpp)
target_link_libraries(test_simulation_rules PRIVATE simulator_core)
add_test(NAME test_simulation_rules COMMAND test_simulation_rules)

add_executable(test_reference_engine tests/reference/test_reference_engine.cpp)
target_link_libraries(test_reference_engine PRIVATE simulator_core)
add_test(NAME test_reference_engine COMMAND test_reference_engine)

add_executable(test_randomized_equivalence tests/randomized/test_randomized_equivalence.cpp)
target_link_libraries(test_randomized_equivalence PRIVATE simulator_core)
add_test(NAME test_randomized_equivalence COMMAND test_randomized_equivalence)

# Benchmark Tool
add_executable(benchmark_runner tools/benchmark/benchmark_runner.cpp)
target_link_libraries(benchmark_runner PRIVATE simulator_core)
