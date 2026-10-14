# Checkpoint — ARM64 baseline APK

Updated 2026-10-14. The Linux native build and ARM64 debug APK assembly are
complete. Final signing, ABI, dependency-closure and 16 KiB package verification
passed. The artifact below passed the final committed-state assembly and audit. No device installation, client import or Thor
runtime qualification has happened. No gameplay module has been integrated.

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

## Native source revisions

- App/fork branch: `Swamisama/pocket-realm`, `vanilla-plus/baseline-setup`.
  Exact app build revision: `f736930745683a918078ea156de43827b72b430d` (later checkpoint-only documentation does not change the artifact inputs).
- CMaNGOS: `15d9293e772b9a825fc1d13be11554680b567e7d` (Swamisama fork).
- Playerbots: `c66302ac8778ead1c6be21fb01091f203df8b7e0` (Swamisama fork).
- Classic-DB: `be1a5206bedccc8dc088b7c79dae31fcf3dbbfce`.
- Previous planning checkpoint: `96feb040e043110669069cd7eaefcf0fd09c753c`,
  tag `checkpoint/thor-apk-plan-2026-10-14`. It remains historical evidence.

The repaired core/bot commits descend from the available replacement pins
`1d2c0260` / `9c3bf0d1`; they retain the Android lifecycle and Playerbots.
The unavailable original app-native pins were not restored or substituted
with a general upstream core. Socket completion ownership/error handling,
reactor exception handling, the Android allocator purge and optional LLM
wiring were restored in our forks. The legacy facade now implements the
shared first-tick listener gate and refuses false readiness on failure.

## Verified build results

- Real Linux NDK/CMake/Ninja discovery, shell tools and bounded builds; no
  misleading `.exe` aliases, MSYS2 requirement or Linux junction emulation.
- OpenSSL 3.4.3, Boost 1.86.0, SQLite 3.46.1 and Connector/C built for ARM64.
- Login/world with Playerbots, the complete legacy lifecycle facade, four
  extractors, packaging/Wine/display bridges, proot/talloc and the Rust tweak
  patcher compiled and staged. Vortek and Gladio guests were also rebuilt.
- MariaDB 12.3.2, llama.cpp and Box64/Wine dependency providers recovered from
  the SHA-256-pinned upstream 0.103.0 release. These are hash-verified provider
  binaries, not claimed as local builds. The fork's core/extractors/patcher
  were compiled locally. See `docs/LINUX_ARM64_BUILD.md` for that boundary.
- Final ELF inspection caught two recovered helpers and the 32-bit proot
  loader with 4 KiB segments. The original helper ABIs were rebuilt from
  retained, pinned BSD source and the loader relinked for 16 KiB pages; no
  alignment check was bypassed. Helper export sets and rebuild hashes pass.
- All 414 migration records retain their original order, SQL identity/size
  and compressed hashes. Seed revalidation reproduced the historical four
  transcript digests exactly, resolved all 1,109,982 cached item references,
  and checked loader/schema contracts and Vanilla equipment bounds. Loader
  and capture hashes now guard reuse. Fresh device recapture is unqualified.
- Full pristine-source Python CI selection: **678 passed, 23 skipped, eight
  unchanged upstream deselections**, zero failures/errors. Remaining skips
  are 19 external LLM authoring-harness cases, two Windows compiler cases and
  two device-only expectations. No new skips/exclusions were added. Earlier
  runs overlapping native overlays are superseded by this pristine rerun.
- Android JVM: **1,143 tests**, zero failures/errors/skips; detekt passes.
- Native host tests: target fence and legacy first-tick/reset gate pass (2/2).
- Normal Gradle source/provenance, SQL, provider, ABI, hash and packaging gates
  pass. APK signature, ZIP alignment, all 51 packaged ELF ABI/16 KiB checks,
  exact locked artifact bytes and Box64's packaged glibc closure pass.

ARM64/MySQL, extractors, patcher, display and helper binary provenance comes
from actual builds. Other realm lanes' binary hashes remain historical;
source-field refreshes do not qualify those other lanes. The old full-build
failure counts are retained in Git history and logs, not the current result.

## Artifact and build evidence

APK: `android/app/build/outputs/apk/debug/app-debug.apk`.

- APK SHA-256: a11e898607dc71ea79553f63f13631963ce241257453d28141ee81d7135092b8
- Signing certificate SHA-256: 36a010b4f085fec8f5546924716f077209d1d776d45f7eab778865bdae9d13a8
- Package: `com.pocketrealm`, debug/test signature, ARM64 native lane.

Toolchain: Ubuntu OpenJDK 17.0.20.1, Python 3.12.3, SDK API 35, build-tools
36.0.0, NDK 30.0.15729638, SDK CMake 4.1.2/Ninja 1.12.1, Gradle 9.5.0 and
AGP 9.3.1. Exact compiler/Rust and source details are in the verification
report and generated native provenance. Build dependencies are retained in
`requirements-linux-build.txt` and pinned source/provider recipes.

Repeatable commands and the clean-build script are documented in
[LINUX_ARM64_BUILD.md](docs/LINUX_ARM64_BUILD.md). The complete clean script is
implemented; components and clean rebuild comparisons were exercised during
qualification, not a second complete clean pipeline.

Evidence: `../baseline/logs/linux-realm-final-arm64.log`,
`linux-extractors-arm64.log`, `linux-final-wrapper.log`,
`linux-apk-verification-final.log`, `linux-pytest-pristine.xml`, `linux-jvm-tests.log`,
`linux-jvm-summary.json`, `linux-native-tests.log`, `linux-seed-revalidation-final.log`,
`linux-display-rebuild.log` and `linux-runtime-helpers-rebuild.log`.
`output/arm64-baseline-verification.json` is the final machine-readable report.
Caches, APKs, logs, keys and generated provider/build artifacts stay local.
No original Blizzard client or extracted client assets were downloaded,
committed or bundled.

## What remains for Thor installation (outside this build task)

Identify the device/model/build/ABI/page size and available storage. If
`com.pocketrealm` is already installed, obtain and verify an off-device save
backup and preserve the installed APK before any replacement. Check signing
compatibility; never uninstall an existing app to evade a signature mismatch
without a verified save/restore plan.

Install the verified APK only as a separate authorized device task. Import
only the user's legitimate WoW 1.12.1 build 5875 through the managed flow.
Qualify startup, login, character creation, movement/combat, controllers,
Playerbots, offline play, clean stop/restart, saves and restoration. Measure
memory/CPU/battery/thermal behavior and bot tiers. Host package verification
is not this on-device qualification. Do not create `baseline-working` until
those device checks pass.

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
