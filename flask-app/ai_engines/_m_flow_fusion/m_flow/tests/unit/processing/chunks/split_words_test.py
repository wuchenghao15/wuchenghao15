"""
单词分块测试
"""

from __future__ import annotations

import numpy as np
import pytest

from m_flow.ingestion.chunks import split_words
from .test_input import INPUT_TEXTS, INPUT_TEXTS_LONGWORDS

_TEXTS = [
    INPUT_TEXTS["unicode_mix"],
    INPUT_TEXTS["structured_list"],
    INPUT_TEXTS["code_sample"],
    INPUT_TEXTS_LONGWORDS["chinese_prose"],
]


class TestChunkByWord:
    """单词分块测试套件"""

    @pytest.mark.parametrize("text", _TEXTS)
    def test_isomorphism(self, text):
        """测试分块后重组等于原文"""
        chunks = split_words(text)
        rebuilt = "".join(c[0] for c in chunks)
        assert rebuilt == text

    @pytest.mark.parametrize("text", _TEXTS)
    def test_no_internal_spaces(self, text):
        """测试分块内无空格"""
        chunks = np.array(list(split_words(text)))
        no_space = np.array([" " not in c[0].strip() for c in chunks])
        assert np.all(no_space), f"含空格块: {chunks[~no_space]}"
