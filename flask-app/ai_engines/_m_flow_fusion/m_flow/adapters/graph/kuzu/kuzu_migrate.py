#!/usr/bin/env python3
"""
Kuzu database migration utility.

Migrates data between Kuzu versions by:
  1. Creating isolated venvs for source and target versions
  2. Exporting data using old version
  3. Importing data using new version
  4. Optional: Replace original database with migrated version

Requirements:
  - Python 3.7+
  - Internet connection
  - Sufficient disk space for venvs and exports
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile

# Storage version → Kuzu release mapping
_VERSION_MAP = {
    34: "0.7.0",
    35: "0.7.1",
    36: "0.8.2",
    37: "0.9.0",
    38: "0.10.1",
    39: "0.11.0",
}


def detect_kuzu_version(db_path: str) -> str:
    """
    Read Kuzu storage version from catalog file.

    Args:
        db_path: Path to Kuzu database directory.

    Returns:
        Kuzu version string (e.g., "0.9.0").

    Raises:
        FileExistsError: Catalog file not found.
        ValueError: Unknown version code.
    """
    if os.path.isdir(db_path):
        catalog = os.path.join(db_path, "catalog.kz")
        if not os.path.isfile(catalog):
            raise FileExistsError("Catalog file catalog.kz not found")
    else:
        catalog = db_path

    with open(catalog, "rb") as f:
        f.seek(4)  # Skip "KUZ" magic + padding
        data = f.read(8)
        if len(data) < 8:
            raise ValueError(f"Invalid catalog file: {catalog}")
        code = struct.unpack("<Q", data)[0]

    version = _VERSION_MAP.get(code)
    if not version:
        raise ValueError(f"Unknown Kuzu storage version code: {code}")

    return version


# Alias
read_kuzu_storage_version = detect_kuzu_version


def _setup_venv(version: str, base_dir: str) -> str:
    """Create venv with specific Kuzu version installed."""
    venv_root = os.path.join(base_dir, ".kuzu_envs")
    venv_path = os.path.join(venv_root, version)
    python_bin = os.path.join(venv_path, "bin", "python")

    # Clean existing venv
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)

    print(f"→ Creating venv for Kuzu {version}...", file=sys.stderr)
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    subprocess.run([python_bin, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([python_bin, "-m", "pip", "install", f"kuzu=={version}"], check=True)

    return python_bin


def _run_cypher(python_bin: str, db_path: str, query: str) -> None:
    """Execute Cypher query in isolated Python process."""
    script = f"""
import kuzu
db = kuzu.Database(r"{db_path}")
conn = kuzu.Connection(db)
conn.execute(r\"\"\"{query}\"\"\")
"""
    proc = subprocess.run([python_bin, "-c", script], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[ERROR] Cypher failed:\n{proc.stderr}", file=sys.stderr)
        sys.exit(proc.returncode)


def _rename_and_cleanup(
    old_db: str,
    old_version: str,
    new_db: str,
    delete_old: bool,
) -> None:
    """Swap new database into old location."""
    base_dir = os.path.dirname(old_db)
    name = os.path.basename(old_db.rstrip(os.sep))
    backup_name = f"{name}_old_{old_version.replace('.', '_')}"
    backup_path = os.path.join(base_dir, backup_name)

    if os.path.isdir(old_db):
        if delete_old:
            shutil.rmtree(old_db)
        else:
            os.rename(old_db, backup_path)
            print(f"Backed up: {old_db} → {backup_path}", file=sys.stderr)
    elif os.path.isfile(old_db):
        for ext in ["", ".wal"]:
            src = old_db + ext
            dst = backup_path + ext
            if os.path.exists(src):
                if delete_old:
                    os.remove(src)
                else:
                    os.rename(src, dst)

    # Move new database into place
    for ext in ["", ".wal"]:
        src = new_db + ext
        dst = os.path.join(base_dir, name + ext)
        if os.path.exists(src):
            os.rename(src, dst)


def kuzu_migration(
    new_db: str,
    old_db: str,
    new_version: str,
    old_version: str | None = None,
    overwrite: bool = False,
    delete_old: bool = False,
) -> None:
    """
    Perform Kuzu database migration.

    Args:
        new_db: Target database path.
        old_db: Source database path.
        new_version: Target Kuzu version.
        old_version: Source version (auto-detected if None).
        overwrite: Replace original with migrated version.
        delete_old: Remove original after migration (requires overwrite).
    """
    if not old_version:
        old_version = detect_kuzu_version(old_db)

    print(f"🔄 Migrating Kuzu: {old_version} → {new_version}", file=sys.stderr)
    print(f"   Source: {old_db}", file=sys.stderr)

    if not os.path.exists(old_db):
        print(f"Source database not found: {old_db}", file=sys.stderr)
        sys.exit(1)

    parent = os.path.dirname(new_db)
    if parent:
        os.makedirs(parent, exist_ok=True)

    if os.path.exists(new_db):
        raise FileExistsError(f"Target already exists: {new_db}. Remove it or use different path.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        old_py = _setup_venv(old_version, tmp_dir)
        new_py = _setup_venv(new_version, tmp_dir)

        export_path = os.path.join(tmp_dir, "kuzu_export")

        print("Exporting from source...", file=sys.stderr)
        _run_cypher(old_py, old_db, f"EXPORT DATABASE '{export_path}'")

        schema = os.path.join(export_path, "schema.cypher")
        if not os.path.exists(schema) or os.path.getsize(schema) == 0:
            raise ValueError("Export failed: schema file missing or empty")

        print("Importing to target...", file=sys.stderr)
        _run_cypher(new_py, new_db, f"IMPORT DATABASE '{export_path}'")

    if overwrite or delete_old:
        lock_file = f"{new_db}.lock"
        if os.path.exists(lock_file):
            os.remove(lock_file)
        _rename_and_cleanup(old_db, old_version, new_db, delete_old)

    print("[OK] Migration completed successfully!", file=sys.stderr)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate Kuzu databases between versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--old-version",
        help="Source Kuzu version (auto-detected if omitted)",
    )
    parser.add_argument(
        "--new-version",
        required=True,
        help="Target Kuzu version",
    )
    parser.add_argument(
        "--old-db",
        required=True,
        help="Source database path",
    )
    parser.add_argument(
        "--new-db",
        required=True,
        help="Target database path (must differ from --old-db)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace source with migrated database",
    )
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="Delete original after migration (requires --overwrite)",
    )

    args = parser.parse_args()

    kuzu_migration(
        new_db=args.new_db,
        old_db=args.old_db,
        new_version=args.new_version,
        old_version=args.old_version,
        overwrite=args.overwrite,
        delete_old=args.delete_old,
    )


if __name__ == "__main__":
    main()
