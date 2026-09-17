"""Demonstrate node-set tagging: assign topics to ingested content."""

import os
import asyncio
import m_flow
from m_flow.api.v1.visualize.visualize import visualize_graph
from m_flow.shared.logging_utils import setup_logging, ERROR

# Three content pieces, each tagged with relevant topic sets
CONTENT = [
    {
        "text": "AI-powered fraud detection is transforming the banking industry.",
        "tags": ["AI", "FinTech"],
    },
    {
        "text": "Reinforcement learning enables agents to improve through trial and error.",
        "tags": ["AI"],
    },
    {
        "text": "Wearable health monitors are driving the digital health revolution.",
        "tags": ["MedTech"],
    },
]


async def run():
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    for item in CONTENT:
        await m_flow.add(item["text"], graph_scope=item["tags"])

    await m_flow.memorize()

    out_path = os.path.join(os.path.dirname(__file__), ".artifacts", "graph_visualization.html")
    await visualize_graph(out_path)
    print(f"Graph saved to {out_path}")


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(run())
