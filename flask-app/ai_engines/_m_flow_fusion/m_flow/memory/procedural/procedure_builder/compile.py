# m_flow/memory/procedural/procedure_builder/compile.py
"""
Compile: Branch compilation with action-specific prompts.

Mirrors episodic/episode_builder/step1_facet_prep.py pattern.
Different merge actions use different LLM prompts for optimal output.
"""

from __future__ import annotations

import json
from typing import Optional

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.llm_concurrency import get_global_llm_semaphore
from m_flow.llm.LLMGateway import LLMService
from m_flow.shared.data_models import ProceduralCandidate
from m_flow.memory.procedural.models import ProceduralWriteDraft

from .pipeline_contexts import MergeAction, ExistingProcedureInfo

logger = get_logger("procedural.incremental.compile")


# ============================================================
# Prompts
# ============================================================


COMPILER_SYSTEM_PROMPT = """You are writing a PROCEDURAL memory from evidence. Return JSON only.

Hard rules:
- Do NOT invent facts. If content does not provide information for a field, output null (not "未说明" or placeholder text).
- Do NOT output secrets. If a secret-like string appears, replace it with "<REDACTED>".
- Context fields (when_text, why_text, boundary_text, etc.): ONLY fill if clearly stated in content. Otherwise output null.
- key_points.points_text: Include ALL related points from source content as a cohesive list.

Output language must match input language."""


COMPILER_USER_PROMPT = """Compile a complete procedure from the following candidate and source content.

CANDIDATE:
{candidate_json}

SOURCE CONTENT:
{content}

Output a structured procedure with ALL required fields:
- title: short human-readable title
- signature: stable short handle for versioning
- search_text: mid-granularity retrieval handle (15-50 chars)
- context: when_text, why_text, boundary_text, outcome_text, prereq_text, exception_text (fill what's available)
- key_points: points_text (for processes: numbered steps; for preferences/persona/habits: bullet points)

NOTE: Do NOT generate 'summary' field - it will be constructed automatically."""


PATCH_SYSTEM_PROMPT = """You are PATCHING an existing procedural memory with NEW information. Return JSON only.

【Task】
An existing procedure already has some content. You need to extract ONLY NEW information 
from the source that is NOT already covered by the existing content.

【Rules】
- Do NOT repeat existing points - only output genuinely NEW points
- Do NOT modify or contradict existing content
- If a point already exists (even with different wording), do NOT include it
- If nothing new to add, output empty strings for points_text and context fields
- Preserve the existing structure (title, signature, search_text should match existing)

【Output】
- key_points.points_text: ONLY NEW points not already in existing (empty string if none)
- context fields: ONLY NEW context not already in existing (null if nothing new)

Output language must match input language."""


PATCH_USER_PROMPT = """EXISTING PROCEDURE (already in database):
- title: {existing_title}
- signature: {existing_signature}
- search_text: {existing_search_text}
- key_points: 
{existing_points_text}
- context: {existing_context_text}

NEW SOURCE CONTENT:
{content}

Extract ONLY NEW information that is NOT already covered above.

Output JSON:
{{
  "title": "{existing_title}",
  "signature": "{existing_signature}",
  "search_text": "{existing_search_text}",
  "key_points": {{
    "points_text": "ONLY NEW points not in existing (empty string if none)"
  }},
  "context": {{
    "when_text": null,
    "why_text": null,
    "boundary_text": null,
    "outcome_text": null,
    "prereq_text": null,
    "exception_text": null
  }}
}}"""


NEWVERSION_SYSTEM_PROMPT = """You are creating a NEW VERSION of an existing procedural memory. Return JSON only.

【Task】
The new content CHANGES or CONFLICTS with existing content.
Create a COMPLETE MERGED version that:
- Incorporates new/changed information (NEW takes priority)
- Preserves old points that are still valid
- Resolves conflicts by preferring the new information

【Rules】
- Output the COMPLETE merged procedure (not just changes)
- When old and new conflict, use the NEW information
- Keep old points that are still valid and not contradicted
- Update title/signature if the change is significant

【Output】
- Full merged procedure with ALL points (old valid + new)
- This will become the new active version

Output language must match input language."""


NEWVERSION_USER_PROMPT = """EXISTING PROCEDURE (version {version}, will be superseded):
- title: {existing_title}
- signature: {existing_signature}
- search_text: {existing_search_text}
- key_points: 
{existing_points_text}
- context: {existing_context_text}

NEW SOURCE CONTENT (takes priority over existing):
{content}

Create a COMPLETE MERGED procedure. New content takes priority when conflicting.

Output JSON:
{{
  "title": "merged title",
  "signature": "merged signature",
  "search_text": "merged search_text",
  "key_points": {{
    "points_text": "COMPLETE merged list (old valid + new)"
  }},
  "context": {{
    "when_text": "merged or new or old or null",
    "why_text": "merged or new or old or null",
    "boundary_text": "merged or new or old or null",
    "outcome_text": "merged or new or old or null",
    "prereq_text": "merged or new or old or null",
    "exception_text": "merged or new or old or null"
  }}
}}"""


# ============================================================
# Core Function
# ============================================================


async def compile_by_action(
    action: MergeAction,
    candidate: ProceduralCandidate,
    content: str,
    existing_procedure: Optional[ExistingProcedureInfo] = None,
) -> Optional[ProceduralWriteDraft]:
    """
    Branch compilation: different prompts for different actions.

    - create_new: Use standard COMPILER prompts
    - patch: Use PATCH prompts (only extract new content)
    - new_version: Use NEWVERSION prompts (complete merged output)
    - skip: Return None

    Args:
        action: Merge action from decision stage
        candidate: ProceduralCandidate from Router
        content: Source content for compilation
        existing_procedure: Existing procedure info (needed for patch/new_version)

    Returns:
        ProceduralWriteDraft or None
    """
    logger.info(
        f"[procedural.incremental.compile] Compiling action={action.value}, "
        f"candidate='{candidate.search_text[:40]}', "
        f"existing={'yes' if existing_procedure else 'no'}"
    )

    if action == MergeAction.skip:
        return None

    if action == MergeAction.create_new:
        return await _compile_create_new(candidate, content)

    if action == MergeAction.patch:
        if not existing_procedure:
            logger.warning(
                "[procedural.incremental.compile] patch action but no existing_procedure, fallback to create_new"
            )
            return await _compile_create_new(candidate, content)
        return await _compile_patch(candidate, content, existing_procedure)

    if action == MergeAction.new_version:
        if not existing_procedure:
            logger.warning(
                "[procedural.incremental.compile] new_version action but no existing_procedure, fallback to create_new"
            )
            return await _compile_create_new(candidate, content)
        return await _compile_new_version(candidate, content, existing_procedure)

    return None


# ============================================================
# Internal Compilation Functions
# ============================================================


async def _compile_create_new(
    candidate: ProceduralCandidate,
    content: str,
) -> Optional[ProceduralWriteDraft]:
    """create_new: Use standard COMPILER prompts."""
    candidate_json = json.dumps(
        {
            "search_text": candidate.search_text,
            "reason": candidate.reason,
            "procedural_type": candidate.procedural_type,
        },
        ensure_ascii=False,
    )

    user_prompt = COMPILER_USER_PROMPT.format(
        candidate_json=candidate_json,
        content=content,
    )

    try:
        async with get_global_llm_semaphore():
            return await LLMService.extract_structured(
                text_input=user_prompt,
                system_prompt=COMPILER_SYSTEM_PROMPT,
                response_model=ProceduralWriteDraft,
            )
    except Exception as e:
        logger.error(f"[procedural.incremental.compile] create_new compile failed: {e}")
        return None


async def _compile_patch(
    candidate: ProceduralCandidate,
    content: str,
    existing: ExistingProcedureInfo,
) -> Optional[ProceduralWriteDraft]:
    """patch: Use PATCH prompts, only extract new content."""
    user_prompt = PATCH_USER_PROMPT.format(
        existing_title=existing.title,
        existing_signature=existing.signature,
        existing_search_text=existing.search_text,
        existing_points_text=existing.points_text or "(empty)",
        existing_context_text=existing.context_text or "(empty)",
        content=content,
    )

    try:
        async with get_global_llm_semaphore():
            return await LLMService.extract_structured(
                text_input=user_prompt,
                system_prompt=PATCH_SYSTEM_PROMPT,
                response_model=ProceduralWriteDraft,
            )
    except Exception as e:
        logger.error(f"[procedural.incremental.compile] patch compile failed: {e}")
        return None


async def _compile_new_version(
    candidate: ProceduralCandidate,
    content: str,
    existing: ExistingProcedureInfo,
) -> Optional[ProceduralWriteDraft]:
    """new_version: Use NEWVERSION prompts, output complete merged content."""
    user_prompt = NEWVERSION_USER_PROMPT.format(
        version=existing.version,
        existing_title=existing.title,
        existing_signature=existing.signature,
        existing_search_text=existing.search_text,
        existing_points_text=existing.points_text or "(empty)",
        existing_context_text=existing.context_text or "(empty)",
        content=content,
    )

    try:
        async with get_global_llm_semaphore():
            return await LLMService.extract_structured(
                text_input=user_prompt,
                system_prompt=NEWVERSION_SYSTEM_PROMPT,
                response_model=ProceduralWriteDraft,
            )
    except Exception as e:
        logger.error(f"[procedural.incremental.compile] new_version compile failed: {e}")
        return None
