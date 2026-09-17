"""Unified async context manager for opening files from any backend.

Supports ``file://`` URIs, ``s3://`` URIs, and plain filesystem paths.
The correct storage backend is selected automatically.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from m_flow.shared.files.utils.get_data_file_path import get_data_file_path
from m_flow.shared.files.storage.LocalFileStorage import LocalFileStorage


def _split(normalised: str):
    """Return ``(directory, basename)`` from a normalised path."""
    return os.path.dirname(normalised), os.path.basename(normalised)


@asynccontextmanager
async def open_data_file(
    file_path: str,
    mode: str = "rb",
    encoding: str | None = None,
    **extra,
):
    """Yield a file handle for *file_path* from the appropriate backend.

    * ``file://`` → :class:`LocalFileStorage`
    * ``s3://``   → :class:`S3FileStorage` (lazily imported)
    * plain path  → :class:`LocalFileStorage`
    """
    resolved = get_data_file_path(file_path)
    directory, basename = _split(resolved)

    if not basename or basename in (".", ".."):
        raise ValueError(
            f"Cannot derive a valid filename from '{file_path}' (resolved: '{resolved}', basename: '{basename}')"
        )

    if file_path.startswith("s3://"):
        from m_flow.shared.files.storage.S3FileStorage import S3FileStorage

        backend = S3FileStorage(directory)
        async with backend.open(basename, mode=mode, **extra) as handle:
            yield handle
        return

    # Local filesystem (with or without ``file://`` scheme)
    backend = LocalFileStorage(directory)
    with backend.open(basename, mode=mode, encoding=encoding, **extra) as handle:
        yield handle
