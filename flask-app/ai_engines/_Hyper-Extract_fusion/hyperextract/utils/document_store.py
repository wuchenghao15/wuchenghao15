"""Archive source documents inside the KA directory (``documents/``).

Files are named deterministically from the ``source_id`` so they can be
located later without a metadata lookup:

    documents/<sha256(source_id)[:12]>-<original basename>

This keeps one *current* copy per source: re-feeding the same source_id
overwrites the archived file, mirroring the ledger's bounded
"current version per source" policy.
"""

import hashlib
import shutil
from pathlib import Path

DOCUMENTS_DIR = "documents"
_HASH_LEN = 12


def source_hash(source_id: str) -> str:
    """Stable short hash used as the archived filename prefix."""
    return hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:_HASH_LEN]


class SourceDocumentStore:
    """Filesystem archive of raw source documents for one KA."""

    def __init__(self, ka_root: Path):
        self.root = Path(ka_root) / DOCUMENTS_DIR

    def path_for(self, source_id: str, original_name: str) -> Path:
        """Deterministic archive path for a source (original name kept for humans)."""
        safe_name = Path(original_name).name or "document.txt"
        return self.root / f"{source_hash(source_id)}-{safe_name}"

    def store_text(
        self, source_id: str, text: str, original_name: str = "document.txt"
    ) -> Path:
        """Archive text content (used for stdin feeds)."""
        self.root.mkdir(parents=True, exist_ok=True)
        # Keep one current copy per source: drop prior archives whose filename
        # differs (the original basename is part of the name), so re-feeding the
        # same source_id overwrites rather than accumulating stale copies.
        self.purge(source_id)
        path = self.path_for(source_id, original_name)
        path.write_text(text, encoding="utf-8")
        return path

    def store_file(self, source_id: str, input_path: str | Path) -> Path:
        """Archive an original file (raw bytes preserved)."""
        src = Path(input_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.purge(source_id)
        dst = self.path_for(source_id, src.name)
        shutil.copy2(src, dst)
        return dst

    def find(self, source_id: str) -> list[Path]:
        """All archived files for a source (usually one)."""
        if not self.root.exists():
            return []
        return sorted(self.root.glob(f"{source_hash(source_id)}-*"))

    def purge(self, source_id: str) -> list[Path]:
        """Delete archived files for a source. Returns the removed paths."""
        removed = []
        for path in self.find(source_id):
            path.unlink()
            removed.append(path)
        return removed
