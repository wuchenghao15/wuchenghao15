"""
Web Scraper Domain Models
=========================

Pydantic models representing web pages, websites, and scraping jobs
for the web scraping subsystem.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from m_flow.core import MemoryNode


class WebPage(MemoryNode):
    """
    Represents a single scraped web page.

    Stores the page content along with metadata about
    when it was scraped and its characteristics.

    Attributes
    ----------
    name : str | None
        Optional page title.
    content : str
        Raw or processed page content.
    content_hash : str
        Hash for change detection.
    scraped_at : datetime
        When the page was scraped.
    last_modified : datetime | None
        Server-reported last modification time.
    status_code : int
        HTTP response status code.
    content_type : str
        MIME type of the response.
    page_size : int
        Content length in bytes.
    extraction_rules : dict
        Rules used for content extraction.
    description : str
        Page description or summary.
    """

    name: Optional[str] = None
    content: str
    content_hash: str
    scraped_at: datetime
    last_modified: Optional[datetime] = None
    status_code: int
    content_type: str
    page_size: int
    extraction_rules: Dict[str, Any]
    description: str

    metadata: dict = {"index_fields": ["name", "description", "content"]}


class WebSite(MemoryNode):
    """
    Represents a website or domain being scraped.

    Tracks site-level configuration and crawl statistics.

    Attributes
    ----------
    name : str
        Site identifier or name.
    base_url : str
        Root URL of the website.
    robots_txt : str | None
        Cached robots.txt content.
    crawl_delay : float
        Delay between requests.
    last_crawled : datetime
        Most recent crawl time.
    page_count : int
        Number of pages discovered.
    scraping_config : dict
        Site-specific scraping settings.
    description : str
        Site description.
    """

    name: str
    base_url: str
    robots_txt: Optional[str] = None
    crawl_delay: float
    last_crawled: datetime
    page_count: int
    scraping_config: Dict[str, Any]
    description: str

    metadata: dict = {"index_fields": ["name", "description"]}


class ScrapingJob(MemoryNode):
    """
    Represents a scheduled scraping job.

    Manages job state and scheduling for recurring scrapes.

    Attributes
    ----------
    name : str
        Job identifier.
    urls : list[str]
        URLs to scrape.
    schedule : str | None
        Cron-style schedule expression.
    status : str
        Current job state (active/paused/completed/failed).
    last_run : datetime | None
        Most recent execution time.
    next_run : datetime | None
        Scheduled next execution.
    description : str
        Job description.
    """

    name: str
    urls: List[str]
    schedule: Optional[str] = None
    status: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    description: str

    metadata: dict = {"index_fields": ["name", "description"]}
