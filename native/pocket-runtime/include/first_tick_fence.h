#pragma once

#if defined(__GNUC__)
#define POCKET_LEGACY_HIDDEN __attribute__((visibility("hidden")))
#else
#define POCKET_LEGACY_HIDDEN
#endif
extern "C" POCKET_LEGACY_HIDDEN void pocket_legacy_first_tick_reset();
extern "C" POCKET_LEGACY_HIDDEN void pocket_legacy_first_tick_complete();
extern "C" POCKET_LEGACY_HIDDEN int pocket_world_first_tick_wait(unsigned int timeout_ms);
