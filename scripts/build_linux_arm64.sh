#!/usr/bin/env bash
# Full baseline pipeline; never touches installed apps, saves or client imports.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/30.0.15729638"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
export POCKET_BUILD_JOBS="${POCKET_BUILD_JOBS:-2}"
# Use the prepared project venv or the shared baseline venv. Both supply the
# real Python executable Gradle's Exec tasks require.
if [[ -x .venv/bin/python ]]; then
    export PATH="$PWD/.venv/bin:$PATH"
elif [[ -x ../baseline/.venv/bin/python ]]; then
    export PATH="$PWD/../baseline/.venv/bin:$PATH"
fi
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmake/4.1.2/bin:$PATH"
command -v python >/dev/null
build_log_root="${POCKET_BUILD_LOGS:-$PWD/output/linux-arm64-logs}"
mkdir -p "$build_log_root"
run_stage() {
    local name="$1"; shift
    "$@" 2>&1 | tee "$build_log_root/$name.log"
}
if [[ "${1:-}" == "--clean" ]]; then
    # Only generated native build trees, never dependency sources or user data.
    python - <<'PY'
from pathlib import Path
import shutil
for name in ('.build-arm64', '.build-aarch64', '.build-o09-arm64-v8a',
             '.build-o11-arm64-v8a', '.build-vanilla-tweaks-arm64-v8a'):
    path = Path('native') / name
    if path.is_symlink():
        raise RuntimeError(f'refusing symlink build tree: {path}')
    if path.exists():
        shutil.rmtree(path)
PY
fi
run_stage hygiene python tools/check_repo.py
run_stage provider-sources python tools/fetch_linux_build_sources.py
run_stage provider-archives python tools/fetch_provider.py --no-extract
run_stage dependency-sources python scripts/fetch_native_deps.py
run_stage providers python tools/stage_baseline_providers.py
run_stage source-pins python tools/check_sources.py
run_stage dependencies python scripts/build_native.py --abi arm64-v8a openssl boost sqlite
run_stage realm python tools/build_o09_realm_runtime.py --abi arm64-v8a
run_stage extractors python tools/build_o11_extractors.py --abi arm64-v8a
run_stage packaging python tools/build_packaging.py --abi arm64-v8a
run_stage wine-bridge python tools/build_wine_spike.py --abi arm64-v8a
run_stage display python tools/build_xserver_winlator.py --abi arm64-v8a
run_stage proot python tools/build_proot.py --abi arm64-v8a
run_stage runtime-helpers python tools/build_runtime_helpers.py
run_stage rust-target rustup target add aarch64-linux-android
run_stage tweak python tools/build_vanilla_tweaks.py --abi arm64-v8a
run_stage migrations python tools/stage_database_migrations.py --abi arm64-v8a
run_stage python-ci python scripts/test_python_ci.py
run_stage native-test-configure cmake -S native/realm-runtime/tests -B native/.build-host/realm-tests -G Ninja
run_stage native-test-build cmake --build native/.build-host/realm-tests --parallel "$POCKET_BUILD_JOBS"
run_stage native-tests ctest --test-dir native/.build-host/realm-tests --output-on-failure
# Serialize all Gradle invocations in this checkout.
(
    cd android
    run_stage jvm bash ./gradlew :app:testDebugUnitTest :app:detekt -PpocketAbi=x86_64 -PpocketLane=full --console=plain --no-daemon --max-workers=2
    run_stage apk bash ./gradlew :app:assembleDebug -PpocketAbi=arm64-v8a -PpocketLane=full --console=plain --no-daemon --max-workers=2
)
run_stage verify python tools/verify_arm64_apk.py
