"""集成测试：DefaultUrlCrawler 对单个 URL 的抓取能力验证。"""

from __future__ import annotations

import pytest

from m_flow.ingestion.web_scraper import DefaultUrlCrawler

SAMPLE_URL = "http://example.com/"


@pytest.mark.asyncio
async def test_single_page_crawl_returns_html():
    """使用 example.com 验证爬虫返回正确的 dict 结构，value 为 str 类型的 HTML 内容。"""
    scraper = DefaultUrlCrawler()
    fetched = await scraper.fetch_urls(SAMPLE_URL)

    assert isinstance(fetched, dict), "返回值应为 dict 类型"
    assert len(fetched) == 1, f"应仅包含 1 个条目，实际 {len(fetched)}"
    assert isinstance(fetched[SAMPLE_URL], str), "抓取内容应为 str"
