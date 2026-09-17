"""Plain-text file ingestion handler."""

from __future__ import annotations

import os
from typing import Sequence

from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata

_TEXT_EXTENSIONS = ("txt", "md", "json", "xml", "yaml", "yml", "log")
_TEXT_MIMES = (
    "text/plain",
    "text/markdown",
    "application/json",
    "text/xml",
    "application/xml",
    "text/yaml",
    "application/yaml",
)


class TextLoader(LoaderInterface):
    """Ingests plain-text and text-like files (Markdown, JSON, YAML, etc.)."""

    @property
    def supported_extensions(self) -> Sequence[str]:
        return list(_TEXT_EXTENSIONS)

    @property
    def supported_mime_types(self) -> Sequence[str]:
        return list(_TEXT_MIMES)

    @property
    def loader_name(self) -> str:
        return "text_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        return extension in _TEXT_EXTENSIONS and mime_type in _TEXT_MIMES

    async def load(self, file_path: str, encoding: str = "utf-8", **kwargs):
        """Read the text file, persist a copy, and return the stored path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing file: {file_path}")

        with open(file_path, "rb") as fh:
            meta = await get_file_metadata(fh)

        dest_name = f"text_{meta['content_hash']}.txt"

        with open(file_path, "r", encoding=encoding) as fh:
            body = fh.read()

        cfg = get_storage_config()
        store = get_file_storage(cfg["data_root_directory"])
        return await store.store(dest_name, body)
