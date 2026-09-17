"""Heuristic file-type detection.

Uses the ``filetype`` library for magic-byte detection, with explicit
overrides for extension-based types that lack magic bytes (plain text,
CSV).
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import BinaryIO, Optional

import filetype
from filetype.types.base import Type

# Extensions that ``filetype.guess`` cannot detect via magic bytes
_EXTENSION_OVERRIDES: dict[str, tuple[str, str]] = {
    ".txt": ("text/plain", "txt"),
    ".text": ("text/plain", "txt"),
    ".csv": ("text/csv", "csv"),
}

# Fallback when detection yields nothing
_DEFAULT_TYPE = Type("text/plain", "txt")


class FileTypeException(Exception):
    """Raised when the file type cannot be determined."""

    def __init__(self, detail: str) -> None:
        self.message = detail
        super().__init__(detail)


def _suffix_from(source: object, override_name: Optional[str]) -> Optional[str]:
    """Return the lowercased file suffix, preferring *override_name*."""
    if override_name is not None:
        return PurePosixPath(override_name).suffix.lower()
    if isinstance(source, str):
        return PurePosixPath(source).suffix.lower()
    return None


def guess_file_type(
    file: BinaryIO,
    name: Optional[str] = None,
) -> Type:
    """Return the detected :class:`filetype.Type` for *file*.

    Falls back to ``text/plain`` when magic-byte detection returns
    *None* (common for text files that have no binary signature).
    """
    ext = _suffix_from(file, name)

    override = _EXTENSION_OVERRIDES.get(ext) if ext else None
    if override is not None:
        return Type(*override)

    detected = filetype.guess(file)
    if detected is not None:
        return detected

    # No magic-byte match — treat as plain text
    return _DEFAULT_TYPE
