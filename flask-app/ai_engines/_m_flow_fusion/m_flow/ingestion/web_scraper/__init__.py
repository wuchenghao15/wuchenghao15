"""
Web scraping utilities.
"""

from __future__ import annotations

from .default_url_crawler import DefaultUrlCrawler
from .utils import fetch_page_content

_LAZY_ATTRS = {
    "cron_web_scraper_task": ("web_scraper_task", "cron_web_scraper_task"),
    "web_scraper_task": ("web_scraper_task", "web_scraper_task"),
}


def __getattr__(attr: str):
    if attr in _LAZY_ATTRS:
        mod, name = _LAZY_ATTRS[attr]
        import importlib

        m = importlib.import_module(f".{mod}", __name__)
        return getattr(m, name)
    raise AttributeError(f"No attribute {attr} in {__name__}")


__all__ = ["fetch_page_content", "DefaultUrlCrawler"]
