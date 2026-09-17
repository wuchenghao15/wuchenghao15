"""
File metadata extraction utilities.

Extracts metadata (name, path, MIME type, hash, size) from
binary file objects for use in document processing pipelines.
"""

from __future__ import annotations

import io
import os
from pathlib import PurePosixPath
from typing import BinaryIO, Optional, TypedDict

from m_flow.shared.files.utils.get_file_content_hash import get_file_content_hash
from m_flow.shared.logging_utils import get_logger

from .guess_file_type import guess_file_type

_logger = get_logger("file_metadata")


class FileMetadata(TypedDict):
    """Container for file metadata fields."""

    name: str
    file_path: str
    mime_type: str
    extension: str
    content_hash: str
    file_size: int


def _get_filename_stem(handle: BinaryIO) -> Optional[str]:
    """
    Extract the filename stem from a file handle.

    Looks for 'name' or 'full_name' attributes on the handle.
    """
    for attr in ("name", "full_name"):
        value = getattr(handle, attr, None)
        if isinstance(value, str) and value:
            return PurePosixPath(value).stem or None
    return None


def _get_file_path(handle: BinaryIO) -> Optional[str]:
    """Extract the file path from a file handle."""
    return getattr(handle, "name", None) or getattr(handle, "full_name", None)


def _calculate_byte_size(handle: BinaryIO) -> int:
    """
    Determine the byte size of a file handle.

    Preserves the original stream position.
    """
    original_pos = handle.tell()
    handle.seek(0, os.SEEK_END)
    total_size = handle.tell()
    handle.seek(original_pos)
    return total_size


async def _compute_content_hash(handle: BinaryIO) -> str:
    """
    Compute the content hash for a file handle.

    Resets stream position before and after hashing.
    Returns empty string on failure.
    """
    try:
        handle.seek(0)
        hash_value = await get_file_content_hash(handle)
        handle.seek(0)
        return hash_value
    except io.UnsupportedOperation as err:
        _logger.error(
            "content_hash_failed",
            file_name=_get_file_path(handle) or "<unknown>",
            error=str(err),
        )
        return ""


async def get_file_metadata(
    file: BinaryIO,
    name: Optional[str] = None,
) -> FileMetadata:
    """
    Extract comprehensive metadata from a file handle.

    Computes content hash, detects MIME type, and gathers
    file information without consuming the stream.

    Args:
        file: Open binary file handle.
        name: Optional filename hint for type detection.

    Returns:
        FileMetadata dictionary with all extracted fields.
    """
    content_hash = await _compute_content_hash(file)
    type_info = guess_file_type(file, name)

    return FileMetadata(
        name=_get_filename_stem(file),
        file_path=_get_file_path(file),
        mime_type=type_info.mime,
        extension=type_info.extension,
        content_hash=content_hash,
        file_size=_calculate_byte_size(file),
    )
