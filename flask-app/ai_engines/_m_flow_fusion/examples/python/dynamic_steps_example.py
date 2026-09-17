"""Selectively enable/disable pipeline steps (classify, chunk, extract, summarize, search)."""

import asyncio
import m_flow
from m_flow.shared.logging_utils import setup_logging, ERROR
from m_flow.api.v1.search import RecallMode

SAMPLE_DOCS = [
    "Quantum computing leverages quantum-mechanical phenomena like superposition and entanglement "
    "to perform computations that would be impractical for classical computers.",
    "The Shor algorithm can factor large integers exponentially faster than the best known "
    "classical algorithms, posing a threat to RSA encryption.",
    "Quantum error correction is essential for building fault-tolerant quantum computers, "
    "as qubits are highly susceptible to decoherence and noise.",
]


async def classify_docs():
    """Step 1: classify ingested documents."""
    print("[classify] Classifying documents...")
    await m_flow.memorize()
    print("[classify] Done.")


async def chunk_and_extract():
    """Step 2+3: chunk text and extract knowledge graph."""
    print("[extract] Chunking and extracting graph...")
    await m_flow.memorize()
    print("[extract] Done.")


async def rebuild_kg():
    """Step 4: rebuild the full knowledge graph."""
    print("[rebuild] Rebuilding knowledge graph...")
    await m_flow.memorize()
    print("[rebuild] Done.")


async def retrieve(query: str = "quantum error correction"):
    """Step 5: search the graph."""
    print(f"[search] Querying: {query}")
    results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=query,
    )
    for r in results:
        print(f"  · {r}")
    return results


STEP_REGISTRY = {
    "classify": classify_docs,
    "extract": chunk_and_extract,
    "memorize": rebuild_kg,
    "search": retrieve,
}


async def main(enabled_steps: dict):
    """Run only the steps the caller has enabled."""
    if enabled_steps.get("classify") or enabled_steps.get("extract"):
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)

        for doc in SAMPLE_DOCS:
            await m_flow.add(doc)
        print(f"Ingested {len(SAMPLE_DOCS)} documents.\n")

    for step_name, step_fn in STEP_REGISTRY.items():
        if enabled_steps.get(step_name):
            await step_fn()
            print()


if __name__ == "__main__":
    setup_logging(log_level=ERROR)

    # Enable all steps by default
    steps_to_run = {name: True for name in STEP_REGISTRY}
    asyncio.run(main(steps_to_run))
