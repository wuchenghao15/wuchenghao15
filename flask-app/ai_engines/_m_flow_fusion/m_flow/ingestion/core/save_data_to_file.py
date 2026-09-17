"""
Utility to persist ingested data to file storage.
"""

from __future__ import annotations

import hashlib
from typing import BinaryIO, Optional, Union

from m_flow.shared.files.storage import get_file_storage, get_storage_config

from .classify import classify


async def save_data_to_file(
    data: Union[str, BinaryIO],
    filename: Optional[str] = None,
    file_extension: Optional[str] = None,
) -> str:
    """
    Save data to file storage and return the full path.

    Parameters
    ----------
    data
        Text or binary data to save.
    filename
        Optional filename hint.
    file_extension
        Optional extension override.

    Returns
    -------
    Full path to the stored file.
    """
    cfg = get_storage_config()
    root_dir = cfg["data_root_directory"]

    classified = classify(data, filename)
    meta = classified.get_metadata()

    async with classified.get_data() as content:
        if not meta.get("name"):
            encoded = content.encode("utf-8")
            hash_val = hashlib.md5(encoded).hexdigest()
            meta["name"] = f"text_{hash_val}.txt"

        name = meta["name"]

        if file_extension:
            ext = file_extension.lstrip(".")
            base = name.rsplit(".", 1)[0]
            name = f"{base}.{ext}"

        storage = get_file_storage(root_dir)
        return await storage.store(name, content)
