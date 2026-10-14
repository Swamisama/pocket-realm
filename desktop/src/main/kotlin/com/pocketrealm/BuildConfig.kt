package com.pocketrealm

/**
 * Desktop twin of the AGP-generated Android BuildConfig fields consumed by
 * the shared server contract. On Android these are baked from the reviewed
 * realm-runtime lane lockfile at build time; here they are pinned to
 * schemas/realm-runtime-lockfile-sqlite-win.json (written by
 * `python tools/build_win_realm_runtime.py --write-lockfile` after a lane
 * rebuild).
 *
 * tests/test_win_lockfile.py recomputes the id from the lockfile with the
 * SAME formula the Android build uses (prefix + backend + commit prefixes
 * + the world DLL digest prefix) and fails on drift — an unpinned id must
 * fail the shared staleness telltale rather than silently pass.
 */
object BuildConfig {
    const val NATIVE_RUNTIME_BUILD_ID: String =
        "win-x86_64-sqlite-cmangos-15d9293e-playerbots-c66302ac-633d89dfb70d"

    const val NATIVE_CMANGOS_COMMIT: String =
        "15d9293e772b9a825fc1d13be11554680b567e7d"

    const val NATIVE_PLAYERBOTS_COMMIT: String =
        "c66302ac8778ead1c6be21fb01091f203df8b7e0"
}
