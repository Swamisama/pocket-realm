#!/usr/bin/env python3
"""Fetch the immutable ARM provider and fallback source inputs."""
import hashlib
from pathlib import Path
import shutil
import tarfile
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'native/.providers-extracted'
PINS = [
    ('winlator-app-ca3d735', 'winlator-app-ca3d735.tar.gz',
     'https://codeload.github.com/brunodev85/winlator-app/tar.gz/ca3d735a60d653a787daf16d14fafef28d9c2c23', '8aa6f93c9d935e479987571f2058bebc0d62b931ecd1df1759eaf5b05ac845a5'),
    ('proot-termux-a89b3732', 'proot-source.tar.gz',
     'https://codeload.github.com/termux/proot/tar.gz/a89b3732ec6ae1db674510f0843b2f3db54d0a2f', 'aafe17d43fc54d6a1d0e0bfddbb855cae544802609aef33226c0808ed1f32349'),
    ('talloc-2.4.2', 'talloc-source.tar.gz',
     'https://www.samba.org/ftp/talloc/talloc-2.4.2.tar.gz',
     '85ecf9e465e20f98f9950a52e9a411e14320bc555fa257d87697b7e7a9b1d8a6'),
]


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    for directory, artifact, url, expected in PINS:
        cached = CACHE / artifact
        if not cached.is_file():
            temporary = cached.with_suffix('.tmp')
            with urlopen(url, timeout=120) as response, temporary.open('wb') as out:
                shutil.copyfileobj(response, out)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                raise RuntimeError(f'source archive hash mismatch: {url}')
            temporary.replace(cached)
        if hashlib.sha256(cached.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'cached source archive hash mismatch: {cached}')
        target = CACHE / directory
        if not target.is_dir():
            target.mkdir()
            with tarfile.open(cached) as bundle:
                for member in bundle.getmembers():
                    member.name = '/'.join(member.name.split('/')[1:])
                    if member.name:
                        bundle.extract(member, target, filter='data')
        print(f'Verified {directory}: {expected}')


if __name__ == '__main__':
    main()
