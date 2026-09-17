"""Shared helpers for local FAISS index loading."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_warned_index_paths: set[str] = set()


def _warn_untrusted_faiss_load(folder_path: str | Path) -> None:
    """Warn once per path that a local FAISS index requires deserialization.

    Local FAISS indexes are loaded with deserialization enabled. Only load
    indexes from Knowledge Abstract directories you created or fully trust.
    """
    path = str(Path(folder_path).resolve())
    if path in _warned_index_paths:
        return
    _warned_index_paths.add(path)
    logger.warning(
        "Loading a local FAISS index from %s requires deserialization. "
        "Only load Knowledge Abstract directories that you created or fully trust.",
        path,
    )
