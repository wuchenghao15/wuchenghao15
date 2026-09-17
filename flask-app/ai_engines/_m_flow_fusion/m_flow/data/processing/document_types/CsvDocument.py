"""
CSV document handler.

Reads CSV files and yields row-wise text chunks.
"""

from __future__ import annotations

import csv
import io
from typing import Type

from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.files.utils.open_data_file import open_data_file
from .Document import Document


class CsvDocument(Document):
    """CSV file handler with row-based text generation."""

    type: str = "csv"
    mime_type: str = "text/csv"

    async def read(
        self,
        chunker_cls: Type[Chunker],
        max_chunk_size: int,
    ):
        """
        Read CSV and yield chunked content.

        Each row is converted to "key: value" pairs.
        """

        async def _row_generator():
            async with open_data_file(
                self.processed_path,
                mode="r",
                encoding="utf-8",
                newline="",
            ) as f:
                content = f.read()
                reader = csv.DictReader(io.StringIO(content))

                for row in reader:
                    text = ", ".join(f"{k}: {v}" for k, v in row.items())
                    if not text.strip():
                        break
                    yield text

        chunker = chunker_cls(
            self,
            max_chunk_size=max_chunk_size,
            get_text=_row_generator,
        )

        async for chunk in chunker.read():
            yield chunk
