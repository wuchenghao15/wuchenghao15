"""
UnstructuredDocument集成测试
测试各种文档类型的读取和分块
"""

from __future__ import annotations

import pathlib
import sys
import uuid

import pytest
from unittest.mock import patch

from m_flow.data.processing.document_types.UnstructuredDocument import UnstructuredDocument
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.tests.integration.documents.AudioDocument_test import mock_get_embedding_engine

_TEST_DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "test_data"
_CHUNK_SIZE = 1024


def _get_test_path(filename: str) -> str:
    return str(_TEST_DATA_DIR / filename)


def _create_doc(name: str, mime: str) -> UnstructuredDocument:
    return UnstructuredDocument(
        id=uuid.uuid4(),
        name=name,
        processed_path=_get_test_path(name),
        external_metadata="",
        mime_type=mime,
    )


# PPTX MIME类型
_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
# DOCX MIME类型
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# XLSX MIME类型
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


_chunk_module = sys.modules.get("m_flow.ingestion.chunks.split_sentences")


@patch.object(_chunk_module, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_pptx_document(mock_engine):
    """测试PPTX文档读取"""
    doc = _create_doc("example.pptx", _PPTX_MIME)

    async for chunk in doc.read(chunker_cls=TextChunker, max_chunk_size=_CHUNK_SIZE):
        assert chunk.chunk_size == 19
        assert len(chunk.text) == 104
        assert chunk.cut_type == "sentence_cut"


@patch.object(_chunk_module, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_docx_document(mock_engine):
    """测试DOCX文档读取"""
    doc = _create_doc("example.docx", _DOCX_MIME)

    async for chunk in doc.read(chunker_cls=TextChunker, max_chunk_size=_CHUNK_SIZE):
        assert chunk.chunk_size == 16
        assert len(chunk.text) == 145
        assert chunk.cut_type == "sentence_end"


@patch.object(_chunk_module, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_csv_document(mock_engine):
    """测试CSV文档读取"""
    doc = _create_doc("example.csv", "text/csv")

    async for chunk in doc.read(chunker_cls=TextChunker, max_chunk_size=_CHUNK_SIZE):
        assert chunk.chunk_size == 15
        assert chunk.text == "A A A A A A A A A,A A A A A A,A A"
        assert chunk.cut_type == "sentence_cut"


@patch.object(_chunk_module, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_xlsx_document(mock_engine):
    """测试XLSX文档读取"""
    doc = _create_doc("example.xlsx", _XLSX_MIME)

    async for chunk in doc.read(chunker_cls=TextChunker, max_chunk_size=_CHUNK_SIZE):
        assert chunk.chunk_size == 36
        assert len(chunk.text) == 171
        assert chunk.cut_type == "sentence_cut"
