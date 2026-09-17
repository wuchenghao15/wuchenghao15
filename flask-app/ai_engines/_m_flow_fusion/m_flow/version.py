"""
Version resolution for M-flow.

Prefers the installed package metadata; falls back to pyproject.toml
when running from a development checkout.
"""

from __future__ import annotations

import importlib.metadata
from pathlib import Path

_CACHED: str | None = None


def get_version() -> str:
    """
    Return the M-flow semantic version string.

    Checks installed package metadata first (typical for ``pip install``),
    then reads ``pyproject.toml`` in development layouts, and finally
    returns a placeholder if neither source is available.
    """
    global _CACHED
    if _CACHED is not None:
        return _CACHED

    # 1. Installed package (pip / wheel)
    try:
        _CACHED = importlib.metadata.version("m_flow")
        return _CACHED
    except importlib.metadata.PackageNotFoundError:
        pass

    # 2. Source checkout (development)
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if pyproject.is_file():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("version"):
                _, _, value = line.partition("=")
                _CACHED = value.strip().strip("'\"") + "-dev"
                return _CACHED

    # 3. Unknown
    _CACHED = "0.0.0-unknown"
    return _CACHED
