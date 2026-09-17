"""Low-level pipeline: define custom MemoryNode models and ingest structured JSON."""

import os
import json
import asyncio
from typing import List, Any
from m_flow import prune, visualize_graph
from m_flow.low_level import setup, MemoryNode
from m_flow.data.methods import load_or_create_datasets
from m_flow.auth.methods import get_seed_user
from m_flow.pipelines import run_tasks, Task
from m_flow.storage import persist_memory_nodes


# --- Domain models ---


class Author(MemoryNode):
    name: str
    metadata: dict = {"index_fields": ["name"]}


class Genre(MemoryNode):
    name: str
    metadata: dict = {"index_fields": ["name"]}


class BookCategory(MemoryNode):
    name: str = "Book"
    metadata: dict = {"index_fields": ["name"]}


class Book(MemoryNode):
    title: str
    authors: list[Author]
    genre: Genre
    is_type: BookCategory
    metadata: dict = {"index_fields": ["title"]}


# --- Ingestion logic ---


def parse_catalog(raw_data: List[Any]):
    """Convert raw JSON catalog into MemoryNode instances."""
    author_cache = {}
    genre_cache = {}
    books = []

    for entry in raw_data:
        for author_name in entry.get("authors", []):
            if author_name not in author_cache:
                author_cache[author_name] = Author(name=author_name)

        for book_info in entry.get("books", []):
            genre_name = book_info.get("genre", "General")
            if genre_name not in genre_cache:
                genre_cache[genre_name] = Genre(name=genre_name)

            book = Book(
                title=book_info["title"],
                authors=[author_cache[a] for a in book_info.get("authors", [])],
                genre=genre_cache[genre_name],
                is_type=BookCategory(),
            )
            books.append(book)

    return list(author_cache.values()), list(genre_cache.values()), books


async def ingest_catalog(nodes):
    """Store parsed nodes in the graph."""
    await persist_memory_nodes(nodes)
    return nodes


async def run():
    await prune.prune_data()
    await prune.prune_system(metadata=True)
    await setup()

    user = await get_seed_user()

    data_path = os.path.join(os.path.dirname(__file__), "people.json")
    with open(data_path) as f:
        raw = json.load(f)

    datasets = await load_or_create_datasets([raw], user, "library_catalog")

    authors, genres, books = parse_catalog(raw if isinstance(raw, list) else [raw])
    all_nodes = authors + genres + books

    pipeline = run_tasks(
        tasks=[Task(ingest_catalog, nodes=all_nodes)],
        dataset_id=datasets[0].id,
        user=user,
    )
    async for result in pipeline:
        print(f"Pipeline step: {type(result).__name__}")

    out = os.path.join(os.path.dirname(__file__), ".artifacts", "graph.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    await visualize_graph(out)
    print(f"Graph saved to {out}")


if __name__ == "__main__":
    asyncio.run(run())
