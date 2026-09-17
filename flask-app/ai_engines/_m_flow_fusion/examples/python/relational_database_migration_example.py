"""M-Flow — relational-to-graph database migration demo.

Demonstrates how to extract a relational DB schema, migrate its data into
M-Flow's graph store, and then query the resulting knowledge graph.
"""

import asyncio
import os
from pathlib import Path

import m_flow
from m_flow.adapters.relational.config import get_migration_config
from m_flow.adapters.graph import get_graph_provider
from m_flow.api.v1.visualize.visualize import visualize_graph
from m_flow.adapters.relational import (
    get_migration_relational_engine,
    create_db_and_tables as init_relational_tables,
)
from m_flow.adapters.vector.pgvector import (
    create_db_and_tables as init_vector_tables,
)
from m_flow.search.types import RecallMode

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# If no external DB is configured, default to the bundled SQLite sample:
#   MIGRATION_DB_PATH = "/<your_m_flow_checkout>/m_flow/tests/test_data"
#   MIGRATION_DB_NAME = "migration_database.sqlite"
#   MIGRATION_DB_PROVIDER = "sqlite"


async def run_migration_demo():
    """Full migration workflow: schema extraction → graph import → search → visualise."""

    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"

    # Reset M-Flow storage
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare the relational and vector stores
    await init_relational_tables()
    await init_vector_tables()

    # Resolve migration source settings (env vars override defaults)
    db_provider = os.environ.get("MIGRATION_DB_PROVIDER", "sqlite")
    db_path = os.environ.get(
        "MIGRATION_DB_PATH",
        str(PROJECT_ROOT / "m_flow" / "tests" / "test_data"),
    )
    db_name = os.environ.get("MIGRATION_DB_NAME", "migration_database.sqlite")

    cfg = get_migration_config()
    cfg.migration_db_provider = db_provider
    cfg.migration_db_path = db_path
    cfg.migration_db_name = db_name

    rel_engine = get_migration_relational_engine()

    print("\nExtracting source database schema …")
    db_schema = await rel_engine.extract_schema()
    print(f"Schema:\n{db_schema}")

    graph_engine = await get_graph_provider()
    print("Migrating relational data into the graph store …")
    from m_flow.ingestion.pipeline_tasks import migrate_relational_database

    await migrate_relational_database(graph_engine, schema=db_schema)
    print("Migration complete.")

    # Broad search — high top_k to cover the whole graph
    broad_results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        question="What kind of data do you contain?",
        top_k=200,
    )
    print(f"\nBroad search results: {broad_results}")

    # Targeted searches — lower top_k to avoid context overflow
    for customer_name in ("Leonie Köhler", "Luís Gonçalves"):
        focused = await m_flow.search(
            query_type=RecallMode.TRIPLET_COMPLETION,
            question=f"What invoices are related to {customer_name}?",
            top_k=50,
        )
        print(f"Invoices for {customer_name}: {focused}")

    # Produce an interactive HTML visualisation
    viz_path = os.path.join(os.path.expanduser("~"), "graph_visualization.html")
    print("\nGenerating graph visualisation …")
    await visualize_graph(viz_path)
    print(f"Visualisation saved → {viz_path}")


if __name__ == "__main__":
    asyncio.run(run_migration_demo())
