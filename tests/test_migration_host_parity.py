"""Linux builds must preserve the bytes and order of shipped SQL migrations."""
import hashlib
import json
from pathlib import Path

import pytest

from tools import stage_database_migrations as migrations


def test_line_ending_conversion_must_prove_the_existing_hash():
    shipped = b"SELECT 1;\r\nSELECT 2;\r\n"
    pin = hashlib.sha256(shipped).hexdigest()
    assert migrations.preserve_sql_bytes(shipped.replace(b"\r\n", b"\n"), pin) == shipped
    with pytest.raises(RuntimeError, match="shipped migration hash"):
        migrations.preserve_sql_bytes(b"SELECT 3;\n", pin)


def test_new_sql_is_host_independent():
    assert migrations.preserve_sql_bytes(b"SELECT 1;\r\n", None) == b"SELECT 1;\n"


def test_native_source_migration_sequence_and_hashes_match_shipped_ledger():
    root = Path(__file__).resolve().parents[1]
    if not (root / "native/cmangos/sql/base/realmd.sql").is_file():
        pytest.skip("native submodules not populated")
    expected = json.loads((root / "schemas/database-migrations.json").read_text())["entries"]
    actual = migrations.select_inputs()
    assert len(actual) == len(expected)
    for item, entry in zip(actual, expected):
        assert item.path.relative_to(root).as_posix() == entry["source_path"]
        assert hashlib.sha256(migrations.sql_bytes(item.path)).hexdigest() == entry["sql_sha256"]
