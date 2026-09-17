"""
PDF document processor.

Extracts text from PDF files page by page.
"""

from __future__ import annotations

from pypdf import PdfReader

from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.files.utils.open_data_file import open_data_file
from m_flow.shared.logging_utils import get_logger

from .Document import Document

logger = get_logger("PdfReader")


class PdfDocument(Document):
    """
    Document type for PDF files.

    Uses pypdf library for text extraction.
    """

    type: str = "pdf"

    async def read(self, chunker_cls: Chunker, max_chunk_size: int):
        """
        Extract and chunk PDF content.

        Args:
            chunker_cls: Chunker implementation.
            max_chunk_size: Token limit per chunk.

        Yields:
            Content fragments from PDF pages.
        """
        async with open_data_file(self.processed_path, mode="rb") as stream:
            logger.info("Processing PDF: %s", self.processed_path)

            reader = PdfReader(stream, strict=False)

            async def text_generator():
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        yield text

            chunker = chunker_cls(
                self,
                get_text=text_generator,
                max_chunk_size=max_chunk_size,
            )

            async for fragment in chunker.read():
                yield fragment
