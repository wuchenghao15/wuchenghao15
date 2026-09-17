"""Scrape a Wikipedia page with CSS selectors and build a knowledge graph."""

import asyncio
import m_flow

PAGE = "https://en.wikipedia.org/wiki/Large_language_model"

SELECTORS = {
    "title": {"selector": "title"},
    "headings": {"selector": "h1, h2, h3", "all": True},
    "links": {"selector": "a", "attr": "href", "all": True},
    "paragraphs": {"selector": "p", "all": True},
}


async def run():
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    print(f"Scraping {PAGE} ...")
    await m_flow.add(
        PAGE,
        incremental_loading=False,
        preferred_loaders={"beautiful_soup_loader": {"extraction_rules": SELECTORS}},
    )

    await m_flow.memorize()
    await m_flow.visualize_graph()
    print("Graph ready.")


if __name__ == "__main__":
    asyncio.run(run())
