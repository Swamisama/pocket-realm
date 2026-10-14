#include "first_tick_fence.h"
#include <chrono>
#include <thread>

int main()
{
    pocket_legacy_first_tick_reset();
    if (pocket_world_first_tick_wait(1)) return 1;
    std::thread tick([] {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
        pocket_legacy_first_tick_complete();
    });
    const bool ready = pocket_world_first_tick_wait(1000) != 0;
    tick.join();
    if (!ready) return 2;
    // A completed prior run must never satisfy the next startup's gate.
    pocket_legacy_first_tick_reset();
    if (pocket_world_first_tick_wait(1)) return 3;
    pocket_legacy_first_tick_complete();
    if (!pocket_world_first_tick_wait(1)) return 4;
    return 0;
}
