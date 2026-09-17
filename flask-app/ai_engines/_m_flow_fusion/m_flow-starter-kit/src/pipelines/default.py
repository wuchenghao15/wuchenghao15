"""M-Flow starter pipeline — ingest sample text and run all search modes."""

from __future__ import annotations

import asyncio
from pathlib import Path

from m_flow import RecallMode, ContentType, add, config, memorize, prune, search, visualize_graph

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / ".data_storage"
SYSTEM_DIR = HERE / ".mflow/system"
VIZ_FILE = HERE / ".artifacts" / "graph_visualization.html"

SAMPLE = (
    "Large language models leverage self-attention to process long sequences. "
    "Retrieval-augmented generation combines a knowledge store with generative AI "
    "to produce factual, grounded answers."
)


async def run() -> None:
    config.data_root_directory(str(DATA_DIR))
    config.system_root_directory(str(SYSTEM_DIR))

    await prune.prune_data()
    await prune.prune_system(metadata=True)

    await add(SAMPLE)
    await memorize(content_type=ContentType.TEXT)
    await visualize_graph(str(VIZ_FILE))

    for mode, label in [
        (RecallMode.TRIPLET_COMPLETION, "Triplet"),
        (RecallMode.RAG_COMPLETION, "RAG"),
        (RecallMode.SUMMARIES, "Summary"),
        (RecallMode.CHUNKS, "Chunk"),
    ]:
        result = await search(query_text="What are large language models?", query_type=mode)
        print(f"\n--- {label} ---")
        if isinstance(result, list):
            for item in result:
                print(item)
        else:
            print(result)


if __name__ == "__main__":
    asyncio.run(run())
