"""
M-flow Quick Start Example

Demonstrates the core workflow: ingest text → build knowledge graph → search.
Requires: LLM_API_KEY in .env (see .env.template).
"""

import asyncio

import m_flow
from m_flow.shared.logging_utils import setup_logging, ERROR
from m_flow.api.v1.search import RecallMode

SAMPLE_TEXT = """
Machine learning is a branch of artificial intelligence that enables
systems to learn patterns from data and improve their performance
without being explicitly programmed for each task.
"""


async def run_example():
    # Clear previous data for a fresh run
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Ingest sample content
    print(f"Ingesting sample text ({len(SAMPLE_TEXT.split())} words)...")
    await m_flow.add(SAMPLE_TEXT)

    # Build the knowledge graph from ingested data
    print("Building knowledge graph...")
    await m_flow.memorize()
    print("Knowledge graph ready.\n")

    # Query the graph
    query = "What is machine learning?"
    print(f"Query: {query}")
    results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=query,
    )

    print("Results:")
    for item in results:
        print(f"  • {item}")


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(run_example())
