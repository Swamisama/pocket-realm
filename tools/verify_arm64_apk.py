#!/usr/bin/env python3
"""Verify signature, ZIP/ELF alignment, packaged bytes, ABI and ELF closure.

Host evidence only: this never installs or runs the APK on a device.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import tarfile
import zipfile
try:
    from tools import common
except ImportError:
    import common
ROOT = common.ROOT
APK = ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk'
REPORT = ROOT / 'output/arm64-baseline-verification.json'


def command(args):
    return subprocess.check_output([str(a) for a in args], text=True, stderr=subprocess.STDOUT).strip()


def elf(data, name):
    if data[:4] != b'\x7fELF' or data[5] != 1:
        raise RuntimeError(f'not a little-endian ELF: {name}')
    machine = struct.unpack_from('<H', data, 18)[0]
    compat32 = name == 'libproot_loader32.so'
    if machine != (40 if compat32 else 183) or data[4] != (1 if compat32 else 2):
        raise RuntimeError(f'wrong ABI: {name} machine={machine} class={data[4]}')
    if compat32:
        phoff = struct.unpack_from('<I', data, 28)[0]
        entsize, count = struct.unpack_from('<HH', data, 42)
    else:
        phoff = struct.unpack_from('<Q', data, 32)[0]
        entsize, count = struct.unpack_from('<HH', data, 54)
    aligns = []
    for i in range(count):
        off = phoff + i * entsize
        if struct.unpack_from('<I', data, off)[0] != 1:
            continue
        if compat32:
            fileoff, vaddr = struct.unpack_from('<II', data, off + 4)
            align = struct.unpack_from('<I', data, off + 28)[0]
        else:
            fileoff, vaddr = struct.unpack_from('<QQ', data, off + 8)
            align = struct.unpack_from('<Q', data, off + 48)[0]
        if align < 16384 or fileoff % 16384 != vaddr % 16384:
            raise RuntimeError(f'ELF not 16 KiB compatible: {name} LOAD[{i}] align={align}')
        aligns.append(align)
    if not aligns:
        raise RuntimeError(f'no LOAD segments: {name}')
    return machine, aligns


def rootfs_libraries(archive, temporary):
    """Resolve the separate glibc namespace from the exact packaged rootfs."""
    rootfs = temporary / 'rootfs.tzst'
    rootfs.write_bytes(archive.read('assets/arm-translated-wine/rootfs.tzst'))
    if common.sha256_file(rootfs) != '8b5110f248e84f2aee4df37dab8bac4c4bf2bdc7b400c0643a0778ca8e7e40c2':
        raise RuntimeError('packaged rootfs provider hash mismatch')
    readelf = common.resolve_ndk_tool('llvm-readelf')
    libraries = {}
    process = subprocess.Popen(['zstd', '-dc', rootfs], stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdout, mode='r|') as stream:
            for member in stream:
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts:
                    raise RuntimeError(f'unsafe rootfs member: {member.name}')
                if re.search(r'(?i)(\.mpq|\.dbc|\.adt|\.wdt|\.blp|\.m2|\.wmo)$', member.name) or path.name.lower() == 'wow.exe':
                    raise RuntimeError(f'proprietary client asset in rootfs: {member.name}')
                if not member.isfile() or '.so' not in path.name:
                    continue
                source = stream.extractfile(member)
                head = source.read(20)
                if head[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', head, 18)[0] != 183:
                    continue
                data = head + source.read()
                _, aligns = elf(data, path.name)
                target = temporary / f'rootfs-library-{len(libraries)}'
                target.write_bytes(data)
                dynamic = command([readelf, '-dW', target])
                soname = re.search(r'\(SONAME\).*?\[([^]]+)\]', dynamic)
                name = soname[1] if soname else path.name
                record = {'path': member.name, 'sha256': hashlib.sha256(data).hexdigest(),
                          'needed': re.findall(r'\(NEEDED\).*?\[([^]]+)\]', dynamic),
                          'load_alignments': aligns}
                if name in libraries and libraries[name]['sha256'] != record['sha256']:
                    raise RuntimeError(f'ambiguous glibc rootfs SONAME: {name}')
                libraries[name] = record
    finally:
        process.stdout.close()
        if process.wait() != 0:
            raise RuntimeError('rootfs decompression failed')
    return libraries


def main():
    if command(['git', '-C', ROOT, 'status', '--porcelain']):
        raise RuntimeError('commit the reviewed build inputs before final APK verification')
    sdk = common.resolve_android_sdk()
    build_tools = sdk / 'build-tools/36.0.0'
    signature = command([build_tools / common._exe('apksigner'), 'verify', '--verbose', '--print-certs', APK])
    certificate = re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', signature)
    if certificate is None:
        raise RuntimeError('APK signing certificate not reported')
    zip_alignment = command([build_tools / common._exe('zipalign'), '-c', '-P', '16', '-v', '4', APK])
    badging = command([build_tools / common._exe('aapt'), 'dump', 'badging', APK])
    if "native-code: 'arm64-v8a'" not in badging or "package: name='com.pocketrealm'" not in badging:
        raise RuntimeError('APK package/ABI metadata mismatch')
    ndk = common.resolve_android_ndk(sdk=sdk, prefer_version='30.0.15729638')
    readelf = common.resolve_ndk_tool('llvm-readelf', ndk)
    platform = {p.name for p in (ndk / 'toolchains/llvm/prebuilt' / common.HOST_TAG / 'sysroot/usr/lib/aarch64-linux-android/26').glob('*.so')}
    inventory = {}
    with tempfile.TemporaryDirectory(prefix='apk-elf-verify-') as tmp, zipfile.ZipFile(APK) as archive:
        for member in archive.namelist():
            if re.search(r'(?i)(\.mpq|\.dbc|\.adt|\.wdt|\.blp|\.m2|\.wmo)$', member) or Path(member).name.lower() == 'wow.exe':
                raise RuntimeError(f'proprietary client asset in APK: {member}')
            if not member.startswith('lib/'):
                continue
            if not member.startswith('lib/arm64-v8a/') or not member.endswith('.so'):
                raise RuntimeError(f'unexpected native APK member: {member}')
            name = Path(member).name
            data = archive.read(member)
            machine, aligns = elf(data, name)
            path = Path(tmp) / name
            path.write_bytes(data)
            dynamic = command([readelf, '-dW', path])
            needed = re.findall(r'\(NEEDED\).*?\[([^]]+)\]', dynamic)
            inventory[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
                               'machine': machine, 'load_alignments': aligns, 'needed': sorted(needed)}
        # The private MariaDB SONAME tree is created from this exact manifest.
        db = json.loads(archive.read('assets/database/provider/runtime-manifest.json'))
        locked = json.loads((ROOT / 'schemas/mariadb-runtime-lockfile-arm64-v8a.json').read_text())['runtime']
        if db != locked:
            raise RuntimeError('packaged MariaDB runtime manifest differs from lockfile')
        aliases = {x['logical']: x['apk_name'] for x in db['links']}
        for artifact in list(db['executables'].values()) + db['links']:
            actual = inventory[artifact['apk_name']]
            if actual['sha256'] != artifact['sha256'] or actual['size'] != artifact['size']:
                raise RuntimeError('packaged MariaDB provider bytes differ from lockfile')
        glibc = rootfs_libraries(archive, Path(tmp))
        glibc_used = {}
        def verify_glibc(name):
            if name in glibc_used:
                return
            if name not in glibc:
                raise RuntimeError(f'unresolved ARM glibc dependency in packaged rootfs: {name}')
            glibc_used[name] = glibc[name]
            for dependency in glibc[name]['needed']:
                verify_glibc(dependency)
        for name, actual in inventory.items():
            # Box64 is exec'd with the rootfs loader; it is not dlopen'd in
            # Android's Bionic namespace. Check its own recursive closure.
            if 'libc.so.6' in actual['needed']:
                actual['namespace'] = 'packaged-rootfs-glibc-arm64'
                for dependency in actual['needed']:
                    verify_glibc(dependency)
                continue
            actual['namespace'] = 'android-bionic'
            unresolved = set(actual['needed']) - platform - inventory.keys() - aliases.keys()
            if unresolved:
                raise RuntimeError(f'unresolved packaged DT_NEEDED: {name}: {sorted(unresolved)}')
        for lock_path in ('schemas/realm-runtime-lockfile-arm64-v8a.json', 'schemas/o11-extractor-lockfile-arm64-v8a.json', 'schemas/vanilla-tweaks-lockfile-arm64-v8a.json'):
            lock = json.loads((ROOT / lock_path).read_text())
            for artifact in lock['artifacts']:
                name = Path(artifact['path']).name
                actual = inventory[name]
                if actual['sha256'] != artifact['sha256'] or actual['size'] != artifact['size']:
                    raise RuntimeError(f'packaged artifact differs from build lockfile: {name}')
        helper_pins = json.loads((ROOT / 'schemas/runtime-helper-lockfile-arm64-v8a.json').read_text())['artifacts']
        for path, pin in helper_pins.items():
            actual = inventory[Path(path).name]
            if actual['sha256'] != pin['sha256'] or actual['size'] != pin['size']:
                raise RuntimeError(f'packaged helper differs from its actual-build pin: {path}')
        facade = json.loads((ROOT / 'native/.build-arm64/pocket-runtime-build/BUILD_PROVENANCE.json').read_text())['artifact']
        actual = inventory['libpocketrealm.so']
        if actual['sha256'] != facade['sha256'] or actual['size'] != facade['size']:
            raise RuntimeError('packaged legacy facade differs from its actual-build provenance')
    revisions = {'app': command(['git', '-C', ROOT, 'rev-parse', 'HEAD'])}
    for source in ('cmangos', 'playerbots', 'classic-db'):
        revisions[source] = command(['git', '-C', ROOT / 'native' / source, 'rev-parse', 'HEAD'])
    report = {'apk': APK.relative_to(ROOT).as_posix(), 'sha256': common.sha256_file(APK),
              'size': APK.stat().st_size, 'signing_certificate_sha256': certificate[1],
              'signature_verification': signature, 'zip_alignment_verified': 'Verification successful' in zip_alignment,
              'revisions': revisions, 'source_tree_clean': True,
              'source_manifest_sha256': common.sha256_file(ROOT / 'schemas/sources.json'),
              'toolchain': {'ndk': ndk.name, 'ndk_source_properties': (ndk / 'source.properties').read_text(),
                  'clang': command([common.resolve_ndk_tool('clang', ndk), '--version']),
                  'cmake': command([common.resolve_sdk_cmake('cmake', sdk), '--version']).splitlines()[0],
                  'ninja': command([common.resolve_sdk_cmake('ninja', sdk), '--version']),
                  'sdk_platform': 'android-35', 'build_tools': '36.0.0', 'gradle': '9.5.0', 'agp': '9.3.1',
                  'jdk': command(['java', '-version']), 'python': command(['python', '--version']), 'rust': command(['rustc', '-vV'])},
              'native_libraries': inventory, 'rootfs_glibc_closure': glibc_used,
              'device_qualification': 'not performed'}
    if not report['zip_alignment_verified']:
        raise RuntimeError('ZIP alignment verifier did not report success')
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('apk', 'sha256', 'size', 'signing_certificate_sha256', 'revisions', 'device_qualification')}, indent=2))
    print(f'ELF ABI, 16 KiB alignment and dependency closure verified for {len(inventory)} libraries')
    print(f'Full report: {REPORT}')


if __name__ == '__main__':
    main()
