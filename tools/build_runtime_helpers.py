#!/usr/bin/env python3
"""Rebuild the original helper ABIs with 16 KiB LOAD alignment."""
from pathlib import Path
import hashlib
import json
import re
import sys
import subprocess
try:
    from tools import common
except ImportError:
    import common
from stage_wine_runtime import validate_elf_page_compatibility
ROOT = common.ROOT
SOURCE = ROOT / 'native/runtime-helpers'
STAGE = ROOT / 'native/.build-arm64/wine-staging/jniLibs'


def exports(binary, readelf):
    result = subprocess.check_output([str(readelf), '-sW', str(binary)], text=True)
    return sorted(set(m[1] for line in result.splitlines()
        if (m := re.search(r'\bFUNC\s+GLOBAL\s+DEFAULT\s+(?!UND\b)\d+\s+(\w+)', line))))


def main():
    sources = json.loads((SOURCE / 'SOURCES.json').read_text())
    for source in sources:
        for name, pin in source['files'].items():
            if common.sha256_file(SOURCE / source['component'] / name) != pin['sha256']:
                raise RuntimeError(f'helper source hash mismatch: {name}')
    ndk = common.resolve_android_ndk(prefer_version='30.0.15729638')
    cc = common.resolve_ndk_tool('clang', ndk)
    readelf = common.resolve_ndk_tool('llvm-readelf', ndk)
    STAGE.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for component, filename, source, extra, expected in (
        ('shmem', 'libpocket_android_shmem.so', 'shmem.c',
         ['-include', 'string.h', '-include', 'fcntl.h', f'-I{SOURCE / "shmem"}', f'-Wl,--version-script={SOURCE / "shmem/exports.txt"}', '-llog'],
         sorted(['shmget','shmat','shmdt','shmctl','libandroid_shmget','libandroid_shmat','libandroid_shmdt','libandroid_shmctl'])),
        ('sysv-sem', 'libpocket_android_sysv_semaphore.so', 'sys_sem.c',
         ['-D__USE_GNU', f'-I{SOURCE / "sysv-sem"}'],
         sorted(['semget','semop','semctl','semtimedop','libandroid_semget','libandroid_semop','libandroid_semctl','libandroid_semtimedop'])),
    ):
        target = STAGE / filename
        command = [str(cc), '--target=aarch64-linux-android26', '-O2', '-fPIC',
                   '-fstack-protector-strong', '-shared', '-Wl,-z,max-page-size=0x4000',
                   str(SOURCE / component / source), *extra, '-o', str(target)]
        subprocess.run(command, check=True)
        subprocess.run([str(common.resolve_ndk_tool("llvm-strip", ndk)), "--strip-unneeded", str(target)], check=True)
        validate_elf_page_compatibility(target.read_bytes(), filename)
        actual = exports(target, readelf)
        if actual != expected:
            raise RuntimeError(f'helper ABI drift: {filename}: {actual}')
        artifacts.append({'path': target.relative_to(ROOT).as_posix(), 'size': target.stat().st_size,
                          'sha256': common.sha256_file(target), 'exports': actual, 'command': command})
    provenance = {'schema': 1, 'abi': 'arm64-v8a', 'ndk': ndk.name,
                  'sources': sources, 'artifacts': artifacts,
                  'recipe_sha256': common.sha256_file(Path(__file__)),
                  'paths_override_sha256': common.sha256_file(SOURCE / 'shmem/paths.h')}
    lockfile = ROOT / 'schemas/runtime-helper-lockfile-arm64-v8a.json'
    pins = {x['path']: {k: x[k] for k in ('size', 'sha256', 'exports')} for x in artifacts}
    if '--write-lockfile' in sys.argv:
        lockfile.write_text(json.dumps({'schema': 1, 'abi': 'arm64-v8a', 'ndk': ndk.name, 'artifacts': pins}, indent=2) + '\n')
    else:
        if json.loads(lockfile.read_text())['artifacts'] != pins:
            raise RuntimeError('runtime helper binary pins changed; review the actual build before relocking')
    (STAGE.parent / 'HELPER_BUILD_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    main()
