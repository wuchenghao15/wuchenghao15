"""
TextChunkerWithOverlap重叠行为测试
"""

from __future__ import annotations

import sys
from uuid import uuid4

import pytest
from unittest.mock import patch

from m_flow.data.processing.document_types import Document
from m_flow.ingestion.chunking.text_chunker_with_overlap import TextChunkerWithOverlap
from m_flow.ingestion.chunks import split_paragraphs


@pytest.fixture
def text_gen_factory():
    """文本生成器工厂"""

    def _make(*texts):
        async def gen():
            for t in texts:
                yield t

        return gen

    return _make


@pytest.fixture
def chunk_data_factory():
    """分块数据生成器工厂"""

    def _make(*sentences, size=10):
        def _gen(text):
            return [{"text": s, "chunk_size": size, "cut_type": "sentence", "chunk_id": uuid4()} for s in sentences]

        return _gen

    return _make


def _doc():
    return Document(
        id=uuid4(),
        name="test",
        processed_path="/test",
        external_metadata=None,
        mime_type="text/plain",
    )


@pytest.mark.asyncio
async def test_half_overlap(text_gen_factory, chunk_data_factory):
    """50%重叠测试"""
    chunker = TextChunkerWithOverlap(
        _doc(),
        text_gen_factory("x"),
        max_chunk_size=20,
        chunk_overlap_ratio=0.5,
        get_chunk_data=chunk_data_factory("一", "二", "三", "四", size=10),
    )
    chunks = [c async for c in chunker.read()]

    assert len(chunks) == 3
    assert "一" in chunks[0].text and "二" in chunks[0].text
    assert "二" in chunks[1].text and "三" in chunks[1].text
    assert "三" in chunks[2].text and "四" in chunks[2].text


@pytest.mark.asyncio
async def test_zero_overlap(text_gen_factory, chunk_data_factory):
    """零重叠测试"""
    chunker = TextChunkerWithOverlap(
        _doc(),
        text_gen_factory("x"),
        max_chunk_size=20,
        chunk_overlap_ratio=0.0,
        get_chunk_data=chunk_data_factory("一", "二", "三", "四", size=10),
    )
    chunks = [c async for c in chunker.read()]

    assert len(chunks) == 2
    assert "一" in chunks[0].text and "二" in chunks[0].text
    assert "三" in chunks[1].text and "四" in chunks[1].text
    assert "二" not in chunks[1].text


@pytest.mark.asyncio
async def test_small_overlap(text_gen_factory, chunk_data_factory):
    """小重叠率测试"""
    chunker = TextChunkerWithOverlap(
        _doc(),
        text_gen_factory("x"),
        max_chunk_size=40,
        chunk_overlap_ratio=0.25,
        get_chunk_data=chunk_data_factory("甲", "乙", "丙", "丁", "戊", size=10),
    )
    chunks = [c async for c in chunker.read()]

    assert len(chunks) == 2
    assert all(t in chunks[0].text for t in ["甲", "乙", "丙", "丁"])
    assert "丁" in chunks[1].text and "戊" in chunks[1].text


@pytest.mark.asyncio
async def test_high_overlap(text_gen_factory, chunk_data_factory):
    """高重叠率测试"""
    chunker = TextChunkerWithOverlap(
        _doc(),
        text_gen_factory("x"),
        max_chunk_size=20,
        chunk_overlap_ratio=0.75,
        get_chunk_data=chunk_data_factory("红", "蓝", "绿", "黄", "紫", size=5),
    )
    chunks = [c async for c in chunker.read()]

    assert len(chunks) == 2
    assert all(t in chunks[0].text for t in ["红", "蓝", "绿", "黄"])
    assert all(t in chunks[1].text for t in ["蓝", "绿", "黄", "紫"])


@pytest.mark.asyncio
async def test_single_chunk_no_artifact(text_gen_factory, chunk_data_factory):
    """单分块无重叠"""
    chunker = TextChunkerWithOverlap(
        _doc(),
        text_gen_factory("x"),
        max_chunk_size=20,
        chunk_overlap_ratio=0.5,
        get_chunk_data=chunk_data_factory("甲", "乙", size=10),
    )
    chunks = [c async for c in chunker.read()]

    assert len(chunks) == 1
    assert "甲" in chunks[0].text and "乙" in chunks[0].text


@pytest.mark.asyncio
async def test_paragraph_integration(text_gen_factory):
    """段落分块集成测试"""

    def mock_engine():
        class E:
            tokenizer = None

        return E()

    mod = sys.modules.get("m_flow.ingestion.chunks.split_sentences")
    max_size = 20
    overlap = 0.25

    text = (
        "A0 A1. A2 A3. A4 A5. A6 A7. A8 A9. "
        "B0 B1. B2 B3. B4 B5. B6 B7. B8 B9. "
        "C0 C1. C2 C3. C4 C5. C6 C7. C8 C9. "
        "D0 D1. D2 D3. D4 D5. D6 D7. D8 D9. "
        "E0 E1. E2 E3. E4 E5. E6 E7. E8 E9."
    )

    para_max = int(0.5 * overlap * max_size)

    def get_data(t):
        return split_paragraphs(t, max_chunk_size=para_max, batch_paragraphs=True)

    with patch.object(mod, "get_embedding_engine", side_effect=mock_engine):
        chunker = TextChunkerWithOverlap(
            _doc(),
            text_gen_factory(text),
            max_chunk_size=max_size,
            chunk_overlap_ratio=overlap,
            get_chunk_data=get_data,
        )
        chunks = [c async for c in chunker.read()]

    assert len(chunks) == 3
    assert all(c.chunk_index == i for i, c in enumerate(chunks))
    assert "A0" in chunks[0].text and "B9" in chunks[0].text
    assert "B" in chunks[1].text and "C" in chunks[1].text
    assert "E9" in chunks[2].text

    # 检查重叠
    end_0 = chunks[0].text.split()[-4:]
    words_1 = chunks[1].text.split()
    assert any(w in words_1 for w in end_0)
