"""Abstract storage contract for M-Flow file backends.

Any concrete storage implementation (local filesystem, S3, etc.) must
satisfy the :class:`Storage` protocol so that higher-level code
remains backend-agnostic.
"""

from __future__ import annotations

from typing import BinaryIO, Protocol, Union, runtime_checkable


@runtime_checkable
class Storage(Protocol):
    """Minimal interface every file-storage backend must expose.

    Attributes:
        storage_path: Root location managed by this backend (local path or URI).
    """

    storage_path: str

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def file_exists(self, file_path: str) -> bool:
        """Return *True* when *file_path* points to an existing object."""
        ...

    def is_file(self, file_path: str) -> bool:
        """Return *True* when *file_path* is a regular file (not a directory)."""
        ...

    def get_size(self, file_path: str) -> int:
        """Return the size in bytes of the object at *file_path*."""
        ...

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def store(self, file_path: str, data: Union[BinaryIO, str], overwrite: bool) -> None:
        """Persist *data* at *file_path*, optionally overwriting an existing object."""
        ...

    def open(self, file_path: str, mode: str = "r"):
        """Open *file_path* and yield a file-like handle."""
        ...

    def copy_file(self, source_file_path: str, destination_file_path: str) -> str:
        """Duplicate *source_file_path* to *destination_file_path*; return the new path."""
        ...

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    def ensure_directory_exists(self, directory_path: str = "") -> None:
        """Create *directory_path* (and parents) if it does not already exist."""
        ...

    def remove(self, file_path: str) -> None:
        """Delete a single object at *file_path*."""
        ...

    def remove_all(self, root_path: str | None = None) -> None:
        """Recursively delete everything under *root_path*."""
        ...
