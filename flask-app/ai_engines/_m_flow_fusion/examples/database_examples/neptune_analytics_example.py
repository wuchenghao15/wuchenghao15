"""Use AWS Neptune Analytics as both graph and vector backend for M-flow."""

import os
import pathlib
import asyncio
import m_flow
from m_flow.search.types import RecallMode

DATASET = "neptune_demo"

SAMPLE = (
    "Amazon Neptune Analytics provides serverless graph analytics with built-in vector search. "
    "It supports openCypher queries and can process billions of relationships for real-time insights."
)


async def run():
    root = pathlib.Path(__file__).parent
    endpoint = os.getenv("NEPTUNE_ENDPOINT", "neptune-graph://<GRAPH_ID>")

    m_flow.config.set_graph_db_config(
        {
            "graph_database_provider": "neptune_analytics",
            "graph_database_url": endpoint,
        }
    )
    m_flow.config.set_vector_db_config(
        {
            "vector_db_provider": "neptune_analytics",
            "vector_db_url": endpoint,
        }
    )
    m_flow.config.data_root_directory(str(root / "data_storage"))
    m_flow.config.system_root_directory(str(root / "mflow/system"))

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add([SAMPLE], DATASET)
    await m_flow.memorize([DATASET])

    results = await m_flow.search(query_type=RecallMode.TRIPLET_COMPLETION, query_text="Neptune Analytics features")
    print("Results:")
    for r in results:
        print(f"  · {r}")


if __name__ == "__main__":
    asyncio.run(run())
