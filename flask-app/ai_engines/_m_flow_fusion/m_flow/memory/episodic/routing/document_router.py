"""
Document Routing Module.

This module handles routing documents/events to Episodes.
Extracted from write_episodic_memories.py during Phase 3 of the large file refactoring.

v1.3 Optimization: PARALLEL entity extraction and routing
- Entity extraction and routing now run concurrently (not serially)
- Routing no longer depends on entity names (entity info removed from routing_text)
- Estimated 34.6% reduction in routing phase time

Main function:
- route_documents_to_episodes: Route input documents to Episodes using vector search + LLM

Internal functions:
- _extract_entities_task: Extract entities for a single document (nested)
- _route_doc_task: Route a single document to episode (nested)
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.llm_concurrency import (
    get_global_llm_semaphore,
    get_llm_concurrency_limit,
)
from m_flow.core.domain.utils.generate_node_id import generate_node_id
from m_flow.knowledge.summarization.models import FragmentDigest
from m_flow.memory.episodic.utils.models import RoutingResult
from m_flow.memory.episodic.utils.pure_functions import (
    _extract_chunk_summaries_from_text_summaries,
    _has_valid_sections,
)
from m_flow.memory.episodic.normalization import _nfkc
from m_flow.memory.episodic.llm_tasks import (
    llm_extract_entity_names as _llm_extract_entity_names,
)
from m_flow.memory.episodic.episode_router import route_episode_id_for_doc

if TYPE_CHECKING:
    from m_flow.adapters.graph.graph_db_interface import GraphProvider
    from m_flow.adapters.vector.vector_db_interface import VectorProvider

logger = get_logger("episodic.routing.document_router")

# Minimum LLM concurrency to allow routing=False (parallel mode)
# Without sufficient LLM concurrency, parallel episode ingestion would
# overload the API. Fallback to routing=True (serial safe mode).
_MIN_CONCURRENCY_FOR_PARALLEL = 30


def _is_all_atomic_events(
    source_events: List[str],
    event_routing_types: Dict[str, str],
) -> bool:
    """
    Check if all source events are atomic events.

    An event is considered atomic if:
    1. Its event_id starts with "atomic_" (V2 atomic event), OR
    2. Its routing_type in event_routing_types is "atomic"

    Args:
        source_events: List of event IDs to check
        event_routing_types: Mapping of event_id -> routing_type

    Returns:
        True if all events are atomic, False otherwise
    """
    return all(evt.startswith("atomic_") or event_routing_types.get(evt) == "atomic" for evt in source_events)


def _extract_event_topic(
    doc_id: str,
    doc_summaries_sorted: List["FragmentDigest"],
) -> str:
    """
    Extract event_topic from sentence classifications for V2 mode.

    Searches through chunks' sentence_classifications to find the topic
    associated with the given event_id.

    Args:
        doc_id: The event ID to search for (e.g., "evt_xxx" or "atomic_xxx")
        doc_summaries_sorted: Sorted list of FragmentDigest objects

    Returns:
        Event topic string if found, empty string otherwise
    """
    for ts in doc_summaries_sorted:
        chunk = ts.made_from
        classifications = getattr(chunk, "metadata", {}).get("sentence_classifications", [])
        for c in classifications:
            if c.get("event_id") == doc_id:
                event_topic = c.get("event_topic") or c.get("suggested_topic") or ""
                if event_topic:
                    return event_topic
    return ""


async def route_documents_to_episodes(
    by_doc: Dict[str, List["FragmentDigest"]],
    *,
    graph_engine: "GraphProvider",
    vector_engine: "VectorProvider",
    enable_episode_routing: bool,
    enable_llm_entity_for_routing: bool,
    max_entities_per_episode: int,
    max_chunk_summaries_in_prompt: int,
    event_routing_types: Optional[Dict[str, str]] = None,  # event_id -> "episodic" | "atomic"
    target_nodeset_id: Optional[str] = None,  # For dataset isolation in routing (graph level)
    target_dataset_id: Optional[str] = None,  # For dataset isolation in routing (vector filter)
) -> RoutingResult:
    """
    Route input documents to Episodes using the following strategy:
    1. If episode_routing is enabled, use vector search + LLM to match existing Episodes
    2. Otherwise, create new Episode for each document

    Args:
        by_doc: Document ID -> FragmentDigest list mapping
        graph_engine: Graph database engine
        vector_engine: Vector database engine
        enable_episode_routing: Whether to enable Episode routing
        enable_llm_entity_for_routing: Whether to use LLM to extract Entity names (for routing)
        max_entities_per_episode: Maximum number of Entities per Episode
        max_chunk_summaries_in_prompt: Maximum number of chunk summaries in prompt
        event_routing_types: Original event_id to routing_type mapping (for tracking memory_type)
        target_nodeset_id: Only route to Episodes in this nodeset (dataset isolation)

    Returns:
        RoutingResult: Contains routing results, document titles, Entity cache and routing decisions
    """
    by_episode: Dict[str, List[FragmentDigest]] = {}
    episode_doc_titles: Dict[str, List[str]] = {}
    doc_entity_cache: Dict[str, List[str]] = {}
    routing_decisions: Dict[str, str] = {}  # episode_id -> "new" | "existing" | "disabled"
    episode_source_events: Dict[str, List[str]] = {}  # episode_id -> [event_id, ...]
    episode_memory_types: Dict[str, str] = {}  # episode_id -> "episodic" | "atomic"

    # Prepare event_routing_types for V1 mode (default to "episodic" for unknown)
    _event_routing_types = event_routing_types or {}

    # ============================================================
    # Safety guard: require MFLOW_LLM_CONCURRENCY_LIMIT >= 30 to allow routing=False
    # Without sufficient LLM concurrency, parallel episode ingestion would
    # overload the API. Fallback to routing=True (serial safe mode).
    # ============================================================
    if not enable_episode_routing:
        _llm_concurrency_limit = get_llm_concurrency_limit()
        if _llm_concurrency_limit < _MIN_CONCURRENCY_FOR_PARALLEL:
            logger.warning(
                f"[episodic][routing] enable_episode_routing=False requested, "
                f"but MFLOW_LLM_CONCURRENCY_LIMIT={_llm_concurrency_limit} < {_MIN_CONCURRENCY_FOR_PARALLEL}. "
                f"Parallel episode ingestion requires at least {_MIN_CONCURRENCY_FOR_PARALLEL} "
                f"concurrent LLM slots. Falling back to routing=True (serial mode). "
                f"Set MFLOW_LLM_CONCURRENCY_LIMIT>={_MIN_CONCURRENCY_FOR_PARALLEL} to enable."
            )
            enable_episode_routing = True  # force fallback

    # ============================================================
    # Fast path: when routing is disabled + concurrency is sufficient,
    # skip ALL LLM calls in the routing phase (entity extraction + routing decision).
    # Each doc gets its own new Episode. Entities are extracted later.
    # ============================================================
    if not enable_episode_routing:
        logger.info(
            f"[episodic][routing] Fast path: routing disabled, "
            f"creating {len(by_doc)} independent episodes (no routing LLM calls)"
        )
        for doc_id, doc_summaries_raw in by_doc.items():
            doc_summaries_sorted = sorted(doc_summaries_raw, key=lambda x: getattr(x.made_from, "chunk_index", 0))
            first_chunk = doc_summaries_sorted[0].made_from
            doc = getattr(first_chunk, "is_part_of", None)
            doc_title = str(getattr(doc, "name", None) or getattr(doc, "title", None) or "Document")

            episode_id_str = str(generate_node_id(f"Episode:{doc_id}"))

            by_episode.setdefault(episode_id_str, []).extend(doc_summaries_sorted)
            episode_doc_titles.setdefault(episode_id_str, []).append(doc_title)
            routing_decisions[episode_id_str] = "disabled"
            episode_source_events.setdefault(episode_id_str, []).append(doc_id)
            # doc_entity_cache intentionally left empty → LLM fallback will handle

        # Calculate episode_memory_types using shared helper
        for episode_id, source_events in episode_source_events.items():
            all_atomic = _is_all_atomic_events(source_events, _event_routing_types)
            episode_memory_types[episode_id] = "atomic" if all_atomic else "episodic"

        return RoutingResult(
            by_episode=by_episode,
            episode_doc_titles=episode_doc_titles,
            doc_entity_cache=doc_entity_cache,
            original_event_routing_types=event_routing_types or {},
            routing_decisions=routing_decisions,
            episode_memory_types=episode_memory_types,
            episode_source_events=episode_source_events,
        )

    # ============================================================
    # Standard path: routing enabled — PARALLEL entity extraction + routing
    # v1.3 Optimization: Entity extraction and routing run CONCURRENTLY
    # ============================================================

    _routing_phase_start = time.time()

    # Get global semaphore for LLM calls (shared by entity extraction and routing)
    _llm_semaphore = get_global_llm_semaphore()

    # ============================================================
    # Step 0: Preprocess - Extract shared data (no LLM calls)
    # This avoids duplicate computation in parallel tasks
    # Tuple: (doc_title, chunk_summaries, doc_summaries_sorted, is_single_event)
    # ============================================================
    doc_meta: Dict[str, Tuple[str, List[str], List["FragmentDigest"], bool]] = {}
    for doc_id, doc_summaries_raw in by_doc.items():
        # Sort for determinism
        doc_summaries_sorted = sorted(doc_summaries_raw, key=lambda x: getattr(x.made_from, "chunk_index", 0))

        first_chunk = doc_summaries_sorted[0].made_from
        doc = getattr(first_chunk, "is_part_of", None)

        # Sentence-level mode: doc_id is actually event_id (precomputed once)
        is_single_event = doc_id.startswith("evt_") or doc_id.startswith("atomic_")

        # Get doc_title (use extracted helper function to reduce nesting)
        doc_title = ""
        if is_single_event:
            doc_title = _extract_event_topic(doc_id, doc_summaries_sorted)

        if not doc_title:
            doc_title = str(getattr(doc, "name", None) or getattr(doc, "title", None) or "Document")

        # Prepare chunk summaries for routing
        chunk_summaries_for_routing = _extract_chunk_summaries_from_text_summaries(
            doc_summaries_sorted,
            max_items=max_chunk_summaries_in_prompt,
            target_event_id=doc_id if is_single_event else None,
        )

        doc_meta[doc_id] = (doc_title, chunk_summaries_for_routing, doc_summaries_sorted, is_single_event)

    # ============================================================
    # Define INDEPENDENT Entity Extraction Task
    # ============================================================
    async def _extract_entities_task(doc_id: str) -> Tuple[str, List[str]]:
        """Extract entities for a single document (uses semaphore)."""
        if not enable_llm_entity_for_routing:
            return (doc_id, [])  # Skip if disabled

        _, _, doc_summaries_sorted, is_single_event = doc_meta[doc_id]

        # Prepare text segments
        text_segments: List[str] = []

        if is_single_event:
            # V2 mode: Extract ONLY sentences belonging to this event_id
            for ts in doc_summaries_sorted:
                chunk = ts.made_from
                classifications = getattr(chunk, "metadata", {}).get("sentence_classifications", [])
                for c in classifications:
                    if c.get("event_id") == doc_id:
                        text = c.get("text", "").strip()
                        if text:
                            text_segments.append(text)
        else:
            # V1 mode: Use all sections from the document
            if _has_valid_sections(doc_summaries_sorted):
                for ts in doc_summaries_sorted:
                    sections = getattr(ts, "sections", None) or []
                    for sec in sections:
                        content = (sec.text or "").strip()
                        if content:
                            text_segments.append(content)
            else:
                _, chunk_summaries, _, _ = doc_meta[doc_id]
                text_segments = [s for s in chunk_summaries if s.strip()]

        # Fallback to full text
        if not text_segments:
            for ts in doc_summaries_sorted:
                text = getattr(ts, "text", "") or ""
                if text.strip():
                    text_segments.append(text)

        if not text_segments:
            return (doc_id, [])

        # Merge all segments into one LLM call
        combined_text = "\n\n".join(text_segments)

        logger.debug(
            f"[routing] Entity extraction for {doc_id[:20]}...: "
            f"{len(text_segments)} segments → {len(combined_text)} chars"
        )

        # Single LLM call with semaphore
        async with _llm_semaphore:
            try:
                result = await _llm_extract_entity_names(text=combined_text, batch_index=0)
                all_names = result.names or []
            except Exception as e:
                logger.warning(f"[routing] Entity extraction failed for {doc_id[:20]}: {e}")
                return (doc_id, [])

        # Deduplicate
        seen: set = set()
        top_names: List[str] = []
        for name in all_names:
            name_clean = _nfkc(name)
            if name_clean and name_clean not in seen:
                seen.add(name_clean)
                top_names.append(name_clean)

        if max_entities_per_episode > 0:
            top_names = top_names[:max_entities_per_episode]

        return (doc_id, top_names)

    # ============================================================
    # Define INDEPENDENT Routing Task (no entity dependency)
    # ============================================================
    async def _route_doc_task(doc_id: str) -> Tuple[str, str, str, str, List["FragmentDigest"]]:
        """Route a single document (no entity dependency for parallel execution)."""
        doc_title, chunk_summaries, doc_summaries_sorted, is_single_event = doc_meta[doc_id]
        default_episode_id = str(generate_node_id(f"Episode:{doc_id}"))

        try:
            # Note: entity parameters are deprecated and ignored in route_episode_id_for_doc
            chosen_episode_id, router_dbg = await route_episode_id_for_doc(
                doc_title=doc_title,
                chunk_summaries=chunk_summaries,
                default_episode_id=default_episode_id,
                graph_engine=graph_engine,
                vector_engine=vector_engine,
                is_single_event=is_single_event,
                target_nodeset_id=target_nodeset_id,  # Dataset isolation (graph level)
                target_dataset_id=target_dataset_id,  # Dataset isolation (vector filter)
            )
        except Exception as e:
            chosen_episode_id = default_episode_id
            router_dbg = {"reason": "routing_failed", "error": str(e)}

        # Calculate routing decision
        reason = router_dbg.get("reason", "unknown")
        if reason in ("routing_disabled", "routing_failed"):
            decision = "disabled"
        elif reason in ("llm_merge", "heuristic_merge"):
            decision = "existing"
        else:
            decision = "new"

        logger.info(
            f"[routing] doc={doc_id[:20]}... -> episode={chosen_episode_id[:20]}... reason={reason} decision={decision}"
        )

        return (doc_id, chosen_episode_id, decision, doc_title, doc_summaries_sorted)

    # ============================================================
    # Step 1: PARALLEL execution of entity extraction AND routing
    # ============================================================
    logger.info(f"[routing] Parallel phase: {len(by_doc)} docs (entity extraction + routing concurrent)")

    entity_tasks = [_extract_entities_task(doc_id) for doc_id in by_doc]
    routing_tasks = [_route_doc_task(doc_id) for doc_id in by_doc]

    # Execute ALL tasks concurrently
    all_results = await asyncio.gather(
        asyncio.gather(*entity_tasks, return_exceptions=True),
        asyncio.gather(*routing_tasks, return_exceptions=True),
    )
    entity_results, routing_results = all_results

    _parallel_elapsed = time.time() - _routing_phase_start
    logger.info(f"[routing] Parallel phase complete: {_parallel_elapsed:.2f}s")

    # ============================================================
    # Step 2: Serial merge of results (safe, no race conditions)
    # ============================================================

    # 2a. Process entity extraction results -> doc_entity_cache
    for entity_result in entity_results:
        if isinstance(entity_result, BaseException):
            logger.error(f"[routing] Entity task exception: {entity_result}")
            continue
        # Type assertion: entity_result is Tuple[str, List[str]]
        doc_id, entities = entity_result
        doc_entity_cache[doc_id] = entities.copy()

    # 2b. Process routing results -> by_episode, episode_doc_titles, etc.
    for routing_result in routing_results:
        if isinstance(routing_result, BaseException):
            logger.error(f"[routing] Routing task exception: {routing_result}")
            continue
        if routing_result is None:
            continue

        # Type assertion: routing_result is Tuple[str, str, str, str, List[FragmentDigest]]
        doc_id, chosen_episode_id, decision, doc_title, doc_summaries_sorted = routing_result

        # Merge into shared dictionaries (serial, safe)
        by_episode.setdefault(chosen_episode_id, []).extend(doc_summaries_sorted)
        episode_doc_titles.setdefault(chosen_episode_id, []).append(doc_title)

        # Track routing decision (first decision wins)
        if chosen_episode_id not in routing_decisions:
            routing_decisions[chosen_episode_id] = decision

        # Track source event_id
        episode_source_events.setdefault(chosen_episode_id, []).append(doc_id)

    _total_routing_elapsed = time.time() - _routing_phase_start
    logger.info(f"[routing] Total routing phase: {_total_routing_elapsed:.2f}s (parallel)")

    # Calculate episode_memory_types based on routing decisions and source events
    for episode_id, source_events in episode_source_events.items():
        decision = routing_decisions.get(episode_id, "disabled")

        if decision == "new":
            # For newly created episodes, check if ALL source events are atomic
            all_atomic = _is_all_atomic_events(source_events, _event_routing_types)
            episode_memory_types[episode_id] = "atomic" if all_atomic else "episodic"
        else:
            # For existing episodes (merge) or disabled routing, default to "episodic"
            # The actual memory_type of existing episodes should be preserved (fetched from DB)
            episode_memory_types[episode_id] = "episodic"

    return RoutingResult(
        by_episode=by_episode,
        episode_doc_titles=episode_doc_titles,
        doc_entity_cache=doc_entity_cache,
        original_event_routing_types=event_routing_types or {},
        routing_decisions=routing_decisions,
        episode_memory_types=episode_memory_types,
        episode_source_events=episode_source_events,  # Event-Level Sections
    )


# Export for backward compatibility
__all__ = ["route_documents_to_episodes", "_MIN_CONCURRENCY_FOR_PARALLEL"]
