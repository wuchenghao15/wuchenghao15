"""M-Flow starter — custom ontology model with typed graph nodes.

Demonstrates how to define domain-specific MemoryNode subclasses that
control the graph schema M-Flow builds during memorization.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List

from m_flow import RecallMode, ContentType, add, config, memorize, prune, search, visualize_graph
from m_flow.low_level import MemoryNode

# -- Paths -----------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
_DATA = _ROOT / ".data_storage"
_SYS = _ROOT / ".mflow/system"
_VIZ = _ROOT / ".artifacts" / "graph_visualization.html"

# -- Domain ontology -------------------------------------------------------


class ResearchArea(MemoryNode):
    """A high-level research discipline."""

    name: str = "Research Area"


class Topic(MemoryNode):
    """A concrete topic belonging to a research area."""

    name: str
    belongs_to: ResearchArea
    metadata: dict = {"index_fields": ["name"]}


class Framework(MemoryNode):
    """An open-source framework used within topics."""

    name: str
    applicable_topics: List[Topic] = []
    belongs_to: ResearchArea
    metadata: dict = {"index_fields": ["name"]}


DEMO_TEXT = (
    "Transformer architectures underpin modern NLP. BERT introduced bidirectional "
    "pre-training while GPT popularised autoregressive generation. Both are widely "
    "used in information extraction and question answering."
)


async def run() -> None:
    config.data_root_directory(str(_DATA))
    config.system_root_directory(str(_SYS))

    await prune.prune_data()
    await prune.prune_system(metadata=True)

    await add(DEMO_TEXT)
    await memorize(content_type=ContentType.TEXT)
    await visualize_graph(str(_VIZ))

    queries = [
        ("What are transformers?", RecallMode.TRIPLET_COMPLETION),
        ("How is BERT used?", RecallMode.RAG_COMPLETION),
        ("NLP", RecallMode.SUMMARIES),
        ("generation", RecallMode.CHUNKS),
    ]
    for q, mode in queries:
        hits = await search(query_text=q, query_type=mode)
        print(f"\n[{mode.value}] {q}")
        for h in hits if isinstance(hits, list) else [hits]:
            print(f"  {h}")


if __name__ == "__main__":
    asyncio.run(run())
