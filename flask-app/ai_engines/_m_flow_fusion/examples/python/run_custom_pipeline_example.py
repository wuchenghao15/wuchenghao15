"""M-Flow — custom pipeline assembly demo.

Illustrates how to replicate M-Flow's built-in add/memorize workflows
using the lower-level Task-based custom pipeline API.
"""

import asyncio
from pprint import pprint

import m_flow
from m_flow.api.v1.search import RecallMode
from m_flow.auth.methods import get_seed_user
from m_flow.core.domain.operations.setup import setup
from m_flow.pipeline import Stage
from m_flow.shared.logging_utils import setup_logging, INFO

SAMPLE_TEXT = """
Artificial intelligence encompasses machine learning techniques that
allow computers to learn from data and make predictions.
"""


async def run_custom_pipeline_demo():
    """Build add + memorize pipelines from individual tasks, then query the result."""

    print("Clearing M-Flow state …")
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    print("State cleared.\n")

    await setup()

    print("Input text:")
    print(SAMPLE_TEXT.strip())

    # ── Assemble the 'add' pipeline manually ────────────────────────
    from m_flow.ingestion.pipeline_tasks import ingest_data, resolve_data_directories

    current_user = await get_seed_user()

    ingestion_steps = [
        Stage(resolve_data_directories, include_subdirectories=True),
        Stage(ingest_data, "main_dataset", current_user),
    ]

    await m_flow.run_custom_pipeline(
        tasks=ingestion_steps,
        data=SAMPLE_TEXT,
        user=current_user,
        dataset="main_dataset",
        workflow_name="add_pipeline",
    )
    print("Ingestion pipeline finished.\n")

    # ── Assemble the 'memorize' pipeline manually ───────────────────
    from m_flow.api.v1.memorize.memorize import get_default_tasks

    graph_tasks = await get_default_tasks(user=current_user)
    print("Running memorize pipeline to construct the knowledge graph …\n")
    await m_flow.run_custom_pipeline(
        tasks=graph_tasks,
        user=current_user,
        dataset="main_dataset",
        workflow_name="memorize_pipeline",
    )
    print("Memorize pipeline finished.\n")

    # ── Query the resulting graph ───────────────────────────────────
    query = "What is artificial intelligence?"
    print(f"Querying M-Flow: '{query}'")
    hits = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=query,
    )

    print("Results:")
    for hit in hits:
        pprint(hit)


if __name__ == "__main__":
    setup_logging(log_level=INFO)
    asyncio.run(run_custom_pipeline_demo())
