#pragma once

#include "server/cache/SymbolCacheManager.hpp"
#include <string>
#include <memory>

namespace server::http {

class HttpServer {
public:
    HttpServer(std::shared_ptr<cache::SymbolCacheManager> cacheManager, uint16_t port = 8080);

    void start();
    void stop();

private:
    std::shared_ptr<cache::SymbolCacheManager> cache_manager_;
    uint16_t port_;
    bool running_;
};

} // namespace server::http
