"""
Episodic Memory LLM task module

Centralizes all functions that interact with LLM, including:
1. Entity selection (_llm_select_entities)
2. Entity name extraction (_llm_extract_entity_names)
3. Entity description generation (_llm_write_entity_descriptions)
4. FacetPoint extraction (_llm_extract_facet_points)

Phase 2: Extracted from write_episodic_memories.py

All functions support MOCK_EPISODIC environment variable to skip LLM calls.

Note: llm_compile_episode and llm_review_and_supplement have been removed.
Facet generation now directly uses section-based path (zero information loss).
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from m_flow.shared.logging_utils import get_logger
from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.prompts import read_query_prompt

from m_flow.memory.episodic.models import (
    ConceptSelectionResult,
    ConceptNamesResult,
    ConceptDescriptionResult,
    FacetPointExtractionResult,
)
from m_flow.memory.episodic.llm_call_tracker import get_llm_tracker, LLMCallTracker

if TYPE_CHECKING:
    pass


logger = get_logger("episodic.llm_tasks")


# ============================================================
# Environment variable utilities (imported from env_utils.py)
# ============================================================
from m_flow.memory.episodic.env_utils import as_bool_env as _as_bool_env


# ============================================================
# LLM Tracker retrieval
# ============================================================

_llm_tracker: LLMCallTracker = None


def _get_tracker() -> LLMCallTracker:
    """Get or create LLM call tracker"""
    global _llm_tracker
    if _llm_tracker is None:
        _llm_tracker = get_llm_tracker()
    return _llm_tracker


# ============================================================
# 1. Entity selection
# ============================================================


async def llm_select_entities(
    *,
    chunk_summaries: List[str],
    generated_facets: List[str],
    candidate_entities: List[str],
) -> ConceptSelectionResult:
    """
    Select and describe entities for each facet (separate LLM pass).

    Args:
        chunk_summaries: Original source material (GROUND TRUTH)
        generated_facets: List of "search_text | description"
        candidate_entities: List of "name | description"

    Returns:
        ConceptSelectionResult with entity mappings for each facet
    """
    if _as_bool_env("MOCK_EPISODIC", False):
        return ConceptSelectionResult(facet_entities=[])

    if not generated_facets or not candidate_entities:
        return ConceptSelectionResult(facet_entities=[])

    system_prompt = read_query_prompt("episodic_select_entities.txt")
    if not system_prompt:
        logger.warning("Missing entity selection prompt file, skipping")
        return ConceptSelectionResult(facet_entities=[])

    content_lines: List[str] = []

    content_lines.append("CHUNK_SUMMARIES (GROUND TRUTH):")
    content_lines.extend([f"- {s}" for s in chunk_summaries] or ["- (none)"])

    content_lines.append("\nGENERATED_FACETS:")
    content_lines.extend([f"- {f}" for f in generated_facets])

    content_lines.append("\nCANDIDATE_ENTITIES:")
    content_lines.extend([f"- {e}" for e in candidate_entities])

    text_input = "\n".join(content_lines)

    logger.info("[episodic] ========== Entity Selection LLM ==========")
    logger.info(
        f"[episodic] Entity Selection Input Stats: "
        f"chunk_summaries={len(chunk_summaries)}, "
        f"generated_facets={len(generated_facets)}, "
        f"candidate_entities={len(candidate_entities)}, text_len={len(text_input)}"
    )
    logger.info(
        f"[episodic] Entity Selection Input Text:\n{text_input[:2500]}{'...(truncated)' if len(text_input) > 2500 else ''}"
    )

    try:
        tracker = _get_tracker()
        async with tracker.track("entity_selection", text_input, ConceptSelectionResult):
            result = await LLMService.extract_structured(
                text_input=text_input,
                system_prompt=system_prompt,
                response_model=ConceptSelectionResult,
            )
            tracker.record_attempt(1)

        logger.info(
            f"[episodic] Entity Selection Output: "
            f"facet_mappings={len(result.facet_entities) if result.facet_entities else 0}"
        )

        if result.facet_entities:
            for mapping in result.facet_entities:
                entity_names = [e.name for e in (mapping.entities or [])]
                logger.info(f"[episodic] Facet '{mapping.facet_search_text}' -> entities: {entity_names}")
                for e in mapping.entities or []:
                    logger.info(
                        f"  - {e.name}: {e.context_description[:100] if e.context_description else '(empty)'}..."
                    )

        return result

    except Exception as e:
        logger.warning(f"Entity selection LLM failed: {e}")
        return ConceptSelectionResult(facet_entities=[])


# ============================================================
# 2. Entity name extraction
# ============================================================


async def llm_extract_entity_names(
    *,
    text: str,
    batch_index: int = 0,
) -> ConceptNamesResult:
    """
    Extract entity names from text using extract_entity_names.txt prompt.

    Args:
        text: Text to extract entities from
        batch_index: Batch index for logging

    Returns:
        ConceptNamesResult with list of entity names
    """
    if _as_bool_env("MOCK_EPISODIC", False):
        return ConceptNamesResult(names=[])

    if not text or not text.strip():
        return ConceptNamesResult(names=[])

    system_prompt = read_query_prompt("extract_entity_names.txt")
    if not system_prompt:
        logger.warning("Missing extract_entity_names.txt prompt file, skipping")
        return ConceptNamesResult(names=[])

    logger.info(f"[episodic] ========== Entity Name Extraction LLM (batch {batch_index}) ==========")
    logger.info(f"[episodic] Entity Name Extraction Input: batch={batch_index}, text_len={len(text)}")

    try:
        tracker = _get_tracker()
        async with tracker.track("entity_name_extraction", text, ConceptNamesResult):
            result = await LLMService.extract_structured(
                text_input=text,
                system_prompt=system_prompt,
                response_model=ConceptNamesResult,
            )
            tracker.record_attempt(1)

        logger.info(
            f"[episodic] Entity Name Extraction Output (batch {batch_index}): "
            f"names={len(result.names) if result.names else 0}"
        )

        return result

    except Exception as e:
        logger.warning(f"Entity name extraction LLM failed (batch {batch_index}): {e}")
        return ConceptNamesResult(names=[])


# ============================================================
# 3. Entity description generation
# ============================================================


async def llm_write_entity_descriptions(
    *,
    entity_names: List[str],
    source_text: str,
    batch_index: int = 0,
) -> ConceptDescriptionResult:
    """
    Write descriptions for a batch of entities (no selection, all entities).

    Args:
        entity_names: List of entity names to describe
        source_text: Full source text for context
        batch_index: Batch index for logging

    Returns:
        ConceptDescriptionResult with descriptions for all input entities
    """
    if _as_bool_env("MOCK_EPISODIC", False):
        return ConceptDescriptionResult(descriptions=[])

    if not entity_names:
        return ConceptDescriptionResult(descriptions=[])

    system_prompt = read_query_prompt("write_entity_descriptions.txt")
    if not system_prompt:
        logger.warning("Missing entity description prompt file, skipping")
        return ConceptDescriptionResult(descriptions=[])

    content_lines: List[str] = []
    content_lines.append("ENTITY_NAMES:")
    content_lines.extend([f"- {n}" for n in entity_names])
    content_lines.append("\nSOURCE_TEXT:")
    content_lines.append(source_text)

    text_input = "\n".join(content_lines)

    logger.info(f"[episodic] ========== Entity Description LLM (batch {batch_index}) ==========")
    logger.info(
        f"[episodic] Entity Description Input: "
        f"batch={batch_index}, entities={len(entity_names)}, text_len={len(text_input)}"
    )

    try:
        tracker = _get_tracker()
        async with tracker.track("entity_description", text_input, ConceptDescriptionResult):
            result = await LLMService.extract_structured(
                text_input=text_input,
                system_prompt=system_prompt,
                response_model=ConceptDescriptionResult,
            )
            tracker.record_attempt(1)

        logger.info(
            f"[episodic] Entity Description Output (batch {batch_index}): "
            f"descriptions={len(result.descriptions) if result.descriptions else 0}"
        )

        return result

    except Exception as e:
        logger.warning(f"Entity description LLM failed (batch {batch_index}): {e}")
        return ConceptDescriptionResult(descriptions=[])


# ============================================================
# 4. FacetPoint extraction
# ============================================================


async def llm_extract_facet_points(
    *,
    facet_type: str,
    facet_search_text: str,
    facet_description: str,
    existing_points: List[str],
    prompt_file_name: str = "episodic_extract_facet_points.txt",
) -> FacetPointExtractionResult:
    """
    Extract FacetPoints from one Facet description.

    We treat facet_description as the ground truth (already dense and complete),
    so we do NOT need to pass chunk_summaries here.

    Args:
        facet_type: Facet type
        facet_search_text: Facet search text
        facet_description: Facet description (as ground truth)
        existing_points: Existing FacetPoint list (for deduplication)
        prompt_file_name: Prompt file name

    Returns:
        FacetPointExtractionResult containing extracted FacetPoints
    """
    if _as_bool_env("MOCK_EPISODIC", False):
        return FacetPointExtractionResult(facet_search_text=facet_search_text, points=[])

    system_prompt = read_query_prompt(prompt_file_name)
    if not system_prompt:
        raise ValueError(f"Missing facet point prompt file: {prompt_file_name}")

    content_lines: List[str] = []
    content_lines.append(f"Facet Type: {facet_type}")
    content_lines.append(f"Facet Name: {facet_search_text}")
    content_lines.append("Facet Description (GROUND TRUTH):")
    content_lines.append(facet_description.strip())

    content_lines.append("\nExisting Points:")
    if existing_points:
        content_lines.extend([f"- {p}" for p in existing_points])
    else:
        content_lines.append("- (none)")

    text_input = "\n".join(content_lines)

    logger.info("[episodic] ========== FacetPoint Extraction LLM ==========")
    logger.info(
        f"[episodic] FacetPoint Input Stats: facet={facet_search_text}, "
        f"desc_len={len(facet_description)}, existing_points={len(existing_points)}, "
        f"text_len={len(text_input)}"
    )

    tracker = _get_tracker()
    async with tracker.track("facet_point_extraction", text_input, FacetPointExtractionResult):
        result = await LLMService.extract_structured(
            text_input=text_input,
            system_prompt=system_prompt,
            response_model=FacetPointExtractionResult,
        )
        tracker.record_attempt(1)

    logger.info(
        f"[episodic] FacetPoint Output: facet={facet_search_text}, points={len(result.points) if result.points else 0}"
    )
    return result


# ============================================================
# Backward compatibility aliases (with underscore prefix)
# ============================================================

# These aliases are used to maintain the original naming style in write_episodic_memories.py
_llm_select_entities = llm_select_entities
_llm_extract_entity_names = llm_extract_entity_names
_llm_write_entity_descriptions = llm_write_entity_descriptions
_llm_extract_facet_points = llm_extract_facet_points
