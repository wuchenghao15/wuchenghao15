# m_flow/memory/procedural/procedure_builder/pipeline_contexts.py
"""
Pipeline Context Data Classes for Procedural Incremental Update

Mirrors episodic/episode_builder/pipeline_contexts.py pattern.
Defines data classes for pipeline stages, configuration, and results.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ============================================================
# Enums
# ============================================================


class MergeAction(str, Enum):
    """Merge action types for incremental update.

    Determines how a new candidate relates to existing procedures:
    - create_new: Different topic → create new procedure
    - patch: Same topic, new additions → merge without new version
    - new_version: Conflicts/changes → create new version, deprecate old
    - skip: Completely duplicate → skip writing
    """

    create_new = "create_new"
    patch = "patch"
    new_version = "new_version"
    skip = "skip"


# ============================================================
# Data Models
# ============================================================


@dataclass
class ExistingProcedureInfo:
    """
    Existing procedure information extracted from recall results.
    Contains all needed fields for decision and compilation.
    """

    procedure_id: str
    title: str
    signature: str
    search_text: str
    version: int = 1
    points_text: str = ""
    context_text: str = ""
    summary: str = ""
    relevance_score: float = 1.0  # lower is better


@dataclass
class IncrementalDecision:
    """
    LLM decision result for a candidate.
    Replaces P4Decision with descriptive name.
    """

    action: MergeAction
    confidence: float = 1.0
    match_procedure_id: Optional[str] = None
    reason: str = ""


# ============================================================
# Module exports
# ============================================================

__all__ = [
    "MergeAction",
    "ExistingProcedureInfo",
    "IncrementalDecision",
]
