"""
Data item to text file conversion.

Loads file content from various sources (S3, local) using appropriate loaders.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Tuple
from urllib.parse import urlparse

from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.ingestion.core.exceptions import IngestionError
from m_flow.shared.files.utils.open_data_file import open_data_file
from m_flow.shared.loaders import get_loader_engine
from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)


class _DataSettings(MflowSettings):
    """Settings for data ingestion."""

    accept_local_file_path: bool = True
    model_config = SettingsConfigDict(env_prefix="MFLOW_", env_file=".env", extra="allow")


_settings = _DataSettings()


async def _download_s3(s3_path: str, dest) -> None:
    """Download file from S3 to local destination."""
    async with open_data_file(s3_path) as src:
        while True:
            chunk = src.read(8192)
            if not chunk:
                break
            dest.write(chunk)


async def data_item_to_text_file(
    data_item_path: str,
    preferred_loaders: dict[str, dict[str, Any]] | None = None,
) -> Tuple[str, LoaderInterface]:
    """
    Load file content from path and return text with loader.

    Supports:
      - S3 paths (s3://bucket/key)
      - file:// URIs
      - Absolute local paths

    Args:
        data_item_path: Source file path or URI.
        preferred_loaders: Optional loader preferences.

    Returns:
        Tuple of (text_content, loader_instance).

    Raises:
        IngestionError: Unsupported path or local access denied.
    """
    if not isinstance(data_item_path, str):
        raise IngestionError(message=f"Unsupported data type: {type(data_item_path)}")

    parsed = urlparse(data_item_path)

    # S3 source
    if parsed.scheme == "s3":
        suffix = Path(parsed.path).suffix
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
            await _download_s3(data_item_path, tmp)
            tmp.flush()
            loader = get_loader_engine()
            text = await loader.load_file(tmp.name, preferred_loaders)
            return text, loader.get_loader(tmp.name, preferred_loaders)

    # Local file path
    if parsed.scheme == "file" or _is_absolute_path(data_item_path):
        if not _settings.accept_local_file_path:
            raise IngestionError(message="Local file access not permitted.")

        loader = get_loader_engine()
        text = await loader.load_file(data_item_path, preferred_loaders)
        return text, loader.get_loader(data_item_path, preferred_loaders)

    raise IngestionError(message=f"Unsupported path scheme: {parsed.scheme}")


def _is_absolute_path(path: str) -> bool:
    """Check if path is absolute (Unix or Windows)."""
    if path.startswith("/"):
        return True
    # Windows: C:\path
    if os.name == "nt" and len(path) > 1 and path[1] == ":":
        return True
    return False
