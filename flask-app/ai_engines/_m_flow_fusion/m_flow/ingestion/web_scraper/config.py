"""
Web Scraper Configuration
=========================

Configuration models for web scraping and crawling operations.
Supports multiple backend providers and customizable crawl behavior.
"""

from __future__ import annotations

import os
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


class TavilyConfig(BaseModel):
    """
    Tavily web search API settings.

    Tavily provides structured web search capabilities
    for knowledge extraction.

    Attributes
    ----------
    api_key : str | None
        Tavily API key from environment.
    extract_depth : str
        Content extraction depth level.
    proxies : dict | None
        Optional proxy configuration.
    timeout : int
        Request timeout in seconds.
    """

    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    extract_depth: Literal["basic", "advanced"] = "basic"
    proxies: Optional[Dict[str, str]] = None
    timeout: int = Field(default=10, ge=1, le=60)


class DefaultCrawlerConfig(BaseModel):
    """
    Default web crawler settings.

    Controls the behavior of the built-in web crawler
    including rate limiting, retries, and rendering options.

    Attributes
    ----------
    concurrency : int
        Maximum concurrent requests.
    crawl_delay : float
        Minimum delay between requests (seconds).
    max_crawl_delay : float | None
        Maximum delay cap for backoff.
    timeout : float
        Request timeout (seconds).
    max_retries : int
        Number of retry attempts.
    retry_delay_factor : float
        Multiplier for exponential backoff.
    headers : dict | None
        Custom HTTP headers.
    use_playwright : bool
        Enable JavaScript rendering.
    playwright_js_wait : float
        Wait time for JS execution.
    robots_cache_ttl : float
        robots.txt cache lifetime.
    join_all_matches : bool
        Combine all CSS selector matches.
    """

    concurrency: int = 5
    crawl_delay: float = 0.5
    max_crawl_delay: Optional[float] = 10.0
    timeout: float = 15.0
    max_retries: int = 2
    retry_delay_factor: float = 0.5
    headers: Optional[Dict[str, str]] = None
    use_playwright: bool = False
    playwright_js_wait: float = 0.8
    robots_cache_ttl: float = 3600.0
    join_all_matches: bool = False
