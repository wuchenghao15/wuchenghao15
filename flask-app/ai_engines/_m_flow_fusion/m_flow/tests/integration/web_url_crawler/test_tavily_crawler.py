"""
Tavily爬虫集成测试
"""

from __future__ import annotations

import os

import pytest

from m_flow.ingestion.web_scraper.utils import fetch_with_tavily

_skip_no_tavily = pytest.mark.skipif(
    os.getenv("TAVILY_API_KEY") is None,
    reason="需要 TAVILY_API_KEY 环境变量",
)


@_skip_no_tavily
@pytest.mark.asyncio
async def test_fetch_url():
    """测试URL抓取"""
    url = "http://example.com/"
    result = await fetch_with_tavily(url)

    assert isinstance(result, dict)
    assert len(result) == 1
    assert url in result
    assert isinstance(result[url], str)
