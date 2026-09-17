"""
Directory resolution for data ingestion.

Expands directory paths to individual file paths, supporting
both local filesystem and S3 storage.
"""

from __future__ import annotations

import os
from typing import BinaryIO, Union
from urllib.parse import urlparse

from m_flow.ingestion.pipeline_tasks.exceptions import S3FileSystemNotFoundError
from m_flow.shared.files.storage.s3_config import get_s3_config


async def resolve_data_directories(
    data: Union[BinaryIO, list[BinaryIO], str, list[str]],
    include_subdirectories: bool = True,
) -> list:
    """
    Expand directories to file lists.

    Resolves directory paths (local or S3) into individual file paths,
    passing through binary streams and direct file paths unchanged.

    Args:
        data: File path(s), directory path(s), or binary stream(s).
        include_subdirectories: Recursively include nested directories.

    Returns:
        Flat list of resolved file paths and binary streams.

    Raises:
        S3FileSystemNotFoundError: S3 path without configured credentials.
    """
    items = data if isinstance(data, list) else [data]

    s3_cfg = get_s3_config()
    s3_fs = None

    # Initialize S3 filesystem if credentials available
    if s3_cfg.aws_access_key_id and s3_cfg.aws_secret_access_key:
        import s3fs

        s3_fs = s3fs.S3FileSystem(
            key=s3_cfg.aws_access_key_id,
            secret=s3_cfg.aws_secret_access_key,
            token=s3_cfg.aws_session_token,
            anon=False,
        )

    resolved = []

    for item in items:
        # Non-string items pass through directly
        if not isinstance(item, str):
            resolved.append(item)
            continue

        parsed = urlparse(item)

        # Handle S3 paths
        if parsed.scheme == "s3":
            if s3_fs is None:
                raise S3FileSystemNotFoundError()

            resolved.extend(_resolve_s3_path(s3_fs, item, include_subdirectories))

        # Handle local directories
        elif os.path.isdir(item):
            resolved.extend(_resolve_local_dir(item, include_subdirectories))

        # Regular files or text strings
        else:
            resolved.append(item)

    return resolved


def _resolve_s3_path(fs, path: str, recursive: bool) -> list[str]:
    """Resolve S3 path to file list."""
    if recursive:
        base = path if path.endswith("/") else f"{path}/"
        keys = fs.glob(f"{base}**")
        if not keys:
            keys = fs.ls(path)
    else:
        keys = fs.ls(path)

    # Filter directories and ensure s3:// prefix
    files = []
    for key in keys:
        if not fs.isdir(key):
            uri = key if key.startswith("s3://") else f"s3://{key}"
            files.append(uri)

    return files


def _resolve_local_dir(path: str, recursive: bool) -> list[str]:
    """Resolve local directory to file list."""
    if recursive:
        files = []
        for root, _, filenames in os.walk(path):
            files.extend(os.path.join(root, f) for f in filenames)
        return files
    else:
        return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
