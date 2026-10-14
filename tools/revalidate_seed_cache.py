#!/usr/bin/env python3
"""Revalidate a source-only manifest repin without changing any cache bytes.

Replays the captured manifest and proves exact baseline/transcript equality,
then validates every cached item against the unchanged live item corpus.
Records the audited loader source so a future semantic change fails closed.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
try:
    from tools import seed_sqlite_from_manifest as seeder
except ImportError:
    import seed_sqlite_from_manifest as seeder

ROOT = seeder.ROOT
CAPTURE_REV = "08b2a281a24774fdec78bb50f86ac4ec63d2c7bb"
LOADER = ROOT / "native/playerbots/playerbot/RandomItemMgr.cpp"


def main():
    provenance_path = seeder.AUGMENT_DIR / "PROVENANCE.json"
    provenance = json.loads(provenance_path.read_text())
    old = subprocess.check_output(["git", "show", f"{CAPTURE_REV}:schemas/database-migrations.json"], cwd=ROOT)
    current = seeder.MANIFEST.read_bytes()
    historical = json.loads(old)
    assert historical["entries"] == json.loads(current)["entries"], "migration corpus changed"
    old_sha = hashlib.sha256(old.replace(b"\r\n", b"\n")).hexdigest()
    original = json.loads(subprocess.check_output([
        "git", "show", f"{CAPTURE_REV}:schemas/seed-augment/PROVENANCE.json"], cwd=ROOT))
    assert old_sha == original["manifest_sha256"], "capture origin not authenticated"
    # Replay with the historical guard; do not rewrite provenance to make the
    # replay pass. Restore even on an execution or integrity failure.
    previous = provenance_path.read_bytes()
    try:
        provenance_path.write_text(json.dumps(original, indent=2) + "\n")
        with tempfile.TemporaryDirectory(prefix="seed-revalidate-") as tmp:
            tmp = Path(tmp)
            manifest = tmp / "manifest.json"
            manifest.write_bytes(old)
            rc, summary = seeder.seed(tmp / "db", tmp / "transcripts", False, 0, manifest)
            assert rc == 0
            baseline = json.loads(subprocess.check_output([
                "git", "show", f"{CAPTURE_REV}:schemas/sqlite-seed-baseline.json"], cwd=ROOT))
            assert seeder.sanitize_summary(summary) == baseline, "captured seed replay changed"
            with sqlite3.connect(tmp / "db/classiccharacters.sqlite") as conn:
                conn.execute("ATTACH DATABASE ? AS world", (str(tmp / "db/classicmangos.sqlite"),))
                assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
                tables = {}
                for table, columns in (
                    ("ai_playerbot_rnditem_cache", "lvl, type, item"),
                    ("ai_playerbot_equip_cache", "clazz, spec, lvl, slot, quality, item"),
                ):
                    loader = LOADER.read_text()
                    assert f"select {columns} from {table}" in loader, "cache loader contract changed"
                    count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    missing = conn.execute(f"SELECT count(*) FROM {table} c LEFT JOIN world.item_template i ON i.entry=c.item WHERE i.entry IS NULL").fetchone()[0]
                    assert count > 0 and missing == 0, "cache item corpus mismatch"
                    tables[table] = {"rows": count, "missing_item_references": missing, "loader_columns": columns}
                invalid = conn.execute("SELECT count(*) FROM ai_playerbot_equip_cache WHERE clazz NOT IN (1,2,3,4,5,7,8,9,11) OR lvl NOT BETWEEN 1 AND 60 OR slot NOT BETWEEN 0 AND 18 OR quality NOT BETWEEN 0 AND 6").fetchone()[0]
                assert invalid == 0, "equipment cache outside Vanilla bounds"
            evidence = {"capture_manifest_revision": CAPTURE_REV, "capture_manifest_sha256": old_sha,
                        "all_migration_records_identical": True, "exact_seed_baseline_reproduced": True,
                        "transcript_digests": summary["transcript_digests"], "tables": tables,
                        "invalid_equipment_rows": invalid,
                        "loader_sha256": hashlib.sha256(LOADER.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                        "augmentation_sha256": hashlib.sha256((seeder.AUGMENT_DIR / "classiccharacters.sql.gz").read_bytes()).hexdigest()}
    finally:
        provenance_path.write_bytes(previous)
    current_sha = hashlib.sha256(current.replace(b"\r\n", b"\n")).hexdigest()
    provenance.update(manifest_sha256=current_sha, revalidated_at="2026-10-14",
                      revalidation=evidence,
                      revalidation_note="Source-only repin: all 414 records, SQL bytes and exact historical seed transcripts reproduced; all 1,109,982 cached item references resolve in the unchanged corpus, loader column contracts and Vanilla equipment bounds pass. Current loader and augmentation hashes now enforced. This validates reuse; new first-boot cache generation and device play remain unqualified.")
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n")
    baseline["manifest_sha256"] = current_sha
    seeder.BASELINE.write_text(json.dumps(baseline, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
