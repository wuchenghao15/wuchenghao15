"""
Web Scraping Integration Tests for M-flow.

Tests various web scraping configurations including:
- BeautifulSoup-based scraping (with and without incremental loading)
- Tavily API integration
- Scheduled cron-based scraping tasks
"""

from __future__ import annotations

import asyncio
from typing import Any

import m_flow
from m_flow.ingestion.web_scraper import cron_web_scraper_task
from m_flow.ingestion.web_scraper.config import DefaultCrawlerConfig


# ============================================================================
# Test Constants
# ============================================================================

QUOTES_SCRAPE_URL = "https://quotes.toscrape.com/"
BOOKS_SCRAPE_URL = "https://books.toscrape.com/"

EINSTEIN_QUOTE_QUERY = (
    "Who said 'The world as we have created it is a process of our thinking. "
    "It cannot be changed without changing our thinking'?"
)
BOOK_PRICE_QUERY = "What is the price of 'A Light in the Attic' book?"

EXPECTED_AUTHOR = "Albert Einstein"
EXPECTED_PRICE = "51.77"


# ============================================================================
# Helper Functions
# ============================================================================


async def clear_mflow_state(clear_metadata: bool = True) -> None:
    """Reset M-flow data and system state for test isolation."""
    await m_flow.prune.prune_data()
    if clear_metadata:
        await m_flow.prune.prune_system(metadata=True)
    else:
        await m_flow.prune.prune_system()


def build_quotes_extraction_rules() -> dict[str, Any]:
    """Create extraction rules for quotes website."""
    return {
        "quotes": {"selector": ".quote span.text", "all": True},
        "authors": {"selector": ".quote small", "all": True},
    }


def build_books_extraction_rules() -> dict[str, str]:
    """Create extraction rules for books website."""
    return {
        "titles": "article.product_pod h3 a",
        "prices": "article.product_pod p.price_color",
    }


def build_combined_extraction_rules() -> dict[str, str]:
    """Create combined rules for multi-site scraping."""
    return {
        "quotes": ".quote .text",
        "authors": ".quote .author",
        "titles": "article.product_pod h3 a",
        "prices": "article.product_pod p.price_color",
    }


async def verify_einstein_found(search_results: list) -> None:
    """Assert that Albert Einstein is found in search results."""
    assert any(EXPECTED_AUTHOR in str(result) for result in search_results), (
        f"Expected to find '{EXPECTED_AUTHOR}' in results"
    )


async def verify_book_price_found(search_results: list) -> None:
    """Assert that book price is found in search results."""
    assert any(EXPECTED_PRICE in str(result) for result in search_results), (
        f"Expected to find price '{EXPECTED_PRICE}' in results"
    )


# ============================================================================
# BeautifulSoup-based Tests
# ============================================================================


async def test_web_scraping_using_bs4() -> None:
    """Test web scraping with BeautifulSoup in full loading mode."""
    await clear_mflow_state(clear_metadata=False)

    crawler_config = DefaultCrawlerConfig(
        concurrency=5,
        crawl_delay=0.5,
        timeout=15.0,
        max_retries=2,
        retry_delay_factor=0.5,
        extraction_rules=build_quotes_extraction_rules(),
        use_playwright=False,
    )

    await m_flow.add(
        data=QUOTES_SCRAPE_URL,
        soup_crawler_config=crawler_config,
        incremental_loading=False,
    )

    await m_flow.memorize()

    search_results = await m_flow.search(
        EINSTEIN_QUOTE_QUERY,
        query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    )

    await verify_einstein_found(search_results)
    print("BS4 scraping test completed successfully.")


async def test_web_scraping_using_bs4_and_incremental_loading() -> None:
    """Test web scraping with BeautifulSoup in incremental mode."""
    await clear_mflow_state()

    crawler_config = DefaultCrawlerConfig(
        concurrency=1,
        crawl_delay=0.1,
        timeout=10.0,
        max_retries=1,
        retry_delay_factor=0.5,
        extraction_rules=build_books_extraction_rules(),
        use_playwright=False,
        structured=True,
    )

    await m_flow.add(
        data=BOOKS_SCRAPE_URL,
        soup_crawler_config=crawler_config,
        incremental_loading=True,
    )

    await m_flow.memorize()

    search_results = await m_flow.search(
        BOOK_PRICE_QUERY,
        query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    )

    await verify_book_price_found(search_results)
    print("BS4 incremental scraping test completed successfully.")


# ============================================================================
# Tavily API Tests
# ============================================================================


async def test_web_scraping_using_tavily() -> None:
    """Test web scraping using Tavily API in full loading mode."""
    await clear_mflow_state()

    await m_flow.add(
        data=QUOTES_SCRAPE_URL,
        incremental_loading=False,
    )

    await m_flow.memorize()

    search_results = await m_flow.search(
        EINSTEIN_QUOTE_QUERY,
        query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    )

    await verify_einstein_found(search_results)
    print("Tavily scraping test completed successfully.")


async def test_web_scraping_using_tavily_and_incremental_loading() -> None:
    """Test web scraping using Tavily API in incremental mode."""
    await clear_mflow_state()

    await m_flow.add(
        data=QUOTES_SCRAPE_URL,
        incremental_loading=True,
    )

    await m_flow.memorize()

    search_results = await m_flow.search(
        EINSTEIN_QUOTE_QUERY,
        query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    )

    await verify_einstein_found(search_results)
    print("Tavily incremental scraping test completed successfully.")


# ============================================================================
# Cron Job Tests
# ============================================================================


async def test_cron_web_scraper() -> None:
    """Test scheduled cron-based web scraping across multiple URLs."""
    await clear_mflow_state()

    target_urls = [QUOTES_SCRAPE_URL, BOOKS_SCRAPE_URL]

    await cron_web_scraper_task(
        url=target_urls,
        job_name="cron_scraping_job",
        extraction_rules=build_combined_extraction_rules(),
    )

    # Verify quotes data
    quotes_results = await m_flow.search(
        EINSTEIN_QUOTE_QUERY,
        query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    )
    await verify_einstein_found(quotes_results)

    # Verify books data
    books_results = await m_flow.search(
        BOOK_PRICE_QUERY,
        query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    )
    await verify_book_price_found(books_results)

    print("Cron web scraper test completed successfully.")


# ============================================================================
# Main Entry Point
# ============================================================================


async def run_all_tests() -> None:
    """Execute all web scraping tests in sequence."""
    test_cases = [
        ("BS4 incremental loading", test_web_scraping_using_bs4_and_incremental_loading),
        ("BS4 full loading", test_web_scraping_using_bs4),
        ("Tavily incremental loading", test_web_scraping_using_tavily_and_incremental_loading),
        ("Tavily full loading", test_web_scraping_using_tavily),
        ("Cron job scraper", test_cron_web_scraper),
    ]

    for test_name, test_func in test_cases:
        print(f"\n--- Running: {test_name} ---")
        await test_func()

    print("\n=== All web scraping tests passed! ===")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
