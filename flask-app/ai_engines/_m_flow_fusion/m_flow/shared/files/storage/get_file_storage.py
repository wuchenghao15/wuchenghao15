"""
Storage backend factory.

Provides factory functions to create StorageManager instances
configured for either local filesystem or S3-compatible storage.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from m_flow.base_config import get_base_config

if TYPE_CHECKING:
    from .StorageManager import StorageManager


def _detect_s3_backend(path: str) -> bool:
    """
    Determine if the given path should use S3 storage.

    Checks:
    1. Path starts with s3:// protocol
    2. STORAGE_BACKEND env var is set to 's3' and config paths use S3
    """
    # Explicit S3 path
    if path.startswith("s3://"):
        return True

    # Check environment override
    backend_env = os.getenv("STORAGE_BACKEND", "").lower()
    if backend_env != "s3":
        return False

    # Verify config also uses S3
    config = get_base_config()
    uses_s3_system = "s3://" in config.system_root_directory
    uses_s3_data = "s3://" in config.data_root_directory
    return uses_s3_system and uses_s3_data


def get_file_storage(storage_path: str) -> "StorageManager":
    """
    Create a StorageManager for the specified path.

    Automatically selects the appropriate backend (local or S3)
    based on the path and environment configuration.

    Args:
        storage_path: Root path for storage operations.

    Returns:
        StorageManager configured with the correct backend.
    """
    from .StorageManager import StorageManager

    if _detect_s3_backend(storage_path):
        from .S3FileStorage import S3FileStorage

        backend = S3FileStorage(storage_path)
    else:
        from .LocalFileStorage import LocalFileStorage

        backend = LocalFileStorage(storage_path)

    return StorageManager(backend)
