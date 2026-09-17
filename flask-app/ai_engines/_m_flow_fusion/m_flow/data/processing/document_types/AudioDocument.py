"""
Audio document processor.

Transcribes audio files via LLM for text extraction.
"""

from __future__ import annotations

from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.llm.LLMGateway import LLMService

from .Document import Document


class AudioDocument(Document):
    """
    Document type for audio files.

    Uses speech-to-text LLM to transcribe audio content.
    """

    type: str = "audio"

    async def transcribe_audio(self) -> str:
        """
        Generate text transcript from audio.

        Returns:
            Transcribed text content.
        """
        response = await LLMService.transcribe_audio(self.processed_path)
        return response.text

    async def read(self, chunker_cls: Chunker, max_chunk_size: int):
        """
        Process audio and generate chunks.

        Args:
            chunker_cls: Chunker implementation.
            max_chunk_size: Token limit per chunk.

        Yields:
            Content fragments from transcribed audio.
        """

        async def text_generator():
            transcript = await self.transcribe_audio()
            yield transcript

        chunker = chunker_cls(
            self,
            get_text=text_generator,
            max_chunk_size=max_chunk_size,
        )

        async for fragment in chunker.read():
            yield fragment
