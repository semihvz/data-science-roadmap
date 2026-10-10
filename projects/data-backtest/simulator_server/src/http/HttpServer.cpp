#include "server/http/HttpServer.hpp"
#include "server/simulation/SimulationEngine.hpp"
#include "server/simulation/KNNMicrostructureEngine.hpp"
#include "server/arrow/ArrowIPCBuilder.hpp"
#include <iostream>
#include <sstream>
#include <thread>
#include <chrono>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

namespace server::http {

HttpServer::HttpServer(std::shared_ptr<cache::SymbolCacheManager> cacheManager, uint16_t port)
    : cache_manager_(cacheManager), port_(port), running_(false) {}

void HttpServer::start() {
    int serverFd = socket(AF_INET, SOCK_STREAM, 0);
    if (serverFd < 0) {
        throw std::runtime_error("HttpServer: Failed to create socket");
    }

    int opt = 1;
    setsockopt(serverFd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port_);

    if (bind(serverFd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        close(serverFd);
        throw std::runtime_error("HttpServer: Failed to bind to port " + std::to_string(port_));
    }

    if (listen(serverFd, 10) < 0) {
        close(serverFd);
        throw std::runtime_error("HttpServer: Failed to listen");
    }

    running_ = true;
    std::cout << "[HTTP SERVER] On-Demand Arrow Simulation Server listening on http://localhost:" << port_ << "/api/v1/simulate" << std::endl;

    while (running_) {
        sockaddr_in clientAddr{};
        socklen_t addrLen = sizeof(clientAddr);
        int clientSocket = accept(serverFd, (struct sockaddr*)&clientAddr, &addrLen);
        if (clientSocket < 0) continue;

        std::thread([this, clientSocket]() {
            char buffer[2048] = {0};
            ssize_t bytesRead = read(clientSocket, buffer, sizeof(buffer) - 1);
            if (bytesRead <= 0) {
                close(clientSocket);
                return;
            }

            std::string reqStr(buffer);

            // Endpoint 1: List available dataset symbols
            if (reqStr.find("/api/v1/symbols") != std::string::npos) {
                auto symbols = cache_manager_->getAvailableSymbols();
                std::ostringstream jsonSS;
                jsonSS << "[";
                for (size_t i = 0; i < symbols.size(); ++i) {
                    jsonSS << "\"" << symbols[i] << "\"";
                    if (i + 1 < symbols.size()) jsonSS << ", ";
                }
                jsonSS << "]";
                std::string body = jsonSS.str();

                std::ostringstream headers;
                headers << "HTTP/1.1 200 OK\r\n"
                        << "Content-Type: application/json\r\n"
                        << "Content-Length: " << body.size() << "\r\n"
                        << "Access-Control-Allow-Origin: *\r\n"
                        << "Connection: close\r\n\r\n"
                        << body;
                std::string resStr = headers.str();
                write(clientSocket, resStr.data(), resStr.size());
                close(clientSocket);
                return;
            }

            // Endpoint 2: Synthetic 1-Second OHLCV Candles (/api/v1/candles1s)
            if (reqStr.find("/api/v1/candles1s") != std::string::npos) {
                std::string symbol = "BTCUSDT";
                size_t max1m = 10000;
                int64_t startTs = 0;
                int64_t endTs = std::numeric_limits<int64_t>::max();

                size_t symPos = reqStr.find("symbol=");
                if (symPos != std::string::npos) {
                    size_t ampPos = reqStr.find_first_of("& ", symPos);
                    symbol = reqStr.substr(symPos + 7, ampPos - (symPos + 7));
                }
                size_t maxPos = reqStr.find("max_candles=");
                if (maxPos != std::string::npos) {
                    size_t ampPos = reqStr.find_first_of("& ", maxPos);
                    max1m = std::stoul(reqStr.substr(maxPos + 12, ampPos - (maxPos + 12)));
                }
                size_t startPos = reqStr.find("start_ts=");
                if (startPos != std::string::npos) {
                    size_t ampPos = reqStr.find_first_of("& ", startPos);
                    startTs = std::stoll(reqStr.substr(startPos + 9, ampPos - (startPos + 9)));
                }
                size_t endPos = reqStr.find("end_ts=");
                if (endPos != std::string::npos) {
                    size_t ampPos = reqStr.find_first_of("& ", endPos);
                    endTs = std::stoll(reqStr.substr(endPos + 7, ampPos - (endPos + 7)));
                }

                auto cached = cache_manager_->getOrLoadSymbol(symbol);

                // Filter 1m candles by date range BEFORE expanding to 1s
                std::vector<size_t> matchedIndices;
                matchedIndices.reserve(cached->candles.size());
                for (size_t i = 0; i < cached->candles.size(); ++i) {
                    int64_t ts = cached->candles.timestamps[i];
                    if (ts >= startTs && ts <= endTs) {
                        matchedIndices.push_back(i);
                    }
                }

                if (max1m > 0 && startTs == 0 && endTs == std::numeric_limits<int64_t>::max() && matchedIndices.size() > max1m) {
                    matchedIndices.resize(max1m);
                }

                uint32_t numRows = static_cast<uint32_t>(matchedIndices.size() * 60);
                uint32_t numCols = 6;

                std::ostringstream ss(std::ios::binary);
                ss.write("ARROW_1S_STRM", 12);
                ss.write(reinterpret_cast<const char*>(&numRows), sizeof(numRows));
                ss.write(reinterpret_cast<const char*>(&numCols), sizeof(numCols));

                static simulation::KNNMicrostructureEngine knnEngine;

                std::vector<int64_t> vecTs(numRows);
                std::vector<double> vecO(numRows);
                std::vector<double> vecH(numRows);
                std::vector<double> vecL(numRows);
                std::vector<double> vecC(numRows);
                std::vector<double> vecV(numRows);

                uint32_t seed = 0;
                double noise = 0.0;

                size_t seedPos = reqStr.find("seed=");
                if (seedPos != std::string::npos) {
                    size_t ampPos = reqStr.find_first_of("& ", seedPos);
                    seed = std::stoul(reqStr.substr(seedPos + 5, ampPos - (seedPos + 5)));
                }
                size_t noisePos = reqStr.find("noise=");
                if (noisePos != std::string::npos) {
                    size_t ampPos = reqStr.find_first_of("& ", noisePos);
                    noise = std::stod(reqStr.substr(noisePos + 6, ampPos - (noisePos + 6)));
                }

                for (size_t m = 0; m < matchedIndices.size(); ++m) {
                    size_t i = matchedIndices[m];
                    int64_t baseTs = cached->candles.timestamps[i];
                    auto subBars = knnEngine.generate1SecondSubBars(
                        cached->candles.open[i], cached->candles.high[i], cached->candles.low[i],
                        cached->candles.close[i], cached->candles.volume[i],
                        seed, noise
                    );
                    for (size_t s = 0; s < 60; ++s) {
                        size_t idx = m * 60 + s;
                        vecTs[idx] = baseTs + static_cast<int64_t>(s);
                        vecO[idx] = subBars[s].open;
                        vecH[idx] = subBars[s].high;
                        vecL[idx] = subBars[s].low;
                        vecC[idx] = subBars[s].close;
                        vecV[idx] = subBars[s].volume;
                    }
                }

                ss.write(reinterpret_cast<const char*>(vecTs.data()), numRows * sizeof(int64_t));
                ss.write(reinterpret_cast<const char*>(vecO.data()), numRows * sizeof(double));
                ss.write(reinterpret_cast<const char*>(vecH.data()), numRows * sizeof(double));
                ss.write(reinterpret_cast<const char*>(vecL.data()), numRows * sizeof(double));
                ss.write(reinterpret_cast<const char*>(vecC.data()), numRows * sizeof(double));
                ss.write(reinterpret_cast<const char*>(vecV.data()), numRows * sizeof(double));

                std::string binaryStream = ss.str();

                std::ostringstream headers;
                headers << "HTTP/1.1 200 OK\r\n"
                        << "Content-Type: application/vnd.apache.arrow.stream\r\n"
                        << "Content-Length: " << binaryStream.size() << "\r\n"
                        << "Access-Control-Allow-Origin: *\r\n"
                        << "Connection: close\r\n\r\n";

                std::string headerStr = headers.str();
                write(clientSocket, headerStr.data(), headerStr.size());

                size_t totalBytes = binaryStream.size();
                size_t writtenBytes = 0;
                const char* dataPtr = binaryStream.data();
                while (writtenBytes < totalBytes) {
                    size_t chunkSize = std::min(size_t(64 * 1024 * 1024), totalBytes - writtenBytes);
                    ssize_t res = write(clientSocket, dataPtr + writtenBytes, chunkSize);
                    if (res <= 0) break;
                    writtenBytes += static_cast<size_t>(res);
                }
                close(clientSocket);
                return;
            }

            // Endpoint 3: On-Demand Arrow Simulation (/api/v1/simulate)

            std::string symbol = "BTCUSDT";

            double sl = 0.005;
            double rr = 3.0;

            size_t symPos = reqStr.find("symbol=");
            if (symPos != std::string::npos) {
                size_t ampPos = reqStr.find_first_of("& ", symPos);
                symbol = reqStr.substr(symPos + 7, ampPos - (symPos + 7));
            }

            size_t slPos = reqStr.find("sl=");
            if (slPos != std::string::npos) {
                size_t ampPos = reqStr.find_first_of("& ", slPos);
                sl = std::stod(reqStr.substr(slPos + 3, ampPos - (slPos + 3)));
            }

            std::string resolution = "1m";
            size_t resPos = reqStr.find("resolution=");
            if (resPos != std::string::npos) {
                size_t ampPos = reqStr.find_first_of("& ", resPos);
                resolution = reqStr.substr(resPos + 11, ampPos - (resPos + 11));
            }

            try {
                auto startSim = std::chrono::high_resolution_clock::now();
                auto cached = cache_manager_->getOrLoadSymbol(symbol);

                simulation::SimParams params;
                params.sl_percent = sl;
                params.risk_reward_ratio = rr;
                params.tp_percent = sl * rr;
                params.resolution = resolution;
                params.threads = 8;

                auto trades = simulation::SimulationEngine::runInMemorySimulation(cached, params);
                auto endSim = std::chrono::high_resolution_clock::now();
                double simSec = std::chrono::duration<double>(endSim - startSim).count();

                // Serialize to binary Arrow IPC Stream
                std::string binaryStream = arrow::ArrowIPCBuilder::serializeToBinaryIPCStream(trades);

                // Build HTTP Response Header
                std::ostringstream responseHeaders;
                responseHeaders << "HTTP/1.1 200 OK\r\n"
                                << "Content-Type: application/vnd.apache.arrow.stream\r\n"
                                << "Content-Length: " << binaryStream.size() << "\r\n"
                                << "X-Simulation-Time-Sec: " << simSec << "\r\n"
                                << "X-Total-Trades: " << trades.size() << "\r\n"
                                << "Access-Control-Allow-Origin: *\r\n"
                                << "Connection: close\r\n\r\n";

                std::string headerStr = responseHeaders.str();
                write(clientSocket, headerStr.data(), headerStr.size());

                size_t totalBytes = binaryStream.size();
                size_t writtenBytes = 0;
                const char* dataPtr = binaryStream.data();
                while (writtenBytes < totalBytes) {
                    size_t chunkSize = std::min(size_t(64 * 1024 * 1024), totalBytes - writtenBytes);
                    ssize_t res = write(clientSocket, dataPtr + writtenBytes, chunkSize);
                    if (res <= 0) break;
                    writtenBytes += static_cast<size_t>(res);
                }
            } catch (const std::exception& ex) {
                std::string errBody = "{\"error\": \"" + std::string(ex.what()) + "\"}";
                std::ostringstream errHeaders;
                errHeaders << "HTTP/1.1 400 Bad Request\r\n"
                           << "Content-Type: application/json\r\n"
                           << "Content-Length: " << errBody.size() << "\r\n"
                           << "Connection: close\r\n\r\n"
                           << errBody;
                std::string errStr = errHeaders.str();
                write(clientSocket, errStr.data(), errStr.size());
            }

            close(clientSocket);
        }).detach();
    }

    close(serverFd);
}

void HttpServer::stop() {
    running_ = false;
}

} // namespace server::http
