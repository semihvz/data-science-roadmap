cmake_minimum_required(VERSION 3.20)
project(simulator_server VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wconversion -Wshadow -O3)
endif()

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)

add_library(sqlite3_static STATIC third_party/sqlite3/sqlite3.c)
target_include_directories(sqlite3_static PUBLIC third_party/sqlite3)
target_compile_options(sqlite3_static PRIVATE -w)

add_library(server_core STATIC
    src/data/SQLiteReader.cpp
    src/validation/DataValidator.cpp
    src/indexing/SegmentTree.cpp
    src/cache/SymbolCacheManager.cpp
    src/simulation/KNNMicrostructureEngine.cpp
    src/simulation/SimulationEngine.cpp
    src/arrow/ArrowIPCBuilder.cpp
    src/http/HttpServer.cpp
)
target_link_libraries(server_core PUBLIC sqlite3_static)

add_executable(simulator_server src/main_server.cpp)
target_link_libraries(simulator_server PRIVATE server_core)

enable_testing()
add_executable(test_server_engine tests/test_server_engine.cpp)
target_link_libraries(test_server_engine PRIVATE server_core)
add_test(NAME test_server_engine COMMAND test_server_engine)
