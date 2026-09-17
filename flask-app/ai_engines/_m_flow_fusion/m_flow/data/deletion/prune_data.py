"""Data pruning utility."""

from __future__ import annotations

from m_flow.shared.files.storage import get_file_storage, get_storage_config


async def prune_data() -> None:
    """Remove all data files from storage."""
    cfg = get_storage_config()
    root = cfg["data_root_directory"]
    storage = get_file_storage(root)
    await storage.remove_all()
