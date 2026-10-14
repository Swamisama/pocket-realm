# Pocket Realm Vanilla+

This is Swamisama's development fork for the AYN Thor Max. The immediate
target is an ARM64 Android APK built on Linux, followed by a measured device
baseline. Gameplay modules and balancing integration remain deferred until
that baseline works. This branch is not yet a qualified APK release.

## Source ownership and lineage

- App: https://github.com/Swamisama/pocket-realm
- Android CMaNGOS fork: https://github.com/Swamisama/mangos-classic
- Playerbots fork: https://github.com/Swamisama/playerbots
- Starting app revision: `203b65b07056312dd23bcb861534a6bda261fb7d`
  from https://github.com/puzzled-pancake/pocket-realm.

The original app revision pins two commits absent from its public native
mirrors. This fork deliberately selects available revisions from those same
Pocket Realm mirrors, retaining their Android adaptations rather than
substituting the general upstream CMaNGOS core:

| Component | Unavailable original pin | Selected fork pin |
|---|---|---|
| CMaNGOS | `ce83805d48f9c98b2af617096be5347acb8a1f17` | `1d2c026013ed9d75f4449b1dcdbfe4900c08747c` |
| Playerbots | `7e2cd2fbbbb4eaa3e1696ee80e9bf8e170b6256d` | `9c3bf0d15a8618a9c61181a2cb67b81e65b0b92a` |
| Classic-DB | `be1a5206bedccc8dc088b7c79dae31fcf3dbbfce` | unchanged |

These are new, explicit source baselines. Full equivalence with the missing
revisions cannot be established. Both selected revisions contain the published
Pocket Realm Android compilation patches; the CMaNGOS revision also contains
its embedded lifecycle API. The last two commits in each mirror only add
funding metadata.

## What has been verified

- `tools/check_sources.py` passes against the selected commits and the
  SHA-256-verified Wine/SQLite provider cache.
- All MySQL realm/core and Playerbots build overlays apply to disposable clones
  of the selected sources. Restoring the core leaves no tracked diff.
- All 414 migration entries retain their original paths, order, uncompressed
  SQL bytes, sizes and compressed asset hashes. Only `source_commits` changes
  in `schemas/database-migrations.json`.
- The migration host-parity tests pass, including refusal of changed SQL.

The migration builder now reproduces the original Windows filename order on
Linux. For existing SQL, it accepts a line-ending conversion only when the
result matches the already recorded SHA-256. Newly appended SQL uses LF.
This preserves existing migration identities; no ledger checks were disabled.

The realm lockfiles' source fields have been refreshed through the existing
`--write-lockfiles` entry point. Their binary artifact hashes still describe
upstream's last build. They do not prove that these selected sources have
been compiled. Complete native builds must regenerate and verify their own
artifact provenance before an APK can ship. Extractor and tweak artifact
lockfiles retain their original historical source/build records pending rebuild.

## Remaining build work

The first Python CI-selection run after source selection reports 635 passed,
18 failed, 26 skipped, 8 upstream deselections and 20 errors. The app JVM suite
passed 1,143 tests before the source selection; it must be rerun against this
fork's pins before treating that result as current.

The failures are retained and must be addressed, not excluded:

- The available native sources lack several stability and optional LLM changes
  expected by the app's tests: socket ownership/error handling, the embedded
  network exception guard, Android allocator purge, bot strategy/refusal wiring
  and guild speech adjustments.
- The SQLite CMake recipe referenced under ignored `native/.deps/` was never
  tracked. It needs a tracked, reproducible replacement.
- The SQLite seeder still assumes raw Windows SQL line endings and its cache
  provenance refers to the old migration-manifest identity. Revalidate its
  corpus and preserve the hash checks when making it host independent.
- The Windows desktop build identifier needs regeneration for the selected
  source pins. The Android ARM64 lane remains the target of this project.
- Native build tools need Linux host discovery and dependency bootstrapping.
  The full ARM runtime/provider and renderer staging must then pass unchanged
  packaging validation.

Do not install over an existing `com.pocketrealm` installation until its saved
realm is backed up and restore access has been checked. Device import, actual
play, shutdown/persistence, RAM, CPU, battery and bot limits remain unverified.

## Reproduction and updates

```bash
git clone --recursive https://github.com/Swamisama/pocket-realm.git
cd pocket-realm
git submodule status
python3 tools/check_repo.py
# Populate the two hash-checked provider archives before check_sources:
python3 tools/fetch_provider.py --no-extract
python3 tools/check_sources.py
```

The current full APK task remains:

```bash
cd android
bash ./gradlew :app:assembleDebug -PpocketAbi=arm64-v8a -PpocketLane=full
```

It requires complete native staging, so the above is not yet a clean-host
end-to-end build recipe. Preserve the GPL licenses and third-party notices
when distributing builds. Original Blizzard client assets remain user supplied
and outside this repository.
