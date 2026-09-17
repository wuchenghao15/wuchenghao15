"""Use PGVector (PostgreSQL) as the vector backend for M-flow."""

import os
import pathlib
import asyncio
import m_flow
from m_flow.search.types import RecallMode

DATASET = "pgvector_demo"

SAMPLE = (
    "PGVector extends PostgreSQL with vector similarity search capabilities. "
    "It stores embeddings alongside relational data, enabling hybrid queries "
    "that combine structured filters with semantic similarity."
)


async def run():
    root = pathlib.Path(__file__).parent

    m_flow.config.set_vector_db_config({"vector_db_provider": "pgvector"})
    m_flow.config.set_relational_db_config(
        {
            "db_host": os.getenv("POSTGRES_HOST", "localhost"),
            "db_port": os.getenv("POSTGRES_PORT", "5432"),
            "db_name": os.getenv("POSTGRES_DB", "mflow_store"),
            "db_username": os.getenv("POSTGRES_USER", "m_flow"),
            "db_password": os.getenv("POSTGRES_PASSWORD", "m_flow"),
            "db_provider": "postgres",
        }
    )
    m_flow.config.data_root_directory(str(root / "data_storage"))
    m_flow.config.system_root_directory(str(root / "mflow/system"))

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add([SAMPLE], DATASET)
    await m_flow.memorize([DATASET])

    results = await m_flow.search(query_type=RecallMode.TRIPLET_COMPLETION, query_text="vector search in PostgreSQL")
    print("Results:")
    for r in results:
        print(f"  · {r}")


if __name__ == "__main__":
    asyncio.run(run())
