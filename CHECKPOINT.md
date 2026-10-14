# Checkpoint — path to an APK on the AYN Thor Max

Recorded 2026-10-14. This is a development checkpoint, **not** a working-build
or device-qualification tag. No APK exists yet and no device installation has
been attempted. No gameplay module has been merged.

## Agreed feature scope

| Feature | Commitment |
|---|---|
| Full Balancing | Required. Include the entire implementation across every affected class: spells, talents/resources, books/discovery, SQL and client patches. |
| Balancing and bots | Shared balancing changes are acceptable. Bots must remain functional, but do not need to learn or use the extra spells. Human-only spell isolation is no longer a requirement. Test compatibility before adding exceptions or AI changes. |
| Hardcore | Required in the feature build. Preserve bot resurrection. Player challenge activation/default rules still need to be chosen; availability does not mean automatically imposing permadeath on existing characters. |
| Transmog | Required in the feature build, including its 1.12 addon/UI and persistent appearances. |
| Dual Spec | Required in the feature build, including talents, action bars and persistence across restarts. |
| Classless | Optional future investigation; does not block either APK milestone. Keep any future Classless mode human-only and investigate coexistence with normal characters. |

Retain the original staged approach: first build and qualify a baseline APK,
then integrate the required features into a second APK. Hardcore, Transmog and
Dual Spec are committed deliverables for that feature build, not discarded
because they are absent from the first baseline. Full Balancing remains the
first requested gameplay module after the framework is qualified. Classless,
Skatecraft/Benilla and speculative QoL changes do not delay the baseline.

## Repositories and exact starting state

- App: https://github.com/Swamisama/pocket-realm
- Branch: `vanilla-plus/baseline-setup`
- Source immediately before this checkpoint: `1ceef2df1570929f1184a9f0100bb6162a3291d1`.
- CMaNGOS: https://github.com/Swamisama/mangos-classic,
  `1d2c026013ed9d75f4449b1dcdbfe4900c08747c`.
- Playerbots: https://github.com/Swamisama/playerbots,
  `9c3bf0d15a8618a9c61181a2cb67b81e65b0b92a`.
- Classic-DB: `be1a5206bedccc8dc088b7c79dae31fcf3dbbfce`.
- Original app lineage: `203b65b07056312dd23bcb861534a6bda261fb7d`.

The original native pins were unavailable upstream. Our explicitly selected
replacement pins clone successfully and retain the published Android
adaptations, but are not proven identical to the missing revisions. Native
fixes expected by the current app still need to be restored and validated.

## Verified progress

- Own app/core/bot forks created; a clean recursive clone succeeds.
- Linux toolchain installed/configured: JDK 17, Android API 35, build-tools
  36.0.0, NDK `30.0.15729638`, SDK CMake 4.1.2/Ninja, Python 3.12 and a local
  pytest environment. SDK: `$HOME/Android/Sdk`.
- Source verification and repository hygiene pass, rechecked for this checkpoint.
- Android JVM tests and detekt pass against our selected pins: **1,143 tests,
  zero failures/errors/skips**. This is a JVM result, not a native APK result.
- All MySQL core/bot build overlays apply to disposable source clones and
  restore without a tracked core diff.
- All **414** original SQL migration records retain their identities, ordering,
  SQL bytes and compressed hashes. Migration assets are staged. Linux/Windows
  filename order and SQL line-ending reproducibility were fixed without
  relaxing hash validation.
- Seventeen targeted migration/overlay/weather tests and seven desktop
  identity tests pass.
- Wine and SQLite provider archives were downloaded and hash verified. These
  caches are not the complete ARM64 runtime/provider set.
- Module framework and five requested module repositories were inspected and
  revisions recorded in [the feasibility report](docs/MODULE_FEASIBILITY.md).

## Current failures and limits

The last full Python CI-selection run was **635 passed, 18 failed, 20 errors,
26 skipped, 8 upstream deselections**. The desktop identity issue was fixed
after that run and its seven checks pass; no complete rerun has established a
new overall count. Do not describe the Python suite as passing.

Known work includes missing native stability/optional LLM changes, a missing
tracked SQLite CMake recipe, cross-platform raw-SQL handling in the SQLite
seeder, and seed-cache provenance revalidation after our source repin. Preserve
the existing test and provenance checks; resolve failures without adding skips.

Native scripts still assume MSYS2, `.exe` tools, Windows NDK paths and Windows
junctions. They have not been ported. The pinned source fields in realm
lockfiles were refreshed, but their binary hashes still describe upstream's
last build. Those records are not proof of compiled fork binaries.

The latest attempted ARM64 assembly failed at `:app:validateDatabaseRuntime`
because the MariaDB provider and supporting staging/provenance were incomplete.
SQL migrations have since been staged; the MariaDB binaries are still absent.
The ARM64 world library and debug APK are also absent at this checkpoint.

ADB currently reports **no connected device**. Whether the Thor already has
Pocket Realm installed and the location of the user's build-5875 client files
have not yet been supplied. No RAM/CPU/battery or bot-limit measurements exist.

## What remains before the first baseline APK reaches the Thor

1. **Repair source/build reproducibility.** Restore the tested native fixes
   missing from the available mirrors. Add the tracked SQLite recipe, correct
   SQL-seeder host handling and revalidate cache provenance against an unchanged
   corpus. Make the published checks pass, retaining only upstream's existing
   documented exclusions. Keep unrelated gameplay changes out of this stage.
2. **Port the native toolchain to Linux.** Implement real host tool discovery
   and a pinned dependency bootstrap for OpenSSL 3.4.3, Boost 1.86.0 and the
   other locked dependencies. Use the installed NDK/CMake versions and bounded
   build parallelism. Do not disguise Linux tools behind Windows `.exe` names.
3. **Build and stage the entire ARM64 runtime.** This includes the MariaDB
   Bionic provider/dependency closure, login/world with Playerbots, extractors,
   packaging/display bridges, client tweak tool, Box64/Wine runtime and renderer
   packages. Record actual build logs and regenerate source-to-binary provenance
   and artifact hashes from the resulting fork builds. Retain ABI, dependency
   closure, 16 KiB alignment, hash, runtime-provider and migration validation.
4. **Assemble and verify the locally signed debug APK.** From `android/`:
   `bash ./gradlew :app:assembleDebug -PpocketAbi=arm64-v8a -PpocketLane=full`.
   The expected output is `android/app/build/outputs/apk/debug/app-debug.apk`.
   Record its SHA-256, signing certificate and exact source revisions. Unit tests
   alone do not produce the required verified APK.
5. **Connect and protect the Thor.** Enable USB debugging and authorize ADB;
   identify the exact serial/model/Android build/ABI/page size/storage. Check
   for `com.pocketrealm` before installation. If present, obtain and verify a
   usable off-device save backup and preserve the original APK before replacing
   it. Review signing/package identity and update behavior for our fork; if a
   separate ID is necessary, audit services, providers and hardcoded names.
6. **Install and qualify.** Install the verified APK, import only the user's
   legitimate WoW 1.12.1 build 5875 through the managed import flow, then test
   realm startup, login, character creation, movement/combat, controller input,
   Playerbots, airplane-mode play, clean shutdown and character persistence.
   Collect logs/resource measurements. Mark/tag `baseline-working` only after
   these succeed. No Blizzard client assets enter source control or the APK.

The PC is the Linux build machine; running the Android app natively on the PC
is not a deliverable. There is no reliable APK delivery estimate until the
first complete native ARM64 build has been attempted.

## What remains for the required feature APK

1. Port a pinned module framework into our Android core, initially with all
   gameplay modules disabled. Its stock patch currently fails in `Player.cpp`
   and `World.cpp`, and lacks later required hooks. Wire modules into
   `pocket_world_runtime`, managed config paths, startup/shutdown and the
   append-only SQL ledger. Preserve Playerbots and the Android adaptations.
2. Integrate **full Balancing** with the normal shared spell data. Verify all
   affected classes, books, custom effects/procs, SQL and matching client patch.
   Check bots still fight/heal/buff and remain stable; unused extra spells are
   acceptable and do not require new bot rotations. Fix concrete incompatibilities
   if found. Do not build human-only spell isolation as a prerequisite.
3. Integrate **Hardcore, Transmog and Dual Spec** in small, reversible changes.
   Each needs actual build/config/SQL wiring, not just a CMake flag. Test bot
   resurrection/challenge eligibility, per-spec talents/action bars, cosmetic
   stat neutrality, addon/controller usability and save/reload behavior. Include
   the required managed client addon/patch installation and rollback support.
4. Package a second verified APK with the required features, back up the baseline
   realm, upgrade the Thor and repeat play/offline/persistence/restore checks.
   Keep a known-good baseline APK and save checkpoint as the rollback path.

## Resume point and evidence

Start with item 1 of the baseline list. The next work is Linux/native build
repair, not Classless or module merging.

Local environment and guarded assembly wrapper are in the adjacent
`../baseline/scripts/`; `../baseline/RUNBOOK.md` retains the original audit.
Evidence is in `../baseline/logs/`, including `fork-gradle-unit.log`,
`fork-pytest-ci.log`, `fork-overlay-audit.log`, `fork-clean-clone.log`,
`gradle-arm64-with-env.log` and `checkpoint-source-check.log`. Logs, provider
caches and installed SDK packages are local artifacts, not committed source.
