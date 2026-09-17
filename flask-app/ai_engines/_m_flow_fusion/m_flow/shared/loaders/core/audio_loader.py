"""Audio file ingestion via LLM transcription."""

from __future__ import annotations

import os
from typing import Sequence

from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.llm.LLMGateway import LLMService
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.files.utils.get_file_metadata import get_file_metadata

_AUDIO_EXTENSIONS = ("aac", "mid", "mp3", "m4a", "ogg", "flac", "wav", "amr", "aiff")
_AUDIO_MIMES = (
    "audio/aac",
    "audio/midi",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/flac",
    "audio/wav",
    "audio/amr",
    "audio/aiff",
    "audio/x-wav",
)


class AudioLoader(LoaderInterface):
    """Transcribes audio files into text via an LLM gateway and persists the result."""

    @property
    def supported_extensions(self) -> Sequence[str]:
        return list(_AUDIO_EXTENSIONS)

    @property
    def supported_mime_types(self) -> Sequence[str]:
        return list(_AUDIO_MIMES)

    @property
    def loader_name(self) -> str:
        return "audio_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        return extension in _AUDIO_EXTENSIONS and mime_type in _AUDIO_MIMES

    async def load(self, file_path: str, **kwargs):
        """Transcribe audio and persist the text transcript."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing file: {file_path}")

        with open(file_path, "rb") as fh:
            meta = await get_file_metadata(fh)

        dest_name = f"text_{meta['content_hash']}.txt"

        transcript = await LLMService.transcribe_audio(file_path)

        cfg = get_storage_config()
        store = get_file_storage(cfg["data_root_directory"])
        return await store.store(dest_name, transcript.text)
