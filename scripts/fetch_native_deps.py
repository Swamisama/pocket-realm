#!/usr/bin/env python3
"""Fetch and verify the reviewed OpenSSL/Boost source archives on any host."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'native/.deps'
PINS = (
    ('openssl-3.4.3', 'openssl-3.4.3.tar.gz',
     'https://github.com/openssl/openssl/releases/download/openssl-3.4.3/openssl-3.4.3.tar.gz',
     'fa727ed1399a64e754030a033435003991aee36bda9a5b080995cb2ac5cf7f37', 'openssl-3.4.3'),
    ('boost-1.86.0', 'boost_1_86_0.tar.bz2',
     'https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.bz2',
     '1bed88e40401b2cb7a1f76d4bab499e352fa4d0c5f31c0dbae64e24d34d7513b', 'boost_1_86_0'),
)


def main():
    (DEPS / 'src').mkdir(parents=True, exist_ok=True)
    records = []
    for name, archive, url, expected, extracted in PINS:
        cached = DEPS / archive
        if not cached.is_file():
            temporary = cached.with_suffix('.tmp')
            with urlopen(url, timeout=120) as response, temporary.open('wb') as out:
                shutil.copyfileobj(response, out)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                raise RuntimeError(f'archive hash mismatch: {url}')
            temporary.replace(cached)
        if hashlib.sha256(cached.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'cached archive hash mismatch: {cached}')
        target = DEPS / 'src' / name
        if not target.is_dir():
            with tarfile.open(cached) as bundle:
                bundle.extractall(DEPS / 'src', filter='data')
            if extracted != name:
                (DEPS / 'src' / extracted).rename(target)
        records.append({'name': name, 'url': url, 'sha256': expected})
    (DEPS / 'SOURCE_PROVENANCE.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Verified OpenSSL 3.4.3 and Boost 1.86.0 source archives')


if __name__ == '__main__':
    main()
