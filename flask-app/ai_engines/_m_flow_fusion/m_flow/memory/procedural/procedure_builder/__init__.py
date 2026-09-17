# m_flow/memory/procedural/procedure_builder/__init__.py
"""
Procedure Builder Module - Pipeline Infrastructure for Procedural Memory Processing

Mirrors episodic/episode_builder/ pattern.
Breaks down the incremental update flow into distinct, testable stages:

Directory Structure:
    procedure_builder/
    ├── __init__.py              # This file - module exports + process_candidate entry
    ├── pipeline_contexts.py     # Data classes: MergeAction, ExistingProcedureInfo, etc.
    ├── recall.py               # Stage 1: Vector recall of similar procedures
    ├── decision.py             # Stage 2: LLM merge decision
    ├── compile.py              # Stage 3: Branch compilation (action-specific prompts)
    ├── write.py                # Stage 4: Branch write + version management
    └── merge_utils.py          # Pure utility functions for content merging
"""

from __future__ import annotations

from typing import List, Optional

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.tracing import TraceManager
from m_flow.shared.data_models import ProceduralCandidate
from m_flow.core.domain.models import Procedure
from m_flow.core.domain.models.memory_space import MemorySpace

from .pipeline_contexts import (
    MergeAction,
    ExistingProcedureInfo,
    IncrementalDecision,
)
from .recall import recall_similar_procedures, RECALL_SIMILARITY_THRESHOLD
from .decision import make_decision
from .compile import compile_by_action
from .write import (
    write_by_action,
    build_procedure_node,
    deprecate_procedure,
    create_supersedes_edge,
)
from .merge_utils import merge_points_text_with_dedup, dedup_candidates

logger = get_logger("procedural.incremental")


# ============================================================
# Main Entry Points
# ============================================================


async def process_candidate(
    candidate: ProceduralCandidate,
    content: str,
    nodeset: MemorySpace,
    source_refs: Optional[List[str]] = None,
    enable_incremental: bool = True,
) -> Optional[Procedure]:
    """
    Process a single candidate with incremental update.

    Full pipeline: Recall → Decide → Compile → Write

    Args:
        candidate: ProceduralCandidate from Router
        content: Source content for compilation
        nodeset: MemorySpace for graph organization
        source_refs: Source tracing
        enable_incremental: If False, skip incremental update and just create_new

    Returns:
        Procedure node (or None if skipped/failed)
    """
    TraceManager.event(
        "procedural.incremental.start",
        {
            "search_text": candidate.search_text[:50],
            "enable_incremental": enable_incremental,
        },
    )

    # Fast path: incremental disabled
    if not enable_incremental:
        from .compile import _compile_create_new
        from .write import _write_create_new

        draft = await _compile_create_new(candidate, content)
        if draft:
            return await _write_create_new(draft, nodeset, source_refs)
        return None

    # Stage 1: Recall
    existing_procedures = await recall_similar_procedures(
        candidate.search_text,
        top_k=3,
        score_threshold=RECALL_SIMILARITY_THRESHOLD,
    )

    # Stage 2: Decide
    decision = await make_decision(
        candidate,
        content[:500],
        existing_procedures,
    )

    logger.info(
        f"[procedural.incremental] Decision: action={decision.action.value}, "
        f"match_id={decision.match_procedure_id[:12] if decision.match_procedure_id else 'None'}..., "
        f"reason={decision.reason[:50]}"
    )

    TraceManager.event(
        "procedural.incremental.decision",
        {
            "action": decision.action.value,
            "has_match": decision.match_procedure_id is not None,
        },
    )

    if decision.action == MergeAction.skip:
        logger.info(f"[procedural.incremental] Skipping candidate: {candidate.search_text[:30]}")
        return None

    # Find matching existing procedure
    existing_procedure = None
    if decision.match_procedure_id and existing_procedures:
        existing_procedure = next(
            (p for p in existing_procedures if p.procedure_id == decision.match_procedure_id),
            existing_procedures[0] if existing_procedures else None,
        )

    # Stage 3: Compile
    draft = await compile_by_action(
        action=decision.action,
        candidate=candidate,
        content=content,
        existing_procedure=existing_procedure,
    )

    if not draft:
        logger.warning(f"[procedural.incremental] Compilation failed for: {candidate.search_text[:30]}")
        return None

    # Stage 4: Write
    procedure = await write_by_action(
        action=decision.action,
        draft=draft,
        nodeset=nodeset,
        existing_procedure=existing_procedure,
        source_refs=source_refs,
    )

    TraceManager.event(
        "procedural.incremental.done",
        {
            "action": decision.action.value,
            "procedure_id": str(procedure.id)[:12] if procedure else None,
        },
    )

    return procedure


async def process_candidates(
    candidates: List[ProceduralCandidate],
    content: str,
    nodeset: MemorySpace,
    source_refs: Optional[List[str]] = None,
    enable_incremental: bool = True,
) -> List[Procedure]:
    """
    Batch entry: Process multiple candidates with incremental update.

    Includes batch-level deduplication before processing.
    """
    if not candidates:
        return []

    deduped = dedup_candidates(candidates)
    logger.info(f"[procedural.incremental] Processing {len(deduped)} candidates (deduped from {len(candidates)})")

    results = []
    for candidate in deduped:
        proc = await process_candidate(
            candidate=candidate,
            content=content,
            nodeset=nodeset,
            source_refs=source_refs,
            enable_incremental=enable_incremental,
        )
        if proc:
            results.append(proc)

    return results


# ============================================================
# Module exports
# ============================================================

__all__ = [
    # Main entry points
    "process_candidate",
    "process_candidates",
    # Pipeline stages (for direct use if needed)
    "recall_similar_procedures",
    "make_decision",
    "compile_by_action",
    "write_by_action",
    "build_procedure_node",
    # Version management
    "deprecate_procedure",
    "create_supersedes_edge",
    # Merge utilities
    "merge_points_text_with_dedup",
    "dedup_candidates",
    # Data classes
    "MergeAction",
    "ExistingProcedureInfo",
    "IncrementalDecision",
    # Constants
    "RECALL_SIMILARITY_THRESHOLD",
]
