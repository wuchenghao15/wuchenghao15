# m_flow/memory/episodic/facet_points_refiner.py
"""
Stage 5: FacetPoint write quality enhancement

Goal: Make FacetPoint truly stable "tip anchors":
- Less noise (quality threshold + rewrite)
- Less duplication (semantic deduplication and merging)
- Less generalization (coverage validation and completion)
- Stronger explainability (evidence linking)

Achieve "coverage without omission" without prescribing "generation quantity/character count".
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from m_flow.shared.logging_utils import get_logger
from m_flow.adapters.vector import get_vector_provider
from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.prompts import read_query_prompt

from m_flow.memory.episodic.models import FacetPointDraft
from m_flow.memory.episodic.llm_call_tracker import get_llm_tracker

logger = get_logger("FacetPointsRefiner")


# ============================================================
# Environment variable switches (imported from env_utils.py)
# ============================================================
from m_flow.memory.episodic.env_utils import as_bool_env as _as_bool_env
from m_flow.memory.episodic.env_utils import as_float_env as _as_float_env


# ============================================================
# 5.1 Quality threshold: Point must be "tip handle"
# ============================================================

# Overly generic terms list
GENERIC_TERMS = {
    "原因",
    "影响",
    "问题",
    "风险",
    "方案",
    "进展",
    "结论",
    "总结",
    "步骤",
    "策略",
    "优化",
    "处理",
    "背景",
    "目标",
    "决策",
    "计划",
    "结果",
    "内容",
    "情况",
    "说明",
    "备注",
    "其他",
    "概述",
    "简介",
    "详情",
    "分析",
    "评估",
    "cause",
    "effect",
    "issue",
    "risk",
    "solution",
    "progress",
    "conclusion",
    "summary",
    "step",
    "strategy",
    "optimization",
    "background",
    "goal",
    "decision",
    "plan",
    "result",
    "content",
    "overview",
    "analysis",
}


def _normalize_aggressive(text: str) -> str:
    """
    Aggressive normalization: removes ALL punctuation and whitespace.

    Used for deduplication where punctuation differences should be ignored.
    Note: Different from normalization.normalize_for_compare which only collapses whitespace.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    return text


def _has_concrete_anchor(text: str) -> bool:
    """Check if text contains concrete anchors (numbers, entities, etc.)."""
    if not text:
        return False

    # Numeric anchors
    if re.search(r"\d+(\.\d+)?[%％]", text):
        return True
    if re.search(r"\d{2,}", text):  # At least 2 digits
        return True

    # Special tokens (camelCase, underscores, path segments, uppercase abbreviations)
    if re.search(r"[A-Z][a-z]+[A-Z]", text):  # CamelCase
        return True
    if re.search(r"\w+_\w+", text):  # Underscores
        return True
    if re.search(r"[A-Z]{2,}", text):  # Uppercase abbreviations
        return True

    # Chinese quantity words
    if re.search(r"[零一二三四五六七八九十百千万亿]+[个条项份次]", text):
        return True

    return False


def _is_paragraph_style(text: str) -> bool:
    """Check if text is paragraph-like (should be in description, not search_text)."""
    if not text:
        return False

    # Multiple periods/newlines/semicolons
    if text.count("。") > 1 or text.count("\n") > 0 or text.count("；") > 1:
        return True

    # Too long (single sentence over 100 chars might be a paragraph)
    if len(text) > 100 and "。" not in text[:50]:
        return True

    return False


def _is_too_generic(text: str) -> bool:
    """Check if text is too generic (only contains generic terms)."""
    if not text:
        return True

    norm = _normalize_aggressive(text)
    if len(norm) < 3:
        return True

    # Only contains generic terms
    for term in GENERIC_TERMS:
        if norm == _normalize_aggressive(term):
            return True

    return False


def is_bad_point_handle(text: str) -> bool:
    """
    Determine if a point.search_text is unqualified.

    Unqualified conditions:
    - Overly generic terms (only "原因/影响/问题" etc.)
    - Paragraph-like (multiple periods/newlines)
    - No anchors (doesn't contain numbers/entities/module names etc.)
    """
    if not text or not text.strip():
        return True

    text = text.strip()

    # Overly generic terms
    if _is_too_generic(text):
        return True

    # Paragraph-like
    if _is_paragraph_style(text):
        return True

    # No anchors (not absolute judgment, only consider bad when text is also short)
    if len(text) < 15 and not _has_concrete_anchor(text):
        # Short text with no anchors → might be generic term
        norm = _normalize_aggressive(text)
        if any(_normalize_aggressive(g) in norm for g in GENERIC_TERMS):
            return True

    return False


async def rewrite_point_handle(
    text: str,
    prompt_file: str = "episodic_point_rewrite.txt",
) -> Optional[str]:
    """
    Rewrite unqualified point to sharp handle.

    Use LLM structured output to rewrite paragraph-like or overly generic points into short, sharp retrieval handles.
    """
    if _as_bool_env("MOCK_EPISODIC", False):
        return text[:50] if text else None

    system_prompt = read_query_prompt(prompt_file)
    if not system_prompt:
        # fallback: direct truncation
        return text[:80] if text else None

    # Define structured output model
    from pydantic import BaseModel, Field

    class RewriteResult(BaseModel):
        rewritten: str = Field(
            ...,
            description="The rewritten short, sharp retrieval handle (10-60 chars)",
            max_length=80,
        )

    try:
        result = await LLMService.extract_structured(
            text_input=f"Original text to rewrite:\n{text}",
            system_prompt=system_prompt,
            response_model=RewriteResult,
        )
        rewritten = (result.rewritten or "").strip()
        if rewritten and len(rewritten) > 3:
            return rewritten
        return text[:80]
    except Exception as e:
        logger.debug(f"Point rewrite failed: {e}")
        return text[:80] if text else None


# ============================================================
# 5.2 Semantic deduplication and merging
# ============================================================


@dataclass
class PointCluster:
    """A cluster of semantically similar points."""

    representative: FacetPointDraft
    members: List[FacetPointDraft] = field(default_factory=list)
    merged_aliases: List[str] = field(default_factory=list)


async def semantic_dedup_points(
    points: List[FacetPointDraft],
    similarity_threshold: float = 0.92,
) -> List[FacetPointDraft]:
    """
    Perform semantic deduplication and merging on points.

    Select best representative within same cluster, add remaining handles to aliases.
    """
    if not points or len(points) <= 1:
        return points

    try:
        vector_engine = get_vector_provider()
        embedding_engine = vector_engine.embedding_engine
    except Exception as e:
        logger.debug(f"Cannot get embedding engine for dedup: {e}")
        return points

    # Get embeddings for all search_text
    texts = [p.search_text for p in points]
    try:
        embeddings = await embedding_engine.embed_text(texts)
    except Exception as e:
        logger.debug(f"Embedding failed for dedup: {e}")
        return points

    if not embeddings or len(embeddings) != len(points):
        return points

    # Calculate similarity matrix and cluster
    embeddings_np = np.array(embeddings)

    # Normalize
    norms = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
    norms[norms == 0] = 1
    embeddings_np = embeddings_np / norms

    # Cosine similarity
    sim_matrix = embeddings_np @ embeddings_np.T

    # Simple clustering: greedy merging
    n = len(points)
    used = [False] * n
    clusters: List[PointCluster] = []

    for i in range(n):
        if used[i]:
            continue

        cluster_indices = [i]
        used[i] = True

        for j in range(i + 1, n):
            if used[j]:
                continue
            if sim_matrix[i, j] >= similarity_threshold:
                cluster_indices.append(j)
                used[j] = True

        # Select representative: prioritize those with number/entity anchors, then shorter ones
        best_idx = cluster_indices[0]
        best_score = -1

        for idx in cluster_indices:
            p = points[idx]
            score = 0
            if _has_concrete_anchor(p.search_text):
                score += 10
            score -= len(p.search_text) / 100  # Shorter is better
            if score > best_score:
                best_score = score
                best_idx = idx

        representative = points[best_idx]
        members = [points[idx] for idx in cluster_indices if idx != best_idx]

        # Merge aliases
        merged_aliases = list(representative.aliases or [])
        for m in members:
            if m.search_text and m.search_text not in merged_aliases:
                merged_aliases.append(m.search_text)
            if m.aliases:
                for a in m.aliases:
                    if a and a not in merged_aliases:
                        merged_aliases.append(a)

        clusters.append(
            PointCluster(
                representative=representative,
                members=members,
                merged_aliases=merged_aliases,
            )
        )

    # Build deduplicated points
    deduped: List[FacetPointDraft] = []
    for cluster in clusters:
        p = cluster.representative
        # Update aliases
        new_aliases = cluster.merged_aliases[:10]  # Safe cap
        deduped.append(
            FacetPointDraft(
                search_text=p.search_text,
                aliases=new_aliases,
                description=p.description,
            )
        )

    return deduped


# ============================================================
# 5.3 Coverage validation and completion
# ============================================================


def extract_anchors_from_description(description: str) -> Set[str]:
    """
    Extract anchor clues from facet.description.
    """
    anchors: Set[str] = set()
    if not description:
        return anchors

    # Numeric anchors (percentages, numbers with units)
    for m in re.finditer(r"\d+(\.\d+)?[%％]", description):
        anchors.add(m.group())

    for m in re.finditer(r"\d+(\.\d+)?\s*(万|亿|元|秒|ms|天|小时|分钟|次|个|条)", description):
        anchors.add(m.group().strip())

    # Special tokens (camelCase, underscore naming)
    for m in re.finditer(r"[A-Z][a-z]+(?:[A-Z][a-z]+)+", description):
        anchors.add(m.group())

    for m in re.finditer(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", description):
        if "_" in m.group():
            anchors.add(m.group())

    # Uppercase abbreviations (e.g., API, SDK, RAG)
    for m in re.finditer(r"\b[A-Z]{2,5}\b", description):
        anchors.add(m.group())

    return anchors


def check_coverage(
    points: List[FacetPointDraft],
    anchors: Set[str],
) -> Set[str]:
    """
    Check if points cover all anchors.
    Returns uncovered anchors.
    """
    covered: Set[str] = set()

    for anchor in anchors:
        anchor_lower = anchor.lower()
        for p in points:
            # Check search_text
            if anchor_lower in (p.search_text or "").lower():
                covered.add(anchor)
                break
            # Check aliases
            if p.aliases:
                for a in p.aliases:
                    if anchor_lower in (a or "").lower():
                        covered.add(anchor)
                        break

    return anchors - covered


async def generate_missing_points(
    facet_description: str,
    missing_anchors: Set[str],
    prompt_file: str = "episodic_point_generate_missing.txt",
) -> List[FacetPointDraft]:
    """
    Generate FacetPoints for uncovered anchors.
    """
    if not missing_anchors:
        return []

    if _as_bool_env("MOCK_EPISODIC", False):
        return [FacetPointDraft(search_text=a, aliases=[], description=None) for a in list(missing_anchors)[:3]]

    system_prompt = read_query_prompt(prompt_file)
    if not system_prompt:
        logger.warning(f"Missing prompt file: {prompt_file}")
        return []

    from pydantic import BaseModel, Field

    class MissingPointsResult(BaseModel):
        points: List[FacetPointDraft] = Field(default_factory=list)

    text_input = f"""FACET_DESCRIPTION:
{facet_description}

MISSING_ANCHORS:
{", ".join(missing_anchors)}
"""

    try:
        # Use tracker to track LLM calls
        tracker = get_llm_tracker()
        async with tracker.track("generate_missing_points", text_input, MissingPointsResult):
            result = await LLMService.extract_structured(
                text_input=text_input,
                system_prompt=system_prompt,
                response_model=MissingPointsResult,
            )
            tracker.record_attempt(1)
        return result.points or []
    except Exception as e:
        logger.debug(f"Generate missing points failed: {e}")
        return []


# ============================================================
# 5.5 Evidence Linking
# ============================================================


@dataclass
class EvidenceLink:
    """Evidence link from FacetPoint to ContentFragment."""

    point_search_text: str
    chunk_id: str
    chunk_index: int
    similarity_score: float
    chunk_snippet: str = ""


async def link_point_evidence(
    points: List[FacetPointDraft],
    facet_search_text: str,
    candidate_chunk_ids: List[str],
    candidate_chunks: List[dict],  # List of {id, text, chunk_index}
    top_k: int = 2,
) -> Dict[str, List[EvidenceLink]]:
    """
    Link evidence chunks for each point.

    Args:
        points: FacetPoint list
        facet_search_text: Facet's search_text
        candidate_chunk_ids: Candidate chunk ID list
        candidate_chunks: Candidate chunk details
        top_k: Maximum number of chunks to link per point

    Returns:
        Dict[point_search_text -> List[EvidenceLink]]
    """
    if not points or not candidate_chunks:
        return {}

    try:
        vector_engine = get_vector_provider()
        embedding_engine = vector_engine.embedding_engine
    except Exception as e:
        logger.debug(f"Cannot get embedding engine for evidence: {e}")
        return {}

    # Build mapping from chunk text to chunk info
    chunk_map = {c.get("id", ""): c for c in candidate_chunks if c.get("id")}
    chunk_texts = [c.get("text", "") for c in candidate_chunks if c.get("id")]
    chunk_ids = [c.get("id", "") for c in candidate_chunks if c.get("id")]

    if not chunk_texts:
        return {}

    # Embed chunks
    try:
        chunk_embeddings = await embedding_engine.embed_text(chunk_texts)
    except Exception as e:
        logger.debug(f"Chunk embedding failed: {e}")
        return {}

    if not chunk_embeddings:
        return {}

    chunk_embeddings_np = np.array(chunk_embeddings)
    norms = np.linalg.norm(chunk_embeddings_np, axis=1, keepdims=True)
    norms[norms == 0] = 1
    chunk_embeddings_np = chunk_embeddings_np / norms

    # Batch embed all point queries (concurrency optimization)
    query_texts = [f"{p.search_text}\n{facet_search_text}" for p in points]

    try:
        query_embeddings = await embedding_engine.embed_text(query_texts)
    except Exception as e:
        logger.debug(f"Batch point embedding failed: {e}")
        return {}

    if not query_embeddings or len(query_embeddings) != len(points):
        return {}

    # Normalize all query embeddings
    query_embeddings_np = np.array(query_embeddings)
    query_norms = np.linalg.norm(query_embeddings_np, axis=1, keepdims=True)
    query_norms[query_norms == 0] = 1
    query_embeddings_np = query_embeddings_np / query_norms

    # Batch compute similarity matrix (points x chunks)
    similarities_matrix = query_embeddings_np @ chunk_embeddings_np.T

    # Find top_k evidence for each point
    evidence_map: Dict[str, List[EvidenceLink]] = {}

    for i, p in enumerate(points):
        similarities = similarities_matrix[i]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        links: List[EvidenceLink] = []
        for idx in top_indices:
            cid = chunk_ids[idx]
            if cid not in candidate_chunk_ids:
                continue

            chunk_info = chunk_map.get(cid, {})
            links.append(
                EvidenceLink(
                    point_search_text=p.search_text,
                    chunk_id=cid,
                    chunk_index=int(chunk_info.get("chunk_index", -1)),
                    similarity_score=float(similarities[idx]),
                    chunk_snippet=str(chunk_info.get("text", ""))[:100],
                )
            )

        if links:
            evidence_map[p.search_text] = links

    return evidence_map


# ============================================================
# Main function: refine_facet_points
# ============================================================


@dataclass
class RefineStats:
    """Statistics for point refinement."""

    raw_points_count: int = 0
    rewritten_count: int = 0
    dropped_count: int = 0
    dedup_before_count: int = 0
    dedup_after_count: int = 0
    coverage_missing_anchors: int = 0
    coverage_generated_points: int = 0
    final_points_count: int = 0
    evidence_links_count: int = 0


async def refine_facet_points(
    raw_points: List[FacetPointDraft],
    facet_search_text: str,
    facet_description: str,
    candidate_chunks: Optional[List[dict]] = None,
    *,
    enable_rewrite: Optional[bool] = None,
    enable_semantic_dedup: Optional[bool] = None,
    enable_coverage_guard: Optional[bool] = None,
    enable_evidence_link: Optional[bool] = None,
    dedup_similarity_threshold: Optional[float] = None,
) -> Tuple[List[FacetPointDraft], Dict[str, List[EvidenceLink]], RefineStats]:
    """
    Stage5 main entry: quality enhancement for raw_points.

    Args:
        raw_points: Raw points extracted by LLM
        facet_search_text: Facet's search_text
        facet_description: Facet's description
        candidate_chunks: Candidate evidence chunks (for evidence linking)

    Returns:
        (refined_points, evidence_map, stats)
    """
    # Read configuration
    if enable_rewrite is None:
        enable_rewrite = _as_bool_env("MFLOW_EPISODIC_POINT_REWRITE", True)
    if enable_semantic_dedup is None:
        enable_semantic_dedup = _as_bool_env("MFLOW_EPISODIC_POINT_SEMANTIC_DEDUP", True)
    if enable_coverage_guard is None:
        enable_coverage_guard = _as_bool_env("MFLOW_EPISODIC_POINT_COVERAGE_GUARD", True)
    if enable_evidence_link is None:
        enable_evidence_link = _as_bool_env("MFLOW_EPISODIC_POINT_EVIDENCE_LINK", False)  # disabled by default
    if dedup_similarity_threshold is None:
        dedup_similarity_threshold = _as_float_env("MFLOW_EPISODIC_POINT_DEDUP_SIM", 0.92)

    stats = RefineStats(raw_points_count=len(raw_points))

    if not raw_points:
        return [], {}, stats

    # ============================================================
    # Step 1: Quality threshold + rewrite (concurrency optimization)
    # ============================================================
    qualified_points: List[FacetPointDraft] = []

    # Classify: good points vs bad points (need rewrite)
    good_points: List[FacetPointDraft] = []
    bad_points_to_rewrite: List[Tuple[int, FacetPointDraft]] = []  # (original index, point)

    for idx, p in enumerate(raw_points):
        st = (p.search_text or "").strip()
        if not st:
            stats.dropped_count += 1
            continue

        if is_bad_point_handle(st):
            if enable_rewrite:
                bad_points_to_rewrite.append((idx, p))
            else:
                stats.dropped_count += 1
        else:
            good_points.append(p)

    # Concurrently rewrite all bad points
    if bad_points_to_rewrite:

        async def _do_rewrite(idx: int, p: FacetPointDraft) -> Tuple[int, Optional[FacetPointDraft]]:
            st = (p.search_text or "").strip()
            rewritten = await rewrite_point_handle(st)
            if rewritten and not is_bad_point_handle(rewritten):
                return idx, FacetPointDraft(
                    search_text=rewritten,
                    aliases=p.aliases,
                    description=p.description,
                )
            return idx, None

        rewrite_results = await asyncio.gather(*[_do_rewrite(idx, p) for idx, p in bad_points_to_rewrite])

        for _idx, result in rewrite_results:  # _idx unused but required for unpacking
            if result is not None:
                good_points.append(result)
                stats.rewritten_count += 1
            else:
                stats.dropped_count += 1

    qualified_points = good_points

    # ============================================================
    # Step 2: Semantic deduplication and merging
    # ============================================================
    stats.dedup_before_count = len(qualified_points)

    if enable_semantic_dedup and len(qualified_points) > 1:
        qualified_points = await semantic_dedup_points(
            qualified_points,
            similarity_threshold=dedup_similarity_threshold,
        )

    stats.dedup_after_count = len(qualified_points)

    # ============================================================
    # Step 3: Coverage verification and supplementation
    # ============================================================
    if enable_coverage_guard and facet_description:
        anchors = extract_anchors_from_description(facet_description)
        missing = check_coverage(qualified_points, anchors)
        stats.coverage_missing_anchors = len(missing)

        if missing:
            generated = await generate_missing_points(
                facet_description=facet_description,
                missing_anchors=missing,
            )
            stats.coverage_generated_points = len(generated)

            if generated:
                # Merge and deduplicate again
                all_points = qualified_points + generated
                if enable_semantic_dedup:
                    qualified_points = await semantic_dedup_points(
                        all_points,
                        similarity_threshold=dedup_similarity_threshold,
                    )
                else:
                    qualified_points = all_points

    stats.final_points_count = len(qualified_points)

    # ============================================================
    # Step 4: Evidence linking
    # ============================================================
    evidence_map: Dict[str, List[EvidenceLink]] = {}

    if enable_evidence_link and candidate_chunks:
        candidate_ids = [c.get("id", "") for c in candidate_chunks if c.get("id")]
        evidence_map = await link_point_evidence(
            points=qualified_points,
            facet_search_text=facet_search_text,
            candidate_chunk_ids=candidate_ids,
            candidate_chunks=candidate_chunks,
            top_k=2,
        )
        stats.evidence_links_count = sum(len(v) for v in evidence_map.values())

    # ============================================================
    # Log output
    # ============================================================
    logger.info(
        f"[Stage5] Refine points: facet='{facet_search_text[:30]}...', "
        f"raw={stats.raw_points_count}, rewritten={stats.rewritten_count}, "
        f"dropped={stats.dropped_count}, dedup={stats.dedup_before_count}->{stats.dedup_after_count}, "
        f"coverage_gaps={stats.coverage_missing_anchors}, generated={stats.coverage_generated_points}, "
        f"final={stats.final_points_count}, evidence={stats.evidence_links_count}"
    )

    return qualified_points, evidence_map, stats
