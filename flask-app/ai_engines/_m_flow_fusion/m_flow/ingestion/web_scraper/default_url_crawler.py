"""
URL Crawler for M-flow web scraping.

Provides an async crawler with rate limiting, robots.txt compliance,
and optional Playwright rendering for JavaScript-heavy pages.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx

from m_flow.ingestion.web_scraper.types import UrlsToHtmls
from m_flow.shared.logging_utils import get_logger

_logger = get_logger()

# Optional dependencies
try:
    from protego import Protego
except ImportError:
    _logger.warning("protego not installed: pip install protego>=0.1")
    Protego = None

try:
    from playwright.async_api import async_playwright
except ImportError:
    _logger.warning("playwright not installed: pip install playwright>=1.9.0")
    async_playwright = None


@dataclass
class _RobotsEntry:
    """Cached robots.txt parsing result."""

    parser: Any
    delay: float
    created: float = field(default_factory=time.time)


class DefaultUrlCrawler:
    """
    Asynchronous URL fetcher with rate limiting and robots.txt support.

    Supports both simple HTTP fetching and Playwright rendering for
    JavaScript-heavy pages. Respects robots.txt crawl-delay directives.
    """

    def __init__(
        self,
        *,
        concurrency: int = 5,
        crawl_delay: float = 0.5,
        max_crawl_delay: Optional[float] = 10.0,
        timeout: float = 15.0,
        max_retries: int = 2,
        retry_backoff: float = 0.5,
        headers: Optional[Dict[str, str]] = None,
        robots_ttl: float = 3600.0,
    ) -> None:
        """
        Initialize crawler with rate limiting configuration.

        Args:
            concurrency: Maximum parallel requests.
            crawl_delay: Default delay between same-domain requests.
            max_crawl_delay: Cap on robots.txt crawl-delay (None = no cap).
            timeout: Request timeout in seconds.
            max_retries: Retry attempts on failure.
            retry_backoff: Exponential backoff multiplier.
            headers: Custom HTTP headers.
            robots_ttl: Cache TTL for robots.txt in seconds.
        """
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)
        self._delay = crawl_delay
        self._max_delay = max_crawl_delay
        self._timeout = timeout
        self._retries = max_retries
        self._backoff = retry_backoff
        self._headers = headers or {"User-Agent": "MflowBot/1.0"}
        self._robots_ttl = robots_ttl

        self._domain_times: Dict[str, float] = {}
        self._robots_cache: Dict[str, _RobotsEntry] = {}
        self._http: Optional[httpx.AsyncClient] = None
        self._robots_lock = asyncio.Lock()

    async def _init_client(self) -> None:
        """Lazy-initialize the HTTP client."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                headers=self._headers,
            )

    async def close(self) -> None:
        """Release HTTP client resources."""
        if self._http:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self):
        await self._init_client()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    @lru_cache(maxsize=1024)
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc
        except Exception:
            return url

    @lru_cache(maxsize=1024)
    def _extract_root(self, url: str) -> str:
        """Get scheme://domain from URL."""
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    async def _apply_rate_limit(self, url: str, delay_sec: Optional[float] = None) -> None:
        """Wait if necessary to respect rate limits."""
        domain = self._extract_domain(url)
        last_time = self._domain_times.get(domain)
        target_delay = delay_sec if delay_sec is not None else self._delay

        if last_time is None:
            self._domain_times[domain] = time.time()
            return

        elapsed = time.time() - last_time
        remaining = target_delay - elapsed

        if remaining > 0:
            _logger.debug(f"Rate limit: wait {remaining:.2f}s for {domain}")
            await asyncio.sleep(remaining)

        self._domain_times[domain] = time.time()

    async def _get_cached_robots(self, root: str) -> Optional[_RobotsEntry]:
        """Return cached robots.txt if still valid."""
        if Protego is None:
            return None

        entry = self._robots_cache.get(root)
        if entry and (time.time() - entry.created) < self._robots_ttl:
            return entry
        return None

    async def _load_robots(self, root: str) -> _RobotsEntry:
        """Fetch and parse robots.txt, caching the result."""
        async with self._robots_lock:
            cached = await self._get_cached_robots(root)
            if cached:
                return cached

            robots_url = f"{root}/robots.txt"
            content = ""

            try:
                await self._init_client()
                await self._apply_rate_limit(robots_url, self._delay)
                resp = await self._http.get(robots_url, timeout=5.0)
                if resp.status_code == 200:
                    content = resp.text
            except Exception as err:
                _logger.debug(f"robots.txt fetch failed for {root}: {err}")

            parser = Protego.parse(content) if content.strip() else None

            # Determine crawl delay
            delay = self._delay
            if parser:
                agent = self._get_user_agent()
                d = parser.crawl_delay(agent) or parser.crawl_delay("*")
                if d:
                    if self._max_delay and d > self._max_delay:
                        _logger.info(f"Capping crawl_delay {d}s to {self._max_delay}s")
                        delay = self._max_delay
                    else:
                        delay = d

            entry = _RobotsEntry(parser=parser, delay=delay)
            self._robots_cache[root] = entry
            return entry

    def _get_user_agent(self) -> str:
        """Extract User-Agent from headers."""
        for k, v in self._headers.items():
            if k.lower() == "user-agent":
                return v
        return "*"

    async def _check_allowed(self, url: str) -> bool:
        """Check if URL is permitted by robots.txt."""
        if Protego is None:
            return True

        try:
            root = self._extract_root(url)
            entry = await self._get_cached_robots(root)
            if entry is None:
                entry = await self._load_robots(root)

            if entry.parser is None:
                return True

            agent = self._get_user_agent()
            return entry.parser.can_fetch(agent, url) or entry.parser.can_fetch("*", url)
        except Exception:
            return True

    async def _get_delay_for(self, url: str) -> float:
        """Get appropriate crawl delay for URL."""
        if Protego is None:
            return self._delay

        try:
            root = self._extract_root(url)
            entry = await self._get_cached_robots(root)
            if entry is None:
                entry = await self._load_robots(root)
            return entry.delay
        except Exception:
            return self._delay

    async def _fetch_with_httpx(self, url: str) -> str:
        """Fetch URL content using httpx with retries."""
        await self._init_client()
        assert self._http is not None

        delay = await self._get_delay_for(url)
        attempt = 0

        while True:
            try:
                await self._apply_rate_limit(url, delay)
                resp = await self._http.get(url)
                resp.raise_for_status()
                _logger.debug(f"Fetched {url}: {len(resp.text)} bytes")
                return resp.text
            except Exception as err:
                attempt += 1
                if attempt > self._retries:
                    _logger.error(f"Failed {url} after {attempt} attempts: {err}")
                    raise

                wait = self._backoff * (2 ** (attempt - 1))
                _logger.warning(f"Retry {attempt} for {url} in {wait:.1f}s")
                await asyncio.sleep(wait)

    async def _render_playwright(
        self,
        url: str,
        js_wait: float = 1.0,
        timeout: Optional[float] = None,
    ) -> str:
        """Render URL using Playwright for JavaScript content."""
        if async_playwright is None:
            raise RuntimeError("Playwright not available")

        t = timeout or self._timeout
        attempt = 0

        while True:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    try:
                        ctx = await browser.new_context()
                        page = await ctx.new_page()
                        await page.goto(url, wait_until="networkidle", timeout=int(t * 1000))

                        if js_wait > 0:
                            await asyncio.sleep(js_wait)

                        html = await page.content()
                        _logger.debug(f"Rendered {url}: {len(html)} bytes")
                        return html
                    finally:
                        await browser.close()
            except Exception as err:
                attempt += 1
                if attempt > self._retries:
                    _logger.error(f"Playwright failed for {url}: {err}")
                    raise

                wait = self._backoff * (2 ** (attempt - 1))
                _logger.warning(f"Playwright retry {attempt} for {url}")
                await asyncio.sleep(wait)

    async def fetch_urls(
        self,
        urls: Union[str, List[str]],
        *,
        use_playwright: bool = False,
        playwright_js_wait: float = 0.8,
    ) -> UrlsToHtmls:
        """
        Fetch HTML content from one or more URLs.

        Args:
            urls: Single URL or list of URLs.
            use_playwright: Use browser rendering for JS content.
            playwright_js_wait: Wait time for JS execution.

        Returns:
            Mapping of URL to HTML content (empty string on failure).
        """
        if isinstance(urls, str):
            url_list = [urls]
        elif isinstance(urls, list):
            url_list = urls
        else:
            raise ValueError(f"Invalid urls type: {type(urls)}")

        async def _process(u: str) -> tuple[str, str]:
            async with self._semaphore:
                try:
                    if not await self._check_allowed(u):
                        _logger.warning(f"Blocked by robots.txt: {u}")
                        return u, ""

                    if use_playwright:
                        html = await self._render_playwright(u, js_wait=playwright_js_wait)
                    else:
                        html = await self._fetch_with_httpx(u)

                    return u, html
                except Exception as err:
                    _logger.error(f"Error fetching {u}: {err}")
                    return u, ""

        tasks = [asyncio.create_task(_process(u)) for u in url_list]
        results: Dict[str, str] = {}

        for coro in asyncio.as_completed(tasks):
            url, html = await coro
            results[url] = html

        _logger.info(f"Fetched {len(results)} URL(s)")
        return results
