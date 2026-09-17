"""
CSV文档集成测试
"""

from __future__ import annotations

import pathlib
import sys
import uuid

import pytest
from unittest.mock import patch

from m_flow.data.processing.document_types.CsvDocument import CsvDocument
from m_flow.ingestion.chunking.CsvChunker import CsvChunker
from m_flow.tests.integration.documents.AudioDocument_test import mock_get_embedding_engine
from m_flow.tests.integration.documents.async_gen_zip import async_gen_zip

_TEST_DATA = pathlib.Path(__file__).parent.parent.parent / "test_data"
_chunk_mod = sys.modules.get("m_flow.ingestion.chunks.split_rows")

# 期望结果 - 使用 mock embedding engine (tokenizer=None) 时的实际值
# CSV 内容: id,name,category,value / 1,alpha,A,100 / 2,beta,B,200
# 注意: mock 使 chunk_size 使用简单的词计数，而非 tokenizer
_EXPECTED = {
    10: [
        {"tokens": 9, "text_len": 31, "cut": "row_cut", "idx": 0},  # 'id: 1, name: alpha, category: A'
        {"tokens": 3, "text_len": 10, "cut": "row_end", "idx": 1},  # 'value: 100'
        {"tokens": 9, "text_len": 30, "cut": "row_cut", "idx": 2},  # 'id: 2, name: beta, category: B'
        {"tokens": 3, "text_len": 10, "cut": "row_end", "idx": 3},  # 'value: 200'
    ],
    128: [
        {"tokens": 12, "text_len": 43, "cut": "row_end", "idx": 0},  # 'id: 1, name: alpha, category: A, value: 100'
        {"tokens": 12, "text_len": 42, "cut": "row_end", "idx": 1},  # 'id: 2, name: beta, category: B, value: 200'
    ],
}


def _create_csv_doc(filename: str) -> CsvDocument:
    return CsvDocument(
        id=uuid.uuid4(),
        name=filename,
        processed_path=str(_TEST_DATA / filename),
        external_metadata="",
        mime_type="text/csv",
    )


@pytest.mark.parametrize(
    "filename,size",
    [
        ("example_with_header.csv", 10),
        ("example_with_header.csv", 128),
    ],
)
@patch.object(_chunk_mod, "get_embedding_engine", side_effect=mock_get_embedding_engine)
@pytest.mark.asyncio
async def test_csv_chunking(mock_eng, filename, size):
    """测试CSV文档分块"""
    doc = _create_csv_doc(filename)
    expected = _EXPECTED[size]

    async for exp, chunk in async_gen_zip(expected, doc.read(chunker_cls=CsvChunker, max_chunk_size=size)):
        assert exp["tokens"] == chunk.chunk_size, f"token数: {exp['tokens']} != {chunk.chunk_size}"
        assert exp["text_len"] == len(chunk.text), f"文本长度: {exp['text_len']} != {len(chunk.text)}"
        assert exp["cut"] == chunk.cut_type, f"切割类型: {exp['cut']} != {chunk.cut_type}"
        assert exp["idx"] == chunk.chunk_index, f"索引: {exp['idx']} != {chunk.chunk_index}"
