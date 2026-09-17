"""Use KuzuDB as the graph backend for M-flow knowledge graphs."""

import pathlib
import asyncio
import m_flow
from m_flow.search.types import RecallMode

DATASET = "kuzu_demo"

SAMPLE = (
    "KuzuDB is an embedded graph database management system built for fast analytical queries. "
    "It uses columnar storage and vectorized execution for high throughput on graph workloads."
)


async def run():
    root = pathlib.Path(__file__).parent

    m_flow.config.set_graph_db_config({"graph_database_provider": "kuzu"})
    m_flow.config.data_root_directory(str(root / "data_storage"))
    m_flow.config.system_root_directory(str(root / "mflow/system"))

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add([SAMPLE], DATASET)
    await m_flow.memorize([DATASET])

    results = await m_flow.search(query_type=RecallMode.TRIPLET_COMPLETION, query_text="graph database")
    print("Results:")
    for r in results:
        print(f"  · {r}")


if __name__ == "__main__":
    asyncio.run(run())
