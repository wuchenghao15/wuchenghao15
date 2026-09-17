"""
TextDocument集成测试
"""

from __future__ import annotations

import pathlib
import sys
import uuid

import pytest
from unittest.mock import patch

from m_flow.data.processing.document_types.TextDocument import TextDocument
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.tests.integration.documents.AudioDocument_test import mock_get_embedding_engine
from m_flow.tests.integration.documents.async_gen_zip import async_gen_zip

_TEST_DATA = pathlib.Path(__file__).parent.parent.parent / "test_data"
_chunk_mod = sys.modules.get("m_flow.ingestion.chunks.split_sentences")

# 期望结果 - 使用 mock embedding engine (tokenizer=None) 时的实际值
# 注意: mock 使 chunk_size 使用简单的词计数，而非 tokenizer
_EXPECTED = {
    "code.txt": [
        {"words": 28, "text_len": 181, "cut": "sentence_cut"},
    ],
    "Natural_language_processing.txt": [
        {"words": 8, "text_len": 46, "cut": "sentence_cut"},
    ],
}


@pytest.mark.parametrize(
    "filename,size",
    [
        ("code.txt", 256),
        ("Natural_language_processing.txt", 128),
    ],
)
@patch.object(_chunk_mod, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_text_chunking(mock_eng, filename, size):
    """测试文本文档分块"""
    doc = TextDocument(
        id=uuid.uuid4(),
        name=filename,
        processed_path=str(_TEST_DATA / filename),
        external_metadata="",
        mime_type="",
    )

    expected = _EXPECTED[filename]
    async for exp, chunk in async_gen_zip(expected, doc.read(chunker_cls=TextChunker, max_chunk_size=size)):
        assert exp["words"] == chunk.chunk_size, f"词数: {exp['words']} != {chunk.chunk_size}"
        assert exp["text_len"] == len(chunk.text), f"长度: {exp['text_len']} != {len(chunk.text)}"
        assert exp["cut"] == chunk.cut_type, f"类型: {exp['cut']} != {chunk.cut_type}"
