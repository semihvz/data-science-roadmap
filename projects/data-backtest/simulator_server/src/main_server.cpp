#include "server/cache/SymbolCacheManager.hpp"
#include "server/http/HttpServer.hpp"
#include <iostream>
#include <csignal>
#include <memory>

std::shared_ptr<server::http::HttpServer> g_server;

void handleSignal(int signal) {
    std::cout << "\n[SERVER] Signal " << signal << " received. Stopping Arrow Simulation Server..." << std::endl;
    if (g_server) g_server->stop();
    exit(0);
}

int main(int argc, char* argv[]) {
    std::string rawDataDir = "../raw_data";
    uint16_t port = 8080;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--data-dir" && i + 1 < argc) rawDataDir = argv[++i];
        else if (arg == "--port" && i + 1 < argc) port = static_cast<uint16_t>(std::stoi(argv[++i]));
    }

    std::signal(SIGINT, handleSignal);
    std::signal(SIGTERM, handleSignal);

    std::cout << "==========================================================" << std::endl;
    std::cout << "   ON-DEMAND BINANCE FUTURES ARROW SIMULATION SERVER v1.0  " << std::endl;
    std::cout << "==========================================================" << std::endl;
    std::cout << "Raw Data Directory: " << rawDataDir << std::endl;
    std::cout << "HTTP Server Port:   " << port << std::endl;

    auto cacheManager = std::make_shared<server::cache::SymbolCacheManager>(rawDataDir, 5);
    g_server = std::make_shared<server::http::HttpServer>(cacheManager, port);

    g_server->start();
    return 0;
}
