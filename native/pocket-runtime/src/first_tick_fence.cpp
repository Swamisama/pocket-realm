#include "first_tick_fence.h"
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <mutex>

namespace {
std::atomic<bool> completed{false};
std::mutex mutex;
std::condition_variable changed;
}

extern "C" void pocket_legacy_first_tick_reset()
{
    std::lock_guard<std::mutex> lock(mutex);
    completed.store(false, std::memory_order_release);
}

extern "C" void pocket_legacy_first_tick_complete()
{
    if (completed.load(std::memory_order_acquire))
        return;
    {
        std::lock_guard<std::mutex> lock(mutex);
        completed.store(true, std::memory_order_release);
    }
    changed.notify_all();
}

extern "C" int pocket_world_first_tick_wait(unsigned int timeout_ms)
{
    std::unique_lock<std::mutex> lock(mutex);
    return changed.wait_for(lock, std::chrono::milliseconds(timeout_ms),
        [] { return completed.load(std::memory_order_acquire); }) ? 1 : 0;
}
