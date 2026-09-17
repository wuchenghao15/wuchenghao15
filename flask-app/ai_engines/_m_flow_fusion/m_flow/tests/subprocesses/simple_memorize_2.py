"""Subprocess: run the second memorization pipeline and validate triplet recall."""

import asyncio
import sys

import m_flow
from m_flow.shared.logging_utils import setup_logging, INFO
from m_flow.api.v1.search import RecallMode

DATASET_TAG = "second_memorize_dataset"
RECALL_PROMPT = (
    "Describe what you find in the context. Prepend the token 'SECOND_MEMORIZE' to the beginning of your response."
)


async def run_memorize_and_recall():
    """Execute memorization on the secondary dataset, then perform a triplet recall query."""
    await m_flow.memorize(datasets=[DATASET_TAG])

    recall_results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=RECALL_PROMPT,
        datasets=[DATASET_TAG],
    )

    sys.stdout.write("=== Recall Output ===\n")
    for idx, entry in enumerate(recall_results):
        sys.stdout.write(f"  [{idx}] {entry}\n")


if __name__ == "__main__":
    log_handle = setup_logging(log_level=INFO)
    ev_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ev_loop)
    try:
        ev_loop.run_until_complete(run_memorize_and_recall())
    finally:
        ev_loop.run_until_complete(ev_loop.shutdown_asyncgens())
