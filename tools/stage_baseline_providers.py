#!/usr/bin/env python3
"""Recover immutable dependency providers from the pinned upstream release.

Never imports upstream app/core/extractor/patcher binaries. The original
Termux packages have rotated out of the mirror; the release preserves their
locked ELF closure and bootstrap. No binary hashes are regenerated here.
"""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from urllib.request import urlopen
try:
    from tools import common
except ImportError:
    import common
ROOT = common.ROOT
SHA = '09d5fde0d9ba9a58331ce6ecca1b03bf7b02e586304058063d6253e9542b7144'
URL = 'https://github.com/puzzled-pancake/pocket-realm/releases/download/v0.103.0-alpha/Pocket-Realm-0.103.0-alpha-arm64-v8a.apk'
CACHE = ROOT / 'native/.providers/pocket-realm-v0.103.0/provider.apk'


def main():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE.is_file():
        temporary = CACHE.with_suffix('.tmp')
        with urlopen(URL, timeout=120) as response, temporary.open('wb') as out:
            shutil.copyfileobj(response, out)
        if common.sha256_file(temporary) != SHA:
            raise RuntimeError('upstream provider APK hash mismatch')
        temporary.replace(CACHE)
    if common.sha256_file(CACHE) != SHA:
        raise RuntimeError('cached upstream provider APK hash mismatch')
    native = ROOT / 'native'
    maria = native / '.build-arm64/mariadb-staging'
    wine = native / '.build-arm64/wine-staging'
    record = json.loads((ROOT / 'schemas/mariadb-runtime-lockfile-arm64-v8a.json').read_text())
    llama = json.loads((native / 'llm/lockfile-arm64-v8a.json').read_text())
    recovery = {'schema': 1, 'archive_url': URL, 'archive_sha256': SHA,
                'archive_bytes': CACHE.stat().st_size, 'artifacts': []}
    with zipfile.ZipFile(CACHE) as z:
        def stage(member, target, expected=None, size=None):
            data = z.read(member)
            digest = hashlib.sha256(data).hexdigest()
            if expected is not None and digest != expected:
                raise RuntimeError(f'provider hash mismatch: {member}')
            if size is not None and len(data) != size:
                raise RuntimeError(f'provider size mismatch: {member}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            recovery['artifacts'].append({'member': member, 'path': target.relative_to(ROOT).as_posix(),
                                          'sha256': digest, 'size': len(data)})
        runtime = record['runtime']
        if json.loads(z.read('assets/database/provider/runtime-manifest.json')) != runtime:
            raise RuntimeError('MariaDB release manifest differs from the locked provider')
        for artifact in list(runtime['executables'].values()) + runtime['links']:
            name = artifact['apk_name']
            stage(f'lib/arm64-v8a/{name}', maria / 'jniLibs/arm64-v8a' / name,
                  artifact['sha256'], artifact['size'])
        for member in z.namelist():
            if member.startswith('assets/database/provider/') and not member.endswith('/'):
                stage(member, maria / member)
        if common.sha256_file(maria / 'assets/database/provider/bootstrap.sql') != runtime['bootstrap_sha256']:
            raise RuntimeError('MariaDB bootstrap hash mismatch')
        for name, meta in llama['libs'].items():
            stage(f'lib/arm64-v8a/{name}', native / 'llm/prebuilt/arm64-v8a' / name,
                  meta['sha256'], meta['bytes'])
        for name, sha, size in (
            ('rootfs.tzst', '8b5110f248e84f2aee4df37dab8bac4c4bf2bdc7b400c0643a0778ca8e7e40c2', 65251198),
            ('rootfs_patches.tzst', '44b73e37587ea827a12a34753632feb6e2a9c127089e342774167dd91aba8210', 4173700),
            ('container_pattern.tzst', '8ae3a4fee33e86da26826395650bb07c6f49ce94629ea4b9442bc633b6b8ca33', 7399363),
        ):
            member = f'assets/arm-translated-wine/{name}'
            stage(member, wine / member, sha, size)
        # The translated provider's Bionic launcher and shmem/semaphore codecs
        # are recovered byte-for-byte from the hash-pinned release. They remain
        # dependency providers, with their existing corresponding source in-tree.
        for name in ('libbox64.so', 'libpocket_lzma.so', 'libpocket_z.so'):
            stage(f'lib/arm64-v8a/{name}', wine / 'jniLibs' / name)
    # Preserve the historical package attribution while making the actual
    # recovery boundary explicit. This is not claimed as a local MariaDB build.
    provenance = {'schema': 1, 'provider': record['provider'], 'abi': record['abi'],
                  'runtime': runtime, 'packages': record['packages'],
                  'package_index': record['package_index'], 'recovery': recovery}
    (maria / 'BUILD_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (wine / 'BUILD_PROVENANCE.json').write_text(json.dumps(recovery, indent=2) + '\n')
    (native / 'llm/prebuilt/BUILD_PROVENANCE.json').write_text(json.dumps(recovery, indent=2) + '\n')
    print(f'Verified and staged {len(recovery["artifacts"])} immutable provider files')


if __name__ == '__main__':
    main()
