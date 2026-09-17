"""Configure M-flow to use ChromaDB as the vector store, then ingest and query data."""

import pathlib
import asyncio
import m_flow
from m_flow.search.types import RecallMode

DATASET = "chroma_demo"

SAMPLE = (
    "ChromaDB is an open-source vector database optimized for embedding storage and retrieval. "
    "It supports in-memory, SQLite-backed, and client-server deployment modes. "
    "Developers use it for semantic search, recommendation engines, and RAG pipelines."
)


async def run():
    root = pathlib.Path(__file__).parent

    # Point M-flow at ChromaDB
    m_flow.config.set_vector_db_config(
        {
            "vector_db_url": "http://localhost:8000",
            "vector_db_key": "",
            "vector_db_provider": "chromadb",
        }
    )
    m_flow.config.data_root_directory(str(root / "data_storage"))
    m_flow.config.system_root_directory(str(root / "mflow/system"))

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add([SAMPLE], DATASET)
    await m_flow.memorize([DATASET])

    for label, mode, q in [
        ("Graph completion", RecallMode.TRIPLET_COMPLETION, "What is ChromaDB?"),
        ("Chunk search", RecallMode.CHUNKS_LEXICAL, "vector database"),
    ]:
        results = await m_flow.search(query_type=mode, query_text=q, datasets=[DATASET])
        print(f"\n{label} -- '{q}':")
        for r in results:
            print(f"  · {r}")


if __name__ == "__main__":
    asyncio.run(run())
