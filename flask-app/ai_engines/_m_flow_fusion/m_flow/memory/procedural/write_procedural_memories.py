# m_flow/memory/procedural/write_procedural_memories.py
"""
Procedural Memory write task.

Convert input text to Procedure + Points (direct triplet, no Pack nodes),
return MemoryNode list, written to graph database and vector index by upper pipeline.

Architecture: Procedure → Point (2-layer triplet)
- Procedure → has_context_point → ContextPoint
- Procedure → has_key_point → KeyPoint (ProcedureStepPoint)

Core flow:
1. Router: identify procedure candidates from input
2. Compiler: LLM extracts full structure (title/context/key_points)
3. Points builder: deterministic generation of ContextPoints + KeyPoints
4. Security: sensitive information redaction
5. Return: MemoryNode list (Procedure + Points)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, List, Optional

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.tracing import TraceManager

# Global LLM concurrency control
from m_flow.shared.llm_concurrency import get_global_llm_semaphore

from m_flow.llm.LLMGateway import LLMService

from m_flow.core.domain.models import (
    Procedure,
)
from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.core.domain.utils.generate_node_id import generate_node_id

from m_flow.knowledge.summarization.models import FragmentDigest
from m_flow.memory.procedural.models import (
    ProceduralWriteDraft,
)
from m_flow.memory.procedural.procedure_builder import process_candidate
from m_flow.shared.data_models import ProceduralCandidate, ProceduralCandidateList
from m_flow.retrieval.time import extract_mentioned_time
from m_flow.memory.procedural.procedural_points_builder import (
    build_step_points,
    build_context_points,
)

from m_flow.memory.episodic.normalization import (
    truncate as _truncate,
    normalize_for_compare,
)

logger = get_logger("procedural.write")


def normalize_for_id(text: str) -> str:
    """For id: more aggressive, reduce 'space/punctuation differences causing new procedure'"""
    t = normalize_for_compare(text)
    t = t.replace(" ", "")
    t = re.sub(r"[，,。.；;：:()[\]【】<>《》" "\"''!！？?]+", "", t)
    return t


# -----------------------------
# Security: Secret Redaction & Dangerous Content Detection
# Unified implementation in procedural_safety.py
# Re-exported here for backward compatibility with tests
# -----------------------------

from m_flow.memory.procedural.procedural_safety import (  # noqa: F401
    redact_secrets,
    contains_dangerous_content,
)


# -----------------------------
# Edge text builders
# -----------------------------


def _make_has_context_edge_text(
    procedure_search_text: str,
    context_anchor_text: str,
) -> str:
    """Build rich edge_text for has_context edge (no truncation)."""
    return f"{procedure_search_text}: context - {context_anchor_text}"


def _make_has_points_edge_text(
    procedure_search_text: str,
    points_text: str,
) -> str:
    """Build rich edge_text for has_points edge (no truncation)."""
    return f"{procedure_search_text}: points - {points_text}"


def _make_has_point_edge_text(
    pack_search_text: str,
    point_search_text: str,
    point_type: Optional[str] = None,
) -> str:
    """Build rich edge_text for has_point edge."""
    if point_type:
        return f"{pack_search_text} -> {point_type}: {point_search_text}"
    return f"{pack_search_text} -> {point_search_text}"


# -----------------------------
# LLM Prompts
# -----------------------------

# ============================================================
# Router Prompt: Identify multiple procedure candidates from one episode
# ============================================================

ROUTER_SYSTEM_PROMPT = """你是 Procedural Memory 候选识别器。从输入内容中提取可复用的流程、偏好、习惯。仅输出 JSON。

【什么是 Procedural Memory】
LLM 自身无法推断、需要额外记住的知识：
- 团队/个人特有的工作方式、规范约定
- 特定环境下的操作步骤、工具链偏好
- 有条件分支或边界约束的决策规则

【提取判断标准】
1. 复用价值：该知识在未来类似场景中是否有用
2. 专有性：LLM 通用知识库是否已包含（通用常识不提取）
3. 操作性：是否包含可执行的步骤、可遵循的规则、或可参考的偏好

【候选粒度】
- 同一主题的所有步骤/规则归为一个候选（不拆分单步）
- search_text 是整体主题名，不是单个步骤名
- 每个候选 15-50 字

【候选类型 procedural_type】
- reusable_process：多步骤技术流程（部署、排查、审查等）
- user_preference：格式偏好、工具选择、参数习惯
- user_habit：个人/团队固定做法（不一定是技术性的）
- persona：角色特征、沟通风格

【输出格式】
candidates 数组，每项含：search_text, confidence (0-1), reason, procedural_type

输出语言必须与输入内容的语言一致。"""

ROUTER_USER_PROMPT = """从以下内容中识别 Procedural Memory 候选：

{content}

输出 JSON: {{"candidates": [...]}}"""

# ============================================================
# Compiler Prompt: Compile complete procedure from candidate + content
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

# Extraction prompt alias
EXTRACTION_SYSTEM_PROMPT = COMPILER_SYSTEM_PROMPT
EXTRACTION_USER_PROMPT = """Extract procedural knowledge from the following content:

Content:
{content}

Output a structured procedure with ALL required fields:
- title, signature, search_text
- context: when_text, why_text, boundary_text, outcome_text, prereq_text, exception_text
- key_points: points_text (for processes: numbered steps; for preferences/persona/habits: bullet points)

NOTE: Do NOT generate 'summary' field - it will be constructed automatically."""


# Point extraction is deterministic (see procedural_points_builder.py)
# No LLM prompts needed - points are generated from structured content directly


# -----------------------------
# Main Task (Router + Compiler Mode)
# -----------------------------


async def write_procedural_memories(
    memory_nodes: List[Any],  # Changed: Accept mixed types for Content Routing Pipeline compatibility
    *,
    procedural_nodeset_name: str = "Procedural",
    enable_routing: bool = True,  # Incremental update routing
    max_candidates_per_episode: int = 10,  # Max candidates to compile per episode
) -> List[Any]:
    """
    Procedural write (Router + Compiler mode):

    1. Router: Identify multiple procedure candidates from each episode
    2. Compiler: Concurrently compile candidates (global semaphore controls concurrency)
    3. Routing: Incremental update routing (merge/version/new)
    4. Return MemoryNode list, written by upper pipeline

    Args:
        memory_nodes: List of MemoryNode objects (filters for FragmentDigest internally)
                    Supports both List[FragmentDigest] and mixed List[Any] inputs
                    for compatibility with Content Routing Pipeline
        procedural_nodeset_name: MemorySpace name for graph organization
        enable_routing: Whether to enable incremental procedure routing
        max_candidates_per_episode: Max candidates to compile per episode

    Returns:
        List of MemoryNode objects (Procedure + Points, no Pack nodes)
    """
    out: List[Any] = []

    if not memory_nodes:
        logger.warning("[procedural] No memory_nodes provided")
        return out

    # Ensure all inputs are passed to subsequent tasks
    # Keep consistent with write_episodic_memories
    out.extend(memory_nodes)

    # Filter FragmentDigest from mixed input
    # This allows write_procedural_memories to receive write_episodic_memories output
    summaries = [dp for dp in memory_nodes if isinstance(dp, FragmentDigest)]

    if not summaries:
        logger.info("[procedural] No FragmentDigest objects found in input, skipping")
        return out

    # Tracing: Start write trace
    TraceManager.start(
        "procedural.write",
        meta={
            "batch_size": len(summaries),
            "enable_routing": enable_routing,
        },
    )

    logger.info(f"[procedural] Processing {len(summaries)} summaries")

    # Create MemorySpace with deterministic ID
    procedural_nodeset = MemorySpace(
        id=generate_node_id(f"MemorySpace:{procedural_nodeset_name}"),
        name=procedural_nodeset_name,
    )

    # Ensure MemorySpace is written to graph
    out.append(procedural_nodeset)

    # Helper to ensure nodeset assignment
    def ensure_nodeset(dp: Any, nodeset: MemorySpace):
        if hasattr(dp, "memory_spaces"):
            if dp.memory_spaces is None:
                dp.memory_spaces = [nodeset]
            elif nodeset not in dp.memory_spaces:
                dp.memory_spaces.append(nodeset)

    # Confidence threshold for filtering candidates
    CONFIDENCE_THRESHOLD = float(os.getenv("MFLOW_PROCEDURAL_CONFIDENCE_THRESHOLD", "0.5"))

    # Process each summary
    for idx, summary in enumerate(summaries):
        content = getattr(summary, "text", "") or getattr(summary, "summary", "")
        if not content:
            logger.warning(f"[procedural] Empty content at index {idx}, skipping")
            continue

        logger.info(f"[procedural] Processing summary {idx + 1}/{len(summaries)}")

        # Extract source tracing information
        summary_source_refs: Optional[List[str]] = None
        meta = getattr(summary, "metadata", None) or {}
        source_episode_id = meta.get("source_episode_id") if isinstance(meta, dict) else None
        if source_episode_id:
            summary_source_refs = [f"episode:{source_episode_id}"]
            logger.debug(f"[procedural] Source episode: {source_episode_id}")

        # Router mode: Identify multiple candidates using unified ProceduralCandidate
        try:
            router_output = await _route_procedures(content)
            candidates = router_output.candidates or []

            # Filter by confidence threshold
            candidates_to_compile = [c for c in candidates if c.confidence >= CONFIDENCE_THRESHOLD]

            # Sort by confidence, limit count
            candidates_to_compile.sort(key=lambda c: c.confidence, reverse=True)
            candidates_to_compile = candidates_to_compile[:max_candidates_per_episode]

            logger.info(
                f"[procedural] Router found {len(candidates)} candidates, "
                f"compiling {len(candidates_to_compile)} (threshold: {CONFIDENCE_THRESHOLD})"
            )
            for ci, c in enumerate(candidates_to_compile):
                logger.info(
                    f"  [procedural.router] Candidate {ci + 1}: "
                    f"search_text='{c.search_text[:50]}', "
                    f"confidence={c.confidence:.2f}, "
                    f"type={c.procedural_type}, "
                    f"reason='{c.reason[:60] if c.reason else ''}'"
                )

            # Tracing: Record Router results
            TraceManager.event(
                "procedural.write.router",
                {
                    "total_candidates": len(candidates),
                    "to_compile": len(candidates_to_compile),
                    "candidate_search_texts": [c.search_text[:50] for c in candidates_to_compile[:5]],
                },
            )

            if not candidates_to_compile:
                continue

            # Concurrent compilation using _compile_and_build_procedure
            tasks = [
                _compile_and_build_procedure(
                    content=content,
                    candidate=c,
                    nodeset=procedural_nodeset,
                    source_refs=summary_source_refs,
                )
                for c in candidates_to_compile
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"[procedural] Compile task failed: {result}")
                elif result is not None:
                    ensure_nodeset(result, procedural_nodeset)
                    out.append(result)

        except Exception as e:
            logger.error(f"[procedural] Router failed: {e}")
            continue

    # Tracing: Record write completion
    TraceManager.event(
        "procedural.write.done",
        {
            "procedures_generated": len(out),
            "summaries_processed": len(summaries),
        },
    )
    TraceManager.end("ok")

    logger.info(f"[procedural] Generated {len(out)} procedures from {len(summaries)} summaries")

    return out


async def _route_procedures(content: str) -> ProceduralCandidateList:
    """
    Router: Identify multiple procedure candidates from one episode.

    Returns ProceduralCandidateList with 0-N candidates.
    Each candidate contains: search_text, confidence, reason, procedural_type.
    """
    user_prompt = ROUTER_USER_PROMPT.format(content=_truncate(content, 3000))

    async with get_global_llm_semaphore():
        result = await LLMService.extract_structured(
            text_input=user_prompt,
            system_prompt=ROUTER_SYSTEM_PROMPT,
            response_model=ProceduralCandidateList,
        )
    return result


async def _compile_procedure(content: str, candidate_json: str) -> ProceduralWriteDraft:
    """
    Compiler: Compile complete procedure from candidate + content.

    Use candidate-provided search_text as guidance, extract complete structure from content.

    NOTE: Concurrency control is handled by the caller (_compile_and_build_procedure).
    """
    user_prompt = COMPILER_USER_PROMPT.format(
        content=_truncate(content, 3000),
        candidate_json=candidate_json,
    )

    # No internal semaphore - caller handles concurrency via global semaphore
    result = await LLMService.extract_structured(
        text_input=user_prompt,
        system_prompt=COMPILER_SYSTEM_PROMPT,
        response_model=ProceduralWriteDraft,
    )
    return result


async def _compile_and_build_procedure(
    content: str,
    candidate: "ProceduralCandidate",
    nodeset: MemorySpace,
    source_refs: Optional[List[str]] = None,
    enable_incremental: bool = True,  # Enable incremental update
) -> Optional[Procedure]:
    """
    Compile a single ProceduralCandidate into a Procedure MemoryNode.

    With enable_incremental=True (default), uses incremental update:
    - Recalls similar existing procedures
    - Decides merge action (create_new / patch / new_version / skip)
    - Uses branch-specific compilation prompts
    - Manages versions with supersedes edges

    Used by:
    - write_procedural_from_decisions (unified routing flow)
    - write_procedural_memories
    - write_episodic_memories (procedural bridge optimization)

    Args:
        content: Source text to compile from
        candidate: ProceduralCandidate with search_text, confidence, reason, procedural_type
        nodeset: MemorySpace to assign the procedure to
        source_refs: Optional source tracing (e.g., ["episode:xxx"])
        enable_incremental: If True, use incremental update; if False, always create new

    Returns:
        Procedure MemoryNode or None if compilation fails or skipped
    """
    # Incremental update integration: Use incremental update when enabled
    if enable_incremental:
        try:
            return await process_candidate(
                candidate=candidate,
                content=content,
                nodeset=nodeset,
                source_refs=source_refs,
                enable_incremental=True,
            )
        except Exception as e:
            logger.error(f"[procedural.incremental] Incremental update failed: {e}, falling back to create_new")
            # Fall through to create_new path

    # Fallback path: always create new (no incremental update)
    async with get_global_llm_semaphore():
        try:
            # Build candidate JSON for Compiler
            candidate_json = json.dumps(
                {
                    "search_text": candidate.search_text,
                    "reason": candidate.reason,
                    "procedural_type": candidate.procedural_type,
                },
                ensure_ascii=False,
            )

            # Compile procedure
            draft = await _compile_procedure(content, candidate_json)

            # Security checks
            if draft.key_points and draft.key_points.points_text:
                if contains_dangerous_content(draft.key_points.points_text):
                    logger.warning(f"[procedural] Dangerous content in '{candidate.search_text[:40]}', skipping")
                    return None

            # Derive write_decision from confidence
            write_decision = "yes" if candidate.confidence >= 0.7 else "maybe"
            confidence_str = "high" if candidate.confidence >= 0.7 else "low"

            # Build MemoryNode
            procedure_dp = await _build_procedure_datapoints(
                draft=draft,
                confidence=confidence_str,
                nodeset=nodeset,
                write_decision=write_decision,
                write_reason=candidate.reason,
                evidence_refs=None,  # New model doesn't have this field
                source_refs=source_refs,
            )

            return procedure_dp

        except Exception as e:
            logger.error(
                f"[procedural] Compile failed for '{candidate.search_text[:40] if candidate.search_text else 'unknown'}': {e}"
            )
            return None


async def _build_procedure_datapoints(
    draft: ProceduralWriteDraft,
    confidence: str,
    nodeset: MemorySpace,
    # Soft gating metadata
    write_decision: Optional[str] = None,
    write_reason: Optional[str] = None,
    evidence_refs: Optional[List[str]] = None,
    # Source tracing
    source_refs: Optional[List[str]] = None,
) -> Optional[Procedure]:
    """Build Procedure MemoryNode with direct edges to Points (no Pack nodes).

    Architecture: Procedure → Point (2-layer triplet, no Pack intermediate).
    """

    # Generate ID (deterministic based on signature)
    procedure_id = str(generate_node_id(f"Procedure:{normalize_for_id(draft.signature)}"))

    # ============================================================
    # Step 1: Build context_text and points_text (display attributes)
    # ============================================================
    context_parts = []
    if draft.context.when_text:
        context_parts.append(f"When: {draft.context.when_text}")
    if draft.context.why_text:
        context_parts.append(f"Why: {draft.context.why_text}")
    if draft.context.boundary_text:
        context_parts.append(f"Boundary: {draft.context.boundary_text}")
    if draft.context.outcome_text:
        context_parts.append(f"Outcome: {draft.context.outcome_text}")
    if draft.context.prereq_text:
        context_parts.append(f"Prerequisites: {draft.context.prereq_text}")
    if draft.context.exception_text:
        context_parts.append(f"Exception: {draft.context.exception_text}")
    context_text = "; ".join(context_parts) if context_parts else ""

    points_text = draft.key_points.points_text or ""

    # ============================================================
    # Step 2: Build summary (only indexed field)
    # Must be before time extraction (time parses from summary text)
    # ============================================================
    summary_parts = []
    if context_text:
        summary_parts.append(f"{draft.search_text}: context - {context_text}")
    if points_text:
        summary_parts.append(f"{draft.search_text}: points - {points_text}")
    constructed_summary = "\n".join(summary_parts) if summary_parts else draft.search_text

    # ============================================================
    # Step 3: Time extraction (from constructed summary)
    # ============================================================
    time_result = extract_mentioned_time(
        text=constructed_summary,
        anchor_time_ms=None,  # Use current time as anchor
        min_confidence=0.5,
    )

    procedure_time_fields = {
        "mentioned_time_start_ms": time_result.start_ms if time_result.has_time else None,
        "mentioned_time_end_ms": time_result.end_ms if time_result.has_time else None,
        "mentioned_time_confidence": time_result.confidence if time_result.has_time else None,
        "mentioned_time_text": time_result.evidence_text if time_result.has_time else None,
    }

    if time_result.has_time:
        logger.info(
            f"[TIME_PROPAGATION] procedure={procedure_id[:12]}..., "
            f"start={time_result.start_ms}, end={time_result.end_ms}, "
            f"conf={time_result.confidence:.2f}"
        )

    # ============================================================
    # Step 4: Build ContextPoints (always generated, linked directly to Procedure)
    # ============================================================
    context_point_pairs = build_context_points(
        context_pack_id=procedure_id,  # Use procedure_id as parent (no Pack)
        when_text=draft.context.when_text,
        why_text=draft.context.why_text,
        boundary_text=draft.context.boundary_text,
        outcome_text=draft.context.outcome_text,
        prereq_text=draft.context.prereq_text,
        exception_text=draft.context.exception_text,
        context_anchor_text=context_text,
        time_fields=procedure_time_fields,
    )
    if context_point_pairs:
        for _, point in context_point_pairs:
            point.memory_spaces = [nodeset]
        logger.info(f"[procedural] Generated {len(context_point_pairs)} context points")

    # ============================================================
    # Step 5: Build KeyPoints (always generated, linked directly to Procedure)
    # ============================================================
    key_point_pairs = []
    if points_text:
        key_point_pairs = build_step_points(
            steps_pack_id=procedure_id,  # Use procedure_id as parent (no Pack)
            steps_anchor_text=points_text,
            time_fields=procedure_time_fields,
        )
        if key_point_pairs:
            for _, point in key_point_pairs:
                point.memory_spaces = [nodeset]
            logger.info(f"[procedural] Generated {len(key_point_pairs)} key points")

    # ============================================================
    # Step 6: Build Procedure with direct Point edges (no Pack)
    # ============================================================

    # Collect all has_context_point edges
    has_context_point_list = []
    for edge, point in context_point_pairs or []:
        # Defensive check: edge_text must be meaningful
        assert edge.edge_text and edge.edge_text != edge.relationship_type, (
            f"ContextPoint edge must have meaningful edge_text, got: {edge.edge_text}"
        )
        has_context_point_list.append((edge, point))

    # Collect all has_key_point edges
    has_key_point_list = []
    for edge, point in key_point_pairs or []:
        assert edge.edge_text and edge.edge_text != edge.relationship_type, (
            f"KeyPoint edge must have meaningful edge_text, got: {edge.edge_text}"
        )
        has_key_point_list.append((edge, point))

    procedure = Procedure(
        id=procedure_id,
        name=draft.title,
        summary=constructed_summary,
        search_text=draft.search_text,
        context_text=context_text or None,
        points_text=points_text or None,
        signature=draft.signature,
        confidence=confidence,
        # Soft gating metadata (traceability)
        write_decision=write_decision,
        write_reason=write_reason,
        evidence_refs=evidence_refs,
        source_refs=source_refs,
        # Direct Point edges (no Pack intermediate)
        has_context_point=has_context_point_list if has_context_point_list else None,
        has_key_point=has_key_point_list if has_key_point_list else None,
        memory_spaces=[nodeset],
        **procedure_time_fields,
    )

    if procedure_time_fields.get("mentioned_time_start_ms"):
        logger.info(
            f"[TIME_PROPAGATION] Procedure created: procedure={procedure_id[:12]}..., "
            f"title='{draft.title[:30]}...', "
            f"context_points={len(has_context_point_list)}, "
            f"key_points={len(has_key_point_list)}"
        )

    return procedure
