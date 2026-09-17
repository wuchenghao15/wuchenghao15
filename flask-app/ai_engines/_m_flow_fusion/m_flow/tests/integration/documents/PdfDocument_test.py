"""
PdfDocument集成测试
"""

from __future__ import annotations

import pathlib
import sys
import uuid

import pytest
from unittest.mock import patch

from m_flow.data.processing.document_types.PdfDocument import PdfDocument
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.tests.integration.documents.AudioDocument_test import mock_get_embedding_engine
from m_flow.tests.integration.documents.async_gen_zip import async_gen_zip

_TEST_DATA = pathlib.Path(__file__).parent.parent.parent / "test_data"
_chunk_mod = sys.modules.get("m_flow.ingestion.chunks.split_sentences")


@patch.object(_chunk_mod, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_pdf_chunking(mock_eng):
    """Test PDF document chunking produces valid chunks"""
    doc = PdfDocument(
        id=uuid.uuid4(),
        name="AI_paper.pdf",
        processed_path=str(_TEST_DATA / "artificial-intelligence.pdf"),
        external_metadata="",
        mime_type="",
    )

    chunks = []
    async for chunk in doc.read(chunker_cls=TextChunker, max_chunk_size=1024):
        chunks.append(chunk)
        assert chunk.chunk_size > 0
        assert len(chunk.text) > 0
        assert chunk.cut_type in ("sentence_end", "paragraph_end", "hard_cut", "sentence_cut")

    assert len(chunks) >= 1, "PDF should produce at least one chunk"
