"""
Data item storage handler.

Routes various input types (files, URLs, text) to appropriate
storage mechanisms and returns file references.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, BinaryIO, Union
from urllib.parse import urlparse

from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.ingestion.core import save_data_to_file
from m_flow.ingestion.core.exceptions import IngestionError
from m_flow.ingestion.web_scraper.utils import fetch_page_content
from m_flow.shared.logging_utils import get_logger

_log = get_logger()


class _StorageSettings(MflowSettings):
    """Settings for local file acceptance."""

    accept_local_file_path: bool = True
    model_config = SettingsConfigDict(env_prefix="MFLOW_", env_file=".env", extra="allow")


_settings = _StorageSettings()


async def save_data_item_to_storage(data_item: Union[BinaryIO, str, Any]) -> str:
    """
    Persist input data and return storage reference.

    Handles:
      - LlamaIndex documents (optional import)
      - Docling documents (optional import)
      - File upload objects with .file attribute
      - S3 paths (s3://...)
      - HTTP/HTTPS URLs (downloads and stores)
      - Local file paths (absolute or relative)
      - Plain text strings

    Args:
        data_item: Input to store.

    Returns:
        File path or S3 URI reference.

    Raises:
        IngestionError: Unsupported data type.
    """
    type_str = str(type(data_item))

    # LlamaIndex integration (optional)
    if "llama_index" in type_str:
        from .transform_data import get_data_from_llama_index

        return await get_data_from_llama_index(data_item)

    # Docling integration (optional)
    if "docling" in type_str:
        from docling_core.types import DoclingDocument

        if isinstance(data_item, DoclingDocument):
            data_item = data_item.export_to_text()

    # File upload object (e.g., FastAPI UploadFile)
    if hasattr(data_item, "file"):
        return await save_data_to_file(data_item.file, filename=data_item.filename)

    # String inputs
    if isinstance(data_item, str):
        return await _handle_string_input(data_item)

    raise IngestionError(message=f"Unsupported data type: {type(data_item).__name__}")


async def _handle_string_input(data: str) -> str:
    """Process string input (URL, path, or text)."""
    parsed = urlparse(data)

    # S3 path - return as-is
    if parsed.scheme == "s3":
        return data

    # HTTP(S) URL - fetch and store
    if parsed.scheme in ("http", "https"):
        pages = await fetch_page_content(data)
        html_content = pages[data]
        return await save_data_to_file(html_content, file_extension="html")

    # file:// URL
    if parsed.scheme == "file":
        if _settings.accept_local_file_path:
            return data
        raise IngestionError(message="Local files are not accepted.")

    # Absolute path
    if _is_absolute_path(data):
        if _settings.accept_local_file_path:
            return _to_file_url(data)
        raise IngestionError(message="Local files are not accepted.")

    # Relative path - check if file exists
    try:
        resolved = (Path.cwd() / Path(data)).resolve()
        if resolved.is_file() and _settings.accept_local_file_path:
            return _to_file_url(str(resolved))
    except (OSError, ValueError):
        _log.debug(f"Path too long for file check: {data[:100]}...")

    # Plain text - save directly
    return await save_data_to_file(data)


def _is_absolute_path(path: str) -> bool:
    """Check if path is absolute (Unix or Windows)."""
    if path.startswith("/"):
        return True
    # Windows: C:\path
    if os.name == "nt" and len(path) > 1 and path[1] == ":":
        return True
    return False


def _to_file_url(path: str) -> str:
    """Convert filesystem path to file:// URL."""
    normalized = os.path.normpath(path).replace(os.sep, "/")
    return f"file://{normalized}"
