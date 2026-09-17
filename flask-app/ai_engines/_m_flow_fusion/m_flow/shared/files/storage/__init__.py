"""
Pluggable file storage layer for M-flow.

This package provides an abstraction layer for file storage,
supporting both local filesystem and cloud object storage (S3).

Components
----------
StorageManager
    Async facade for storage operations with automatic
    backend selection.

get_file_storage
    Factory function that creates a StorageManager configured
    for the appropriate backend based on path and environment.

get_storage_config
    Retrieves merged storage configuration from context
    and global settings.

Example
-------
>>> from m_flow.shared.files.storage import get_file_storage
>>> storage = get_file_storage("/data/documents")
>>> await storage.store("doc.txt", "Hello, world!")
"""

from __future__ import annotations

# Explicit imports to ensure functions are accessible
# (Python's import system prefers submodule names over __getattr__)
from .StorageManager import StorageManager
from .get_file_storage import get_file_storage
from .get_storage_config import get_storage_config as get_storage_config

__all__ = ["StorageManager", "get_file_storage", "get_storage_config"]
