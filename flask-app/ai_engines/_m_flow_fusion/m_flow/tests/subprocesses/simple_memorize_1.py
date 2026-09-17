"""Subprocess: run the first memorization pipeline and verify triplet recall results."""

import asyncio
import sys

import m_flow
from m_flow.shared.logging_utils import setup_logging, INFO
from m_flow.api.v1.search import RecallMode

PRIMARY_DATASET = "first_memorize_dataset"
PRIMARY_QUERY = (
    "Summarize the information available in the context. Start your answer with the marker 'FIRST_MEMORIZE'."
)


async def execute_primary_memorize():
    """Run the memorize pipeline on the primary dataset and query via triplet completion."""
    await m_flow.memorize(datasets=[PRIMARY_DATASET])

    matched_items = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=PRIMARY_QUERY,
        datasets=[PRIMARY_DATASET],
    )

    sys.stdout.write("--- Primary Recall Results ---\n")
    for pos, item in enumerate(matched_items):
        sys.stdout.write(f"  #{pos + 1}: {item}\n")


if __name__ == "__main__":
    log_ref = setup_logging(log_level=INFO)
    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)
    try:
        main_loop.run_until_complete(execute_primary_memorize())
    finally:
        main_loop.run_until_complete(main_loop.shutdown_asyncgens())
