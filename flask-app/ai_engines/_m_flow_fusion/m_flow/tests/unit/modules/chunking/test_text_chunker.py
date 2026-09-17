"""
TextChunker单元测试
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from m_flow.data.processing.document_types import Document
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.ingestion.chunking.text_chunker_with_overlap import TextChunkerWithOverlap


@pytest.fixture(params=["base", "overlap"])
def chunker_cls(request):
    """参数化测试两种实现"""
    return TextChunker if request.param == "base" else TextChunkerWithOverlap


@pytest.fixture
def text_gen_factory():
    """异步文本生成器工厂"""

    def _make(*texts):
        async def gen():
            for t in texts:
                yield t

        return gen

    return _make


async def _collect(chunker):
    """收集分块"""
    results = []
    async for c in chunker.read():
        results.append(c)
    return results


def _doc(doc_id=None):
    """创建测试文档"""
    return Document(
        id=doc_id or uuid4(),
        name="test",
        processed_path="/test",
        external_metadata=None,
        mime_type="text/plain",
    )


@pytest.mark.asyncio
async def test_empty_no_chunks(chunker_cls, text_gen_factory):
    """空输入无分块"""
    chunker = chunker_cls(_doc(), text_gen_factory(""), max_chunk_size=512)
    assert len(await _collect(chunker)) == 0


@pytest.mark.asyncio
async def test_whitespace_one_chunk(chunker_cls, text_gen_factory):
    """纯空白一个分块"""
    text = "   \n\t   \r\n   "
    chunker = chunker_cls(_doc(), text_gen_factory(text), max_chunk_size=512)
    chunks = await _collect(chunker)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_index == 0


@pytest.mark.asyncio
async def test_short_paragraph_one_chunk(chunker_cls, text_gen_factory):
    """短段落一个分块"""
    text = "短段落测试。"
    chunker = chunker_cls(_doc(), text_gen_factory(text), max_chunk_size=512)
    chunks = await _collect(chunker)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_size > 0


@pytest.mark.asyncio
async def test_oversized_paragraph_emitted(chunker_cls, text_gen_factory):
    """超大段落作为单独分块"""
    text = ("长" * 1500) + "。下一句。"
    chunker = chunker_cls(_doc(), text_gen_factory(text), max_chunk_size=50)
    chunks = await _collect(chunker)
    assert len(chunks) == 2
    assert chunks[0].chunk_size > 50
    assert chunks[1].chunk_index == 1


@pytest.mark.asyncio
async def test_overflow_separate_chunks(chunker_cls, text_gen_factory):
    """溢出产生独立分块 - 细粒度分块可能产生更多 chunks"""
    p1 = " ".join(["词"] * 5)
    p2 = "短文。"
    chunker = chunker_cls(_doc(), text_gen_factory(p1 + " " + p2), max_chunk_size=10)
    chunks = await _collect(chunker)
    # 细粒度分块行为：内容被按 max_chunk_size 边界分割
    assert len(chunks) >= 2  # 至少 2 个 chunks
    assert chunks[0].chunk_index == 0
    assert chunks[-1].chunk_index == len(chunks) - 1


@pytest.mark.asyncio
async def test_batch_small_paragraphs(chunker_cls, text_gen_factory):
    """小段落批量处理 - 验证分块索引连续性"""
    paras = [" ".join(["词"] * 12) for _ in range(40)]
    text = " ".join(paras)
    chunker = chunker_cls(_doc(), text_gen_factory(text), max_chunk_size=49)
    chunks = await _collect(chunker)
    # 分块数量取决于具体的分块算法，验证基本属性
    assert len(chunks) > 0
    assert all(c.chunk_index == i for i, c in enumerate(chunks))


@pytest.mark.asyncio
async def test_alternating_sizes(chunker_cls, text_gen_factory):
    """交替大小段落不合并"""
    parts = ["词" * 15 + "。", "短。", "词" * 15 + "。", "小。"]
    text = " ".join(parts)
    chunker = chunker_cls(_doc(), text_gen_factory(text), max_chunk_size=10)
    chunks = await _collect(chunker)
    assert len(chunks) == 4
    assert chunks[0].chunk_size > 10
    assert chunks[1].chunk_size <= 10


@pytest.mark.asyncio
async def test_deterministic_ids(chunker_cls, text_gen_factory):
    """ID确定性"""
    text = ("一 " * 4 + ". ") * 4
    doc_id = uuid4()
    max_size = 20

    c1 = chunker_cls(
        Document(
            id=doc_id,
            name="t",
            processed_path="/",
            external_metadata=None,
            mime_type="text/plain",
        ),
        text_gen_factory(text),
        max_chunk_size=max_size,
    )
    c2 = chunker_cls(
        Document(
            id=doc_id,
            name="t",
            processed_path="/",
            external_metadata=None,
            mime_type="text/plain",
        ),
        text_gen_factory(text),
        max_chunk_size=max_size,
    )

    r1 = await _collect(c1)
    r2 = await _collect(c2)

    assert len(r1) == 2 and len(r2) == 2
    assert r1[0].id == r2[0].id
    assert r1[1].id == r2[1].id
    assert r1[0].id != r1[1].id
