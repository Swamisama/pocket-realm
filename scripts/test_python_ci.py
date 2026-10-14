#!/usr/bin/env python3
"""Run exactly the repository CI Python selection, retaining its eight exclusions."""
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / '.github/workflows/ci.yml').read_text()
exclusions = re.findall(r'--deselect\s+(tests/[^\s]+)', workflow)
if len(exclusions) != 8:
    raise RuntimeError('review CI Python selection: expected the eight existing upstream exclusions')
args = [sys.executable, '-m', 'pytest', 'tests/', '-q']
for test_id in exclusions:
    args += ['--deselect', test_id]
args += sys.argv[1:]
raise SystemExit(subprocess.call(args, cwd=ROOT,
    env={**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}))
