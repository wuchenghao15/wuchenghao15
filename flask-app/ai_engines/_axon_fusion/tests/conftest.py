from __future__ import annotations

from pathlib import Path

import pytest

from axon.core.storage.kuzu_backend import KuzuBackend


@pytest.fixture()
def kuzu_backend(tmp_path: Path) -> KuzuBackend:
    """Provide an initialised KuzuBackend in a temporary directory."""
    db_path = tmp_path / "test_db"
    b = KuzuBackend()
    b.initialize(db_path)
    yield b
    b.close()
