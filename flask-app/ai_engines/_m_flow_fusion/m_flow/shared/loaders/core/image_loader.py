"""Image file ingestion via LLM vision transcription."""

from __future__ import annotations

import os
from typing import Sequence

from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.llm.LLMGateway import LLMService
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata

_IMG_EXTENSIONS = (
    "png",
    "dwg",
    "xcf",
    "jpg",
    "jpe",
    "jpeg",
    "jpx",
    "apng",
    "gif",
    "webp",
    "cr2",
    "tif",
    "tiff",
    "bmp",
    "jxr",
    "psd",
    "ico",
    "heic",
    "avif",
)
_IMG_MIMES = (
    "image/png",
    "image/vnd.dwg",
    "image/x-xcf",
    "image/jpeg",
    "image/jpx",
    "image/apng",
    "image/gif",
    "image/webp",
    "image/x-canon-cr2",
    "image/tiff",
    "image/bmp",
    "image/jxr",
    "image/vnd.adobe.photoshop",
    "image/vnd.microsoft.icon",
    "image/heic",
    "image/avif",
)


class ImageLoader(LoaderInterface):
    """Converts images to descriptive text via an LLM vision model."""

    @property
    def supported_extensions(self) -> Sequence[str]:
        return list(_IMG_EXTENSIONS)

    @property
    def supported_mime_types(self) -> Sequence[str]:
        return list(_IMG_MIMES)

    @property
    def loader_name(self) -> str:
        return "image_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        return extension in _IMG_EXTENSIONS and mime_type in _IMG_MIMES

    async def load(self, file_path: str, **kwargs):
        """Describe the image via LLM and persist the resulting text."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing file: {file_path}")

        with open(file_path, "rb") as fh:
            meta = await get_file_metadata(fh)

        dest_name = f"text_{meta['content_hash']}.txt"

        vision_result = await LLMService.describe_image(file_path)
        description = vision_result.choices[0].message.content

        cfg = get_storage_config()
        store = get_file_storage(cfg["data_root_directory"])
        return await store.store(dest_name, description)
