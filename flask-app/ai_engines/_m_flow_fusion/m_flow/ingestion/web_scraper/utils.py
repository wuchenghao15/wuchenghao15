"""
Web scraping utilities for M-flow ingestion.

Provides high-level functions to fetch web page content using
either the built-in crawler or the Tavily API.
"""

from __future__ import annotations

import os
from typing import List, Union

from m_flow.ingestion.web_scraper.config import DefaultCrawlerConfig, TavilyConfig
from m_flow.ingestion.web_scraper.default_url_crawler import DefaultUrlCrawler
from m_flow.ingestion.web_scraper.types import UrlsToHtmls
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)


async def fetch_page_content(urls: Union[str, List[str]]) -> UrlsToHtmls:
    """
    Fetch HTML/text content from one or more URLs.

    Automatically selects Tavily API if TAVILY_API_KEY is set,
    otherwise falls back to the built-in HTTP crawler.

    Args:
        urls: Single URL string or list of URLs.

    Returns:
        Mapping from URL to fetched content (empty string on failure).
    """
    if os.getenv("TAVILY_API_KEY"):
        _log.info("Tavily API key detected; using Tavily for extraction")
        return await _tavily_extract(urls)

    _log.info("Using default HTTP crawler")
    return await _crawler_fetch(urls)


async def _crawler_fetch(urls: Union[str, List[str]]) -> UrlsToHtmls:
    """Fetch URLs using the built-in DefaultUrlCrawler."""
    cfg = DefaultCrawlerConfig()

    _log.debug(
        f"Crawler config: concurrency={cfg.concurrency}, timeout={cfg.timeout}s, max_delay={cfg.max_crawl_delay}s"
    )

    crawler = DefaultUrlCrawler(
        concurrency=cfg.concurrency,
        crawl_delay=cfg.crawl_delay,
        max_crawl_delay=cfg.max_crawl_delay,
        timeout=cfg.timeout,
        max_retries=cfg.max_retries,
        retry_backoff=cfg.retry_delay_factor,
        headers=cfg.headers,
        robots_ttl=cfg.robots_cache_ttl,
    )

    try:
        url_list = [urls] if isinstance(urls, str) else urls
        _log.info(f"Crawling {len(url_list)} URL(s) (playwright={cfg.use_playwright})")

        results = await crawler.fetch_urls(
            urls,
            use_playwright=cfg.use_playwright,
            playwright_js_wait=cfg.playwright_js_wait,
        )
        _log.info(f"Fetched {len(results)} page(s)")
        return results
    except Exception as err:
        _log.error(f"Crawler error: {err}")
        raise
    finally:
        await crawler.close()


async def _tavily_extract(urls: Union[str, List[str]]) -> UrlsToHtmls:
    """
    Fetch URLs using the Tavily extraction API.

    Requires TAVILY_API_KEY environment variable.
    """
    try:
        from tavily import AsyncTavilyClient
    except ImportError as err:
        _log.error("tavily-python not installed: pip install tavily-python>=0.7.0")
        raise ImportError("Missing tavily-python dependency") from err

    cfg = TavilyConfig()
    url_list = [urls] if isinstance(urls, str) else urls

    _log.debug(f"Tavily config: depth={cfg.extract_depth}, timeout={cfg.timeout}s")

    client = AsyncTavilyClient(
        api_key=cfg.api_key,
        proxies=cfg.proxies,
    )

    _log.info(f"Tavily extract: {len(url_list)} URL(s)")

    response = await client.extract(
        urls,
        format="text",
        extract_depth=cfg.extract_depth,
        timeout=cfg.timeout,
    )

    # Log failures
    failed = response.get("failed_results", [])
    if failed:
        _log.warning(f"Tavily failed for {len(failed)} URL(s): {failed}")

    # Build result mapping
    output: UrlsToHtmls = {}
    for item in response.get("results", []):
        output[item["url"]] = item.get("raw_content", "")

    _log.info(f"Tavily returned {len(output)} result(s)")
    return output


# Public alias
fetch_with_tavily = _tavily_extract
