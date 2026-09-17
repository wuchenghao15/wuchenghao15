"""
对话历史测试
"""

from __future__ import annotations

import importlib

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from m_flow.context_global_variables import session_user


def _mock_cache(history=None):
    """创建模拟缓存引擎"""
    cache = AsyncMock()
    cache.get_latest_qa = AsyncMock(return_value=history or [])
    cache.add_qa = AsyncMock(return_value=None)
    return cache


def _mock_user():
    """创建模拟用户"""
    u = MagicMock()
    u.id = "user-123"
    return u


_cache_mod = importlib.import_module("m_flow.adapters.cache.get_cache_engine")


class TestConversationHistory:
    """对话历史测试"""

    @pytest.mark.asyncio
    async def test_empty_history(self):
        """测试空历史返回空字符串"""
        session_user.set(_mock_user())
        cache = _mock_cache([])

        with patch.object(_cache_mod, "get_cache_engine", return_value=cache):
            from m_flow.retrieval.utils.session_cache import get_conversation_history

            result = await get_conversation_history(session_id="s1")

        assert result == ""

    @pytest.mark.asyncio
    async def test_format_history(self):
        """测试历史格式化"""
        session_user.set(_mock_user())

        history = [
            {
                "time": "2024-01-15 10:30:45",
                "question": "什么是AI？",
                "context": "AI是人工智能",
                "answer": "AI代表人工智能",
            }
        ]
        cache = _mock_cache(history)

        with patch.object(_cache_mod, "get_cache_engine", return_value=cache):
            with patch("m_flow.retrieval.utils.session_cache.CacheConfig") as MockCfg:
                MockCfg.return_value = MagicMock(caching=True)
                from m_flow.retrieval.utils.session_cache import get_conversation_history

                result = await get_conversation_history(session_id="s1")

                assert "Previous conversation:" in result
                assert "[2024-01-15 10:30:45]" in result
                assert "QUESTION: 什么是AI？" in result

    @pytest.mark.asyncio
    async def test_save_history(self):
        """测试保存历史"""
        session_user.set(_mock_user())
        cache = _mock_cache([])

        with patch.object(_cache_mod, "get_cache_engine", return_value=cache):
            with patch("m_flow.retrieval.utils.session_cache.CacheConfig") as MockCfg:
                MockCfg.return_value = MagicMock(caching=True)
                from m_flow.retrieval.utils.session_cache import save_conversation_history

                result = await save_conversation_history(
                    query="什么是Python？",
                    context_summary="Python是编程语言",
                    answer="Python是高级编程语言",
                    session_id="my_sess",
                )

                assert result is True
                cache.add_qa.assert_called_once()
                kwargs = cache.add_qa.call_args.kwargs
                assert kwargs["question"] == "什么是Python？"
                assert kwargs["session_id"] == "my_sess"

    @pytest.mark.asyncio
    async def test_default_session(self):
        """测试默认会话ID"""
        session_user.set(_mock_user())
        cache = _mock_cache([])

        with patch.object(_cache_mod, "get_cache_engine", return_value=cache):
            with patch("m_flow.retrieval.utils.session_cache.CacheConfig") as MockCfg:
                MockCfg.return_value = MagicMock(caching=True)
                from m_flow.retrieval.utils.session_cache import save_conversation_history

                await save_conversation_history(
                    query="测试",
                    context_summary="上下文",
                    answer="答案",
                    session_id=None,
                )

                kwargs = cache.add_qa.call_args.kwargs
                assert kwargs["session_id"] == "default_session"
