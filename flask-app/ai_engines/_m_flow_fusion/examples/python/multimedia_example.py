"""M-Flow — multimedia ingestion and knowledge-graph search demo.

Shows how M-Flow can process audio and image files, build a knowledge graph
from their content, and answer natural-language queries about them.
"""

import asyncio
import os
import pathlib
from pprint import pprint

import m_flow
from m_flow.api.v1.search import RecallMode
from m_flow.shared.logging_utils import setup_logging, ERROR


EXAMPLE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


async def run_multimedia_demo():
    """Ingest sample audio/image files, build the graph, then query for summaries."""

    # Wipe any previous state so the demo is reproducible
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Locate sample media assets
    audio_asset = os.path.join(EXAMPLE_ROOT, "examples/data/multimedia/text_to_speech.mp3")
    image_asset = os.path.join(EXAMPLE_ROOT, "examples/data/multimedia/example.png")

    # Feed them into the M-Flow pipeline
    await m_flow.add([audio_asset, image_asset])

    # Construct the knowledge graph from the ingested content
    await m_flow.memorize()

    # Retrieve summaries describing the multimedia data
    hits = await m_flow.search(
        query_type=RecallMode.SUMMARIES,
        query_text="What is in the multimedia files?",
    )

    for item in hits:
        pprint(item)


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(run_multimedia_demo())
