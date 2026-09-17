"""
Path resolution utilities for the M-Flow package tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

_PKG_ROOT: Path = Path(__file__).resolve().parent


def get_absolute_path(relative: str) -> str:
    """
    Resolve *relative* against the package root and return an absolute path.

    Parameters
    ----------
    relative
        A path fragment (e.g. ``".data_storage"``).

    Returns
    -------
    str
        Fully resolved absolute path.
    """
    return str((_PKG_ROOT / relative).resolve())


def ensure_absolute_path(raw: Union[str, Path]) -> str:
    """
    Validate that *raw* is an absolute path (or an S3 URI).

    Raises
    ------
    ValueError
        If *raw* is ``None`` or represents a relative local path.
    """
    if raw is None:
        raise ValueError("Path cannot be None")

    text = str(raw)
    # S3 URIs are absolute by convention
    if text.startswith("s3://"):
        return text

    expanded = Path(text).expanduser()
    if not expanded.is_absolute():
        raise ValueError(f"Expected an absolute path, received: {text}")

    return str(expanded.resolve())
