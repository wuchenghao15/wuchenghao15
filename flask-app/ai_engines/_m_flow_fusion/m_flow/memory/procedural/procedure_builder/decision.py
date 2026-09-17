# m_flow/memory/procedural/procedure_builder/decision.py
"""
Decision: LLM-based merge action decision.

Mirrors episodic/episode_builder/phase0c.py pattern.
Decides how to handle a new candidate relative to existing procedures.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.llm_concurrency import get_global_llm_semaphore
from m_flow.llm.LLMGateway import LLMService
from m_flow.shared.data_models import ProceduralCandidate

from .pipeline_contexts import (
    MergeAction,
    ExistingProcedureInfo,
    IncrementalDecision,
)

logger = get_logger("procedural.incremental.decision")


# ============================================================
# Prompts
# ============================================================


DECISION_SYSTEM_PROMPT = """You are deciding how to handle a new procedural knowledge candidate.

【Existing Procedures】
The database already has some similar procedures. You need to decide:

- create_new: The new content is about a DIFFERENT topic. Create a new procedure.
- patch: The new content ADDS TO the existing procedure (same topic, new details). Merge without creating new version.
- new_version: The new content CONFLICTS with or CHANGES the existing procedure. Create a new version.
- skip: The new content is COMPLETELY DUPLICATE with existing. Skip writing.

【Decision Rules】
1. If topics are different → create_new
2. If same topic + only new additions → patch
3. If same topic + conflicting/changed content → new_version
4. If completely same content → skip

Return JSON only:
{
  "action": "create_new" | "patch" | "new_version" | "skip",
  "match_procedure_id": "ID of best matching procedure (null if create_new)",
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}"""


DECISION_USER_PROMPT = """NEW CANDIDATE:
- search_text: {candidate_search_text}
- content preview: {content_preview}

EXISTING PROCEDURES:
{existing_procedures_text}

Decide the action."""


# ============================================================
# LLM Response Model
# ============================================================


class DecisionResponse(BaseModel):
    """LLM response model for incremental update decision."""

    action: str = Field(..., description="create_new | patch | new_version | skip")
    match_procedure_id: Optional[str] = Field(None, description="ID of matching procedure")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    reason: str = Field("", description="Brief explanation")


# ============================================================
# Core Function
# ============================================================


async def make_decision(
    candidate: ProceduralCandidate,
    content_preview: str,
    existing_procedures: List[ExistingProcedureInfo],
) -> IncrementalDecision:
    """
    Decide merge action using LLM.
    Short-circuit: if no existing procedures, return create_new immediately.

    Args:
        candidate: New procedural candidate
        content_preview: Preview of source content for LLM context
        existing_procedures: List of similar existing procedures from recall

    Returns:
        IncrementalDecision with action, confidence, match ID, and reason
    """
    # Short-circuit: no similar procedures found
    if not existing_procedures:
        logger.debug("[procedural.incremental.decision] No similar procedures found, create_new")
        return IncrementalDecision(
            action=MergeAction.create_new,
            confidence=1.0,
            match_procedure_id=None,
            reason="No similar procedures found",
        )

    # Build existing procedures text for prompt
    existing_text_parts = []
    for i, proc in enumerate(existing_procedures[:3]):  # Max 3
        existing_text_parts.append(
            f"""
[{i + 1}] ID: {proc.procedure_id}
    Title: {proc.title}
    Search_text: {proc.search_text}
    Points: {proc.points_text[:200]}...
    Version: v{proc.version}
    Score: {proc.relevance_score:.3f}
"""
        )
    existing_text = "\n".join(existing_text_parts)

    # Build user prompt
    user_prompt = DECISION_USER_PROMPT.format(
        candidate_search_text=candidate.search_text,
        content_preview=content_preview[:500],
        existing_procedures_text=existing_text,
    )

    try:
        # Call LLM for decision (protected by global semaphore)
        async with get_global_llm_semaphore():
            response = await LLMService.extract_structured(
                text_input=user_prompt,
                system_prompt=DECISION_SYSTEM_PROMPT,
                response_model=DecisionResponse,
            )

        action = (
            MergeAction(response.action)
            if response.action in [e.value for e in MergeAction]
            else MergeAction.create_new
        )

        return IncrementalDecision(
            action=action,
            confidence=response.confidence,
            match_procedure_id=response.match_procedure_id,
            reason=response.reason,
        )

    except Exception as e:
        logger.warning(f"[procedural.incremental.decision] Decision LLM failed: {e}, defaulting to create_new")
        return IncrementalDecision(
            action=MergeAction.create_new,
            confidence=0.5,
            match_procedure_id=None,
            reason=f"LLM decision failed: {e}",
        )
