# m_flow/memory/procedural/__init__.py
"""
Procedural Memory Tasks

Stages:
- Schema & Index infrastructure
- Write: Router + Compiler extraction of Procedure
- Points Builder: Deterministic StepPoint/ContextPoint generation
- Retrieval: Procedural Bundle Search
- Incremental Update: Cross-batch dedup + LLM decision + version management
- System Integration: Pipeline Task integration

Architecture:
- Procedure (anchor) → ContextPoint + KeyPoint (2-layer triplet, no Pack)

Design principles:
- Context must appear together with Procedure (when/why/boundary)
- Selective storage, but gating should not be too strict (prevent misses)
- Write side depends on LLM, prioritize quality and safety
- Point extraction uses Deterministic approach, avoid fabrication, ensure coverage
- Incremental update: batch deduplication + recall + LLM decision + patch/new_version/create_new
"""

# Core write task
from .write_procedural_memories import write_procedural_memories

# Deterministic Point Builder
from .procedural_points_builder import (
    build_step_points,
    build_context_points,
    extract_anchor_tokens,
)

# LLM output models
from .models import (
    ProceduralWriteDraft,
    ContextPackDraft,
    StepsPackDraft,
    # Version management models
    ProcedureCandidate,
    MergeDecision,
)

# Unified ProceduralCandidate from shared (replaces RouterCandidate/RouterOutput)
from m_flow.shared.data_models import ProceduralCandidate, ProceduralCandidateList  # noqa: F811

# Routing and version management
from .procedure_router import (
    route_procedure,
    find_similar_procedures,
    decide_merge_action,
    RouteResult,
    get_procedure_version,
    deprecate_procedure,
    create_supersedes_edge,
    merge_procedure_content,
)

# Incremental update pipeline (new modular architecture)
from .procedure_builder import (  # noqa: F401
    process_candidate,
    process_candidates,
    MergeAction,
    ExistingProcedureInfo,
    IncrementalDecision,
)

# Procedure state query
from .procedure_state import (  # noqa: F401
    ProcedureState,
    fetch_procedure_state,
    get_version_chain,
)

# Episodic -> Procedural bridge
from .write_procedural_from_episodic import (
    write_procedural_from_decisions,
    extract_procedural_from_episodic,
)

__all__ = [
    # Core tasks
    "write_procedural_memories",
    # Deterministic Point Builder
    "build_step_points",
    "build_context_points",
    "extract_anchor_tokens",
    # LLM output models
    "ProceduralWriteDraft",
    "ContextPackDraft",
    "StepsPackDraft",
    # Unified procedural candidate (from shared)
    "ProceduralCandidate",
    "ProceduralCandidateList",
    # Version management models
    "ProcedureCandidate",
    "MergeDecision",
    # Routing and version management
    "route_procedure",
    "find_similar_procedures",
    "decide_merge_action",
    "RouteResult",
    "get_procedure_version",
    "deprecate_procedure",
    "create_supersedes_edge",
    "merge_procedure_content",
    # Incremental update pipeline (new)
    "process_candidate",
    "process_candidates",
    "MergeAction",
    "ExistingProcedureInfo",
    "IncrementalDecision",
    # Procedure state
    "ProcedureState",
    "fetch_procedure_state",
    "get_version_chain",
    # Episodic -> Procedural bridge
    "write_procedural_from_decisions",
    "extract_procedural_from_episodic",
]
