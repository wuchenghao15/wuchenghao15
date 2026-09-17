"""
段落分块测试 - 参数化测试
"""

from __future__ import annotations

from itertools import product

import numpy as np
import pytest

from m_flow.adapters.vector.embeddings import get_embedding_engine
from m_flow.ingestion.chunks import split_paragraphs
from .test_input import INPUT_TEXTS

_BATCH_MODES = [True, False]
_CHUNK_SIZES = [512, 1024, 4096]

_ALL_CASES = list(product(INPUT_TEXTS.values(), _CHUNK_SIZES, _BATCH_MODES))


class TestParagraphChunking:
    """段落分块测试套件"""

    @pytest.mark.parametrize("text,size,batch", _ALL_CASES)
    def test_isomorphism(self, text, size, batch):
        """测试分块后重组等于原文"""
        chunks = split_paragraphs(text, size, batch)
        rebuilt = "".join(c["text"] for c in chunks)
        assert rebuilt == text, f"长度不匹配: {len(text)} vs {len(rebuilt)}"

    @pytest.mark.parametrize("text,size,batch", _ALL_CASES)
    def test_chunk_size_limit(self, text, size, batch):
        """测试分块不超过最大长度"""
        chunks = list(split_paragraphs(data=text, max_chunk_size=size, batch_paragraphs=batch))
        engine = get_embedding_engine()

        lengths = np.array([engine.tokenizer.count_tokens(c["text"]) for c in chunks])
        oversized = lengths[lengths > size]
        assert len(oversized) == 0, f"超长块: {oversized}"

    @pytest.mark.parametrize("text,size,batch", _ALL_CASES)
    def test_chunk_index_sequence(self, text, size, batch):
        """测试分块索引递增"""
        chunks = split_paragraphs(data=text, max_chunk_size=size, batch_paragraphs=batch)
        indices = np.array([c["chunk_index"] for c in chunks])
        expected = np.arange(len(indices))
        assert np.array_equal(indices, expected), f"索引不连续: {indices}"
