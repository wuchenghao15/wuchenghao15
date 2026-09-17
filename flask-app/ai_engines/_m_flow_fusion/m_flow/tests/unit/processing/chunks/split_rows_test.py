"""
行分块测试
"""

from __future__ import annotations

from itertools import product

import numpy as np
import pytest

from m_flow.adapters.vector.embeddings import get_embedding_engine
from m_flow.ingestion.chunks import split_rows

_INPUT = "name: John, age: 30, city: New York, country: USA"
_SIZES = [8, 32]
_CASES = list(product([_INPUT], _SIZES))


class TestChunkByRow:
    """行分块测试套件"""

    @pytest.mark.parametrize("text,size", _CASES)
    def test_isomorphism(self, text, size):
        """测试分块后重组等于原文"""
        chunks = split_rows(text, size)
        rebuilt = ", ".join(c["text"] for c in chunks)
        assert rebuilt == text

    @pytest.mark.parametrize("text,size", _CASES)
    def test_chunk_size_limit(self, text, size):
        """测试分块不超过最大长度"""
        chunks = list(split_rows(data=text, max_chunk_size=size))
        engine = get_embedding_engine()

        lengths = np.array([engine.tokenizer.count_tokens(c["text"]) for c in chunks])
        assert np.all(lengths <= size), f"超长块: {lengths[lengths > size]}"

    @pytest.mark.parametrize("text,size", _CASES)
    def test_index_sequence(self, text, size):
        """测试分块索引递增"""
        chunks = split_rows(data=text, max_chunk_size=size)
        indices = np.array([c["chunk_index"] for c in chunks])
        assert np.array_equal(indices, np.arange(len(indices)))
