"""
Image document processor.

Extracts text from images via LLM transcription.
"""

from __future__ import annotations

from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.llm.LLMGateway import LLMService

from .Document import Document


class ImageDocument(Document):
    """
    Document type for image files.

    Uses multimodal LLM to extract text content from images.
    """

    type: str = "image"

    async def describe_image(self) -> str:
        """
        Extract text description from image.

        Returns:
            Transcribed text content.
        """
        response = await LLMService.describe_image(self.processed_path)
        return response.choices[0].message.content

    async def read(self, chunker_cls: Chunker, max_chunk_size: int):
        """
        Process image and generate chunks.

        Args:
            chunker_cls: Chunker implementation.
            max_chunk_size: Token limit per chunk.

        Yields:
            Content fragments from transcribed text.
        """

        async def text_generator():
            transcription = await self.describe_image()
            yield transcription

        chunker = chunker_cls(
            self,
            get_text=text_generator,
            max_chunk_size=max_chunk_size,
        )

        async for fragment in chunker.read():
            yield fragment
