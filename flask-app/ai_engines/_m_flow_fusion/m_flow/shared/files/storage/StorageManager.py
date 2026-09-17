"""Async facade that delegates to a concrete :class:`Storage` backend.

All public methods are ``async`` so that callers can work uniformly
regardless of whether the underlying backend is synchronous (local FS)
or asynchronous (S3 via ``s3fs``).
"""

from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from typing import BinaryIO

from .storage import Storage


def _is_coro(fn) -> bool:
    """Return *True* when *fn* is a coroutine function."""
    return inspect.iscoroutinefunction(fn)


class StorageManager:
    """Thin async wrapper around any :class:`Storage` implementation.

    Methods mirror :class:`Storage` but are always awaitable so that
    the rest of the code-base stays async-first.
    """

    storage: Storage

    def __init__(self, backend: Storage) -> None:
        self.storage = backend

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def file_exists(self, file_path: str) -> bool:
        """Check whether *file_path* exists in the backing store."""
        op = self.storage.file_exists
        return await op(file_path) if _is_coro(op) else op(file_path)

    async def is_file(self, file_path: str) -> bool:
        op = self.storage.is_file
        return await op(file_path) if _is_coro(op) else op(file_path)

    async def get_size(self, file_path: str) -> int:
        op = self.storage.get_size
        return await op(file_path) if _is_coro(op) else op(file_path)

    # ------------------------------------------------------------------
    # Write / copy
    # ------------------------------------------------------------------

    async def store(self, file_path: str, data: BinaryIO, overwrite: bool = False) -> str:
        """Persist *data* at *file_path* and return the resulting full path."""
        op = self.storage.store
        return await op(file_path, data, overwrite) if _is_coro(op) else op(file_path, data, overwrite)

    @asynccontextmanager
    async def open(self, file_path: str, encoding: str | None = None, *args, **kwargs):
        """Yield a file-like handle for *file_path*."""
        # S3 backend exposes an async context manager; local backend is sync.
        backend_name = type(self.storage).__name__
        if backend_name == "S3FileStorage":
            async with self.storage.open(file_path, *args, **kwargs) as fh:
                yield fh
        else:
            with self.storage.open(file_path, *args, **kwargs) as fh:
                yield fh

    # ------------------------------------------------------------------
    # Directory lifecycle
    # ------------------------------------------------------------------

    async def ensure_directory_exists(self, directory_path: str = "") -> None:
        op = self.storage.ensure_directory_exists
        return await op(directory_path) if _is_coro(op) else op(directory_path)

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------

    async def remove(self, file_path: str) -> None:
        """Delete a single object."""
        op = self.storage.remove
        return await op(file_path) if _is_coro(op) else op(file_path)

    async def list_files(self, directory_path: str, recursive: bool = False) -> list[str]:
        """Enumerate objects under *directory_path*."""
        op = self.storage.list_files
        return await op(directory_path, recursive) if _is_coro(op) else op(directory_path, recursive)

    async def remove_all(self, tree_path: str | None = None) -> None:
        """Recursively remove everything under *tree_path*."""
        op = self.storage.remove_all
        return await op(tree_path) if _is_coro(op) else op(tree_path)
