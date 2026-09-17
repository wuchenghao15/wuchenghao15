"""Use Neo4j as the graph backend for M-flow knowledge graphs."""

import os
import pathlib
import asyncio
import m_flow
from m_flow.search.types import RecallMode

DATASET = "neo4j_demo"

SAMPLE = (
    "Neo4j is a native graph database that stores data as nodes and relationships. "
    "It uses the Cypher query language and is widely adopted for fraud detection, "
    "recommendation engines, and knowledge graph applications."
)


async def run():
    root = pathlib.Path(__file__).parent

    neo4j_uri = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")

    m_flow.config.set_graph_db_config(
        {
            "graph_database_url": neo4j_uri,
            "graph_database_provider": "neo4j",
            "graph_database_username": neo4j_user,
            "graph_database_password": neo4j_pass,
        }
    )
    m_flow.config.data_root_directory(str(root / "data_storage"))
    m_flow.config.system_root_directory(str(root / "mflow/system"))

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add([SAMPLE], DATASET)
    await m_flow.memorize([DATASET])

    results = await m_flow.search(query_type=RecallMode.TRIPLET_COMPLETION, query_text="Neo4j capabilities")
    print("Results:")
    for r in results:
        print(f"  · {r}")


if __name__ == "__main__":
    asyncio.run(run())
