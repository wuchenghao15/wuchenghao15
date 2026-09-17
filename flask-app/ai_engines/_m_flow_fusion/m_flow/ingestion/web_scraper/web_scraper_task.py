"""
Web scraping tasks for M-flow.

Provides scheduled and on-demand web scraping with graph storage.
Creates WebPage, WebSite, and ScrapingJob nodes in the graph database.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
from uuid import NAMESPACE_OID, uuid5

from m_flow.adapters.graph import get_graph_provider
from m_flow.core.domain.operations.setup import setup
from m_flow.shared.logging_utils import get_logger
from m_flow.storage.index_graph_links import index_relations
from m_flow.storage.index_memory_nodes import index_memory_nodes

from .config import DefaultCrawlerConfig, TavilyConfig
from .models import ScrapingJob, WebPage, WebSite
from .utils import fetch_page_content

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    raise ImportError("APScheduler required: pip install APScheduler>=3.10")

_log = get_logger(__name__)
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Return singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def cron_web_scraper_task(
    url: Union[str, List[str]],
    *,
    schedule: Optional[str] = None,
    extraction_rules: Optional[dict] = None,
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", ""),
    soup_crawler_config: Optional[DefaultCrawlerConfig] = None,
    tavily_config: Optional[TavilyConfig] = None,
    job_name: str = "scraping",
) -> Any:
    """
    Schedule or immediately execute a web scraping task.

    Args:
        url: URL or list of URLs to scrape.
        schedule: Cron expression for recurring runs.
        extraction_rules: CSS selector rules for BeautifulSoup.
        tavily_api_key: Tavily API key.
        soup_crawler_config: BeautifulSoup crawler settings.
        tavily_config: Tavily API settings.
        job_name: Identifier for the scraping job.

    Returns:
        Result of immediate run, or None if scheduled.
    """
    ts = datetime.now()
    job_id = job_name or f"scrape_{ts:%Y%m%d_%H%M%S}"

    task_kwargs = {
        "url": url,
        "schedule": schedule,
        "extraction_rules": extraction_rules,
        "tavily_api_key": tavily_api_key,
        "soup_crawler_config": soup_crawler_config,
        "tavily_config": tavily_config,
        "job_name": job_id,
    }

    if schedule:
        try:
            trigger = CronTrigger.from_crontab(schedule)
        except ValueError as err:
            raise ValueError(f"Invalid cron: '{schedule}'") from err

        sched = get_scheduler()
        sched.add_job(
            web_scraper_task,
            kwargs=task_kwargs,
            trigger=trigger,
            id=job_id,
            name=f"WebScraper_{uuid5(NAMESPACE_OID, job_id)}",
            replace_existing=True,
        )
        if not sched.running:
            sched.start()
        return None

    _log.info(f"Executing scrape task immediately: {job_id}")
    return await web_scraper_task(**task_kwargs)


def _validate_config(
    api_key: str,
    rules: Optional[dict],
    tv_cfg: Optional[TavilyConfig],
    bs_cfg: Optional[DefaultCrawlerConfig],
) -> Tuple[Optional[DefaultCrawlerConfig], Optional[TavilyConfig], str]:
    """
    Resolve and validate scraping configuration.

    Returns:
        Tuple of (bs_config, tavily_config, tool_name).
    """
    tool = "beautifulsoup"

    if rules and not bs_cfg:
        bs_cfg = DefaultCrawlerConfig(extraction_rules=rules)

    if api_key:
        if not tv_cfg:
            tv_cfg = TavilyConfig(api_key=api_key)
        else:
            tv_cfg.api_key = api_key

        if not rules and not bs_cfg:
            tool = "tavily"

    if not tv_cfg and not bs_cfg:
        raise TypeError("Must provide either tavily_config or soup_crawler_config")

    return bs_cfg, tv_cfg, tool


def _build_job_description(
    name: str,
    urls: List[str],
    status: str,
    schedule: Optional[str],
    last_run: datetime,
    next_run: Optional[datetime],
) -> str:
    """Format ScrapingJob description string."""
    next_str = next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "Not scheduled"
    return (
        f"Job: {name}\n"
        f"URLs: {', '.join(urls)}\n"
        f"Status: {status}\n"
        f"Schedule: {schedule or 'None'}\n"
        f"Last run: {last_run:%Y-%m-%d %H:%M:%S}\n"
        f"Next run: {next_str}"
    )


def _build_site_description(
    domain: str,
    base_url: str,
    ts: datetime,
    page_count: int,
    tool: str,
    has_robots: bool,
    delay: float,
) -> str:
    """Format WebSite description string."""
    robots_str = "Available" if has_robots else "Not set"
    return (
        f"Site: {domain}\n"
        f"Base: {base_url}\n"
        f"Crawled: {ts:%Y-%m-%d %H:%M:%S}\n"
        f"Pages: {page_count}\n"
        f"Tool: {tool}\n"
        f"Robots: {robots_str}\n"
        f"Delay: {delay}s"
    )


def _build_page_description(
    path: str,
    url: str,
    ts: datetime,
    content: str,
    size: int,
) -> str:
    """Format WebPage description string."""
    preview = content[:500] + ("..." if len(content) > 500 else "")
    return (
        f"Page: {path or 'Home'}\n"
        f"URL: {url}\n"
        f"Scraped: {ts:%Y-%m-%d %H:%M:%S}\n"
        f"Content: {preview}\n"
        f"Type: text/html\n"
        f"Size: {size} bytes\n"
        f"Status: 200"
    )


async def web_scraper_task(
    url: Union[str, List[str]],
    *,
    schedule: Optional[str] = None,
    extraction_rules: Optional[dict] = None,
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", ""),
    soup_crawler_config: Optional[DefaultCrawlerConfig] = None,
    tavily_config: Optional[TavilyConfig] = None,
    job_name: Optional[str] = None,
) -> Any:
    """
    Scrape URLs and store results in the graph database.

    Creates or updates WebPage, WebSite, and ScrapingJob nodes with
    relationships: is_scraping (Job->Site) and is_part_of (Page->Site).

    Args:
        url: URL or list of URLs.
        schedule: Cron schedule string.
        extraction_rules: BeautifulSoup extraction config.
        tavily_api_key: Tavily API key.
        soup_crawler_config: BeautifulSoup crawler config.
        tavily_config: Tavily API config.
        job_name: Job identifier.

    Returns:
        Graph data from database.
    """
    await setup()
    db = await get_graph_provider()

    urls = [url] if isinstance(url, str) else url
    bs_cfg, tv_cfg, tool = _validate_config(tavily_api_key, extraction_rules, tavily_config, soup_crawler_config)

    ts = datetime.now()
    job_id = job_name or f"scrape_{ts:%Y%m%d_%H%M%S}"

    trigger = CronTrigger.from_crontab(schedule) if schedule else None
    next_run = trigger.get_next_fire_time(None, ts) if trigger else None

    # Check existing job
    existing_job = await db.get_node(uuid5(NAMESPACE_OID, job_id))

    scraping_job = ScrapingJob(
        id=uuid5(NAMESPACE_OID, job_id),
        name=job_id,
        urls=urls,
        status="active",
        schedule=schedule,
        last_run=ts,
        next_run=next_run,
        description=_build_job_description(job_id, urls, "active", schedule, ts, next_run),
    )

    if existing_job:
        await db.add_node(scraping_job)

    # Fetch content
    results = await fetch_page_content(urls)

    sites: Dict[str, WebSite] = {}
    pages: List[WebPage] = []

    for page_url, content in results.items():
        parsed = urlparse(page_url)
        domain = parsed.netloc
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Create/update site
        if base not in sites:
            sites[base] = WebSite(
                id=uuid5(NAMESPACE_OID, domain),
                name=domain,
                base_url=base,
                robots_txt=None,
                crawl_delay=0.5,
                last_crawled=ts,
                page_count=1,
                scraping_config={"extraction_rules": extraction_rules or {}, "tool": tool},
                description=_build_site_description(domain, base, ts, 1, tool, False, 0.5),
            )
            if existing_job:
                await db.add_node(sites[base])
        else:
            sites[base].page_count += 1
            sites[base].description = _build_site_description(
                domain, base, ts, sites[base].page_count, tool, False, 0.5
            )
            if existing_job:
                await db.add_node(sites[base])

        # Create page
        content_str = content if isinstance(content, str) else str(content)
        page = WebPage(
            id=uuid5(NAMESPACE_OID, page_url),
            name=page_url,
            content=content_str,
            content_hash=hashlib.sha256(content_str.encode()).hexdigest(),
            scraped_at=ts,
            last_modified=None,
            status_code=200,
            content_type="text/html",
            page_size=len(content_str),
            extraction_rules=extraction_rules or {},
            description=_build_page_description(parsed.path.lstrip("/"), page_url, ts, content_str, len(content_str)),
        )
        pages.append(page)

    # Update job status
    scraping_job.status = "completed" if pages else "failed"
    scraping_job.description = _build_job_description(job_id, urls, scraping_job.status, schedule, ts, next_run)

    # Build graph nodes and edges
    nodes: Dict[Any, Any] = {scraping_job.id: scraping_job}
    edges: List[Tuple[Any, Any, str, dict]] = []

    for site in sites.values():
        nodes[site.id] = site
        edges.append(
            (
                scraping_job.id,
                site.id,
                "is_scraping",
                {
                    "source_node_id": scraping_job.id,
                    "target_node_id": site.id,
                    "relationship_name": "is_scraping",
                },
            )
        )

    for page in pages:
        nodes[page.id] = page
        parsed = urlparse(page.name)
        base = f"{parsed.scheme}://{parsed.netloc}"
        edges.append(
            (
                page.id,
                sites[base].id,
                "is_part_of",
                {
                    "source_node_id": page.id,
                    "target_node_id": sites[base].id,
                    "relationship_name": "is_part_of",
                },
            )
        )

    await db.add_nodes(list(nodes.values()))
    await db.add_edges(edges)
    await index_memory_nodes(list(nodes.values()))
    await index_relations()

    return await db.get_graph_data()


def get_path_after_base(base_url: str, target_url: str) -> str:
    """
    Extract path portion after base URL.

    Args:
        base_url: Base URL (e.g., "https://example.com/docs").
        target_url: Full URL to extract from.

    Returns:
        Path after base, with leading slashes removed.

    Raises:
        ValueError: If domains don't match.
    """
    p_base = urlparse(base_url)
    p_target = urlparse(target_url)

    if p_base.netloc != p_target.netloc:
        raise ValueError("Domain mismatch between base and target")

    base_path = p_base.path.rstrip("/")
    target_path = p_target.path

    if target_path.startswith(base_path):
        return target_path[len(base_path) :].lstrip("/")
    return target_path.lstrip("/")


# Backward compatibility alias
check_arguments = _validate_config
