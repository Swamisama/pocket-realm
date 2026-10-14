# Linux ARM64 baseline build

This pipeline builds the Android app on Linux. It does not install the app,
access saves or import a game client. Gameplay modules remain deferred.

## Prerequisites

Use an x86_64 Linux host with JDK 17, Python 3.12, a C/C++ compiler, Perl,
Make, Git, Rust/Cargo/rustup, zstd, and access to a running Docker daemon.
Install Android SDK platform 35, build-tools 36.0.0, NDK 30.0.15729638 and
SDK CMake 4.1.2. Accept the SDK licenses. Set `ANDROID_HOME` to the SDK root
and `JAVA_HOME` to JDK 17. No Windows tool aliases or MSYS2 are used on Linux.

```bash
git clone --recursive --branch vanilla-plus/baseline-setup \
  https://github.com/Swamisama/pocket-realm.git
cd pocket-realm
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-linux-build.txt
export ANDROID_HOME="$HOME/Android/Sdk"
# Set JAVA_HOME if your distribution's default differs from the script.
bash scripts/build_linux_arm64.sh
```

The default native concurrency is two workers; `POCKET_BUILD_JOBS` explicitly
overrides it. The qualification build started with two and used four for the
last realm rebuild after observing available memory. Avoid overlapping Gradle
invocations in this checkout. A fresh native build takes substantially longer
than an incremental APK assembly.

`bash scripts/build_linux_arm64.sh --clean` removes only the listed generated
ARM native build trees before rebuilding. Provider/source archives, dependency
prefixes, imported clients, saves and backups are preserved. This clean entry
point is implemented; the qualification run executed its component commands
and rebuild checks individually, not a second complete `--clean` run.

## Pipeline and provenance

The script fetches hash-pinned source/provider archives, verifies source pins,
builds OpenSSL 3.4.3, Boost 1.86.0 and SQLite 3.46.1, then builds the MySQL
connector and the login/world/legacy lifecycle libraries with Playerbots.
It builds/stages the four extractors, packaging and Wine bridges, display
bridges, proot/talloc, the aligned original shared-memory/semaphore helper
ABIs, and the Rust client patcher. It stages all 414 unchanged SQL migrations.
Gradle builds/stages the pinned Vortek/Gladio guests and renderer catalogs.

The original MariaDB 12.3.2 Termux package URLs return 404. Instead of changing
the database version or historical hashes, `tools/stage_baseline_providers.py`
recovers dependency providers from upstream's immutable 0.103.0 ARM APK:
SHA-256 `09d5fde0d9ba9a58331ce6ecca1b03bf7b02e586304058063d6253e9542b7144`.
MariaDB executables, closure and bootstrap and the five llama.cpp libraries
must match the existing lockfiles. Wine/Box64 runtime assets retain their
provider hashes. This is dependency recovery, not a local MariaDB/llama/Wine
compilation, and it never imports upstream core, extractor or patcher binaries.
The two old 4 KiB helper binaries are rebuilt from retained, pinned BSD source;
export checks preserve their original eight-symbol ABIs. The 32-bit proot
loader is also relinked for 16 KiB pages. Full licenses ship in the APK.

`schemas/display-runtime-lockfile-arm64-v8a.json` retains historical Windows
pins and adds actual Linux build pins. The Gladio/VirGL servers and SQLite
ARM archive were checked against clean, byte-identical rebuilds. Binary pins
for ARM MySQL, extractors, patcher and helpers come from actual builds.
Other realm lanes' binary hashes remain historical; refreshed source fields
in those lockfiles do not qualify those lanes.

The seed-cache audit replays the exact captured manifest, proves all 414
records and four transcript digests unchanged, checks all 1,109,982 cached
item references and Vanilla equipment bounds, and binds future reuse to the
loader and capture hashes. Run `python tools/revalidate_seed_cache.py` only
for a reviewed source-only repin. It fails on changed migration records or
seed output. A fresh device cache capture remains outside host qualification.

## Recording a rebuild on another host/path

Native binaries can differ when the build path or toolchain changes. Builders
regenerate binary lockfiles from the actual outputs. Final verification
requires a clean, committed source tree: review and commit those generated
lockfile changes, then rerun the assembly command below and
`python tools/verify_arm64_apk.py`. This records a concrete build revision;
source-only lockfile regeneration cannot substitute for compilation. The full
script intentionally fails final verification when those inputs are uncommitted.

## Checks and outputs

The script runs repository/source checks, the exact CI Python selection
(`scripts/test_python_ci.py`, retaining its eight existing exclusions), two
native host tests, JVM unit tests and detekt. All normal Gradle provenance,
provider, ABI, source, SQL, hash and packaging gates remain enabled.

Final assembly, from `android/`:

```bash
bash ./gradlew :app:assembleDebug -PpocketAbi=arm64-v8a -PpocketLane=full
```

APK: `android/app/build/outputs/apk/debug/app-debug.apk`.
Run `python tools/verify_arm64_apk.py` to verify its local signing certificate,
ZIP alignment, every packaged ELF's ABI/16 KiB compatibility, exact locked
artifact bytes and namespace-aware dependency closure, including Box64's
packaged glibc rootfs. It also checks for client assets and records exact
source/toolchain revisions in `output/arm64-baseline-verification.json`.

Logs default to `output/linux-arm64-logs/`; `POCKET_BUILD_LOGS` changes the
location. This qualification's individual logs live in `../baseline/logs/`.
`CHECKPOINT.md` records the final artifact and qualification boundary. No Thor
installation, client import or on-device runtime qualification is claimed.
