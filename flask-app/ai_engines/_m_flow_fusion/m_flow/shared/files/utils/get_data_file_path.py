"""Normalise heterogeneous path strings into filesystem-native paths.

Handles ``file://`` URIs, ``s3://`` URIs, and plain paths.
Windows drive-letter edge cases are handled explicitly.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse


def _normalise_file_uri(raw: str) -> str:
    """Convert a ``file://`` URI into a native OS path."""
    without_scheme = raw.replace("file://", "", 1)
    normalised = os.path.normpath(without_scheme)
    # On Windows the URI ``file:///C:/dir`` normalises to ``/C:\\dir``
    if os.name == "nt":
        if (normalised.startswith("/") or normalised.startswith("\\")) and len(normalised) > 2 and normalised[2] == ":":
            normalised = normalised[1:]
    return normalised


def _normalise_s3_uri(raw: str) -> str:
    """Normalise an ``s3://`` URI without corrupting the scheme."""
    parsed = urlparse(raw)
    path_part = os.path.normpath(parsed.path).lstrip(os.sep)
    return f"s3://{parsed.netloc}{os.sep}{path_part}"


def get_data_file_path(file_path: str) -> str:
    """Return a normalised version of *file_path*.

    * ``file://`` → local OS path
    * ``s3://``   → normalised S3 URI
    * anything else → ``os.path.normpath``
    """
    if file_path.startswith("file://"):
        return _normalise_file_uri(file_path)
    if file_path.startswith("s3://"):
        return _normalise_s3_uri(file_path)
    return os.path.normpath(file_path)
