#pragma once

#include <queue>
#include <mutex>
#include <condition_variable>
#include <cstddef>

namespace simulator::concurrency {

template <typename T>
class BoundedQueue {
public:
    explicit BoundedQueue(size_t capacity) : capacity_(capacity), closed_(false) {}

    void push(T item) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_push_.wait(lock, [this]() { return queue_.size() < capacity_ || closed_; });
        if (closed_) return;
        queue_.push(std::move(item));
        cv_pop_.notify_one();
    }

    bool pop(T& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        cv_pop_.wait(lock, [this]() { return !queue_.empty() || closed_; });
        if (queue_.empty() && closed_) {
            return false;
        }
        item = std::move(queue_.front());
        queue_.pop();
        cv_push_.notify_one();
        return true;
    }

    void close() {
        std::lock_guard<std::mutex> lock(mutex_);
        closed_ = true;
        cv_push_.notify_all();
        cv_pop_.notify_all();
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.size();
    }

    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }

private:
    size_t capacity_;
    std::queue<T> queue_;
    mutable std::mutex mutex_;
    std::condition_variable cv_push_;
    std::condition_variable cv_pop_;
    bool closed_;
};

} // namespace simulator::concurrency
