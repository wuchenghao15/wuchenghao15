"""
File handling infrastructure for M-flow.

This package provides unified file operations across different
storage backends and utilities for file processing.

Sub-packages
------------
storage
    Backend abstraction layer supporting local filesystem
    and S3-compatible object storage.

utils
    File utilities including content hashing, MIME type
    detection, metadata extraction, and path normalization.

Convenience Exports
-------------------
FileMetadata
    TypedDict containing file metadata fields.

get_file_metadata
    Async function to extract metadata from file handles.

Example
-------
>>> from m_flow.shared.files import get_file_metadata
>>> async with aiofiles.open("doc.pdf", "rb") as f:
...     metadata = await get_file_metadata(f)
...     print(metadata["content_hash"])
"""

from __future__ import annotations


def __getattr__(name: str):
    """Lazy import for convenience exports."""
    if name in ("FileMetadata", "get_file_metadata"):
        from m_flow.shared.files.utils.get_file_metadata import (
            FileMetadata,
            get_file_metadata,
        )

        if name == "FileMetadata":
            return FileMetadata
        return get_file_metadata

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["FileMetadata", "get_file_metadata"]
