# m_flow/memory/episodic/episode_size_check.py
"""
Episode Size Check & Adaptive Split Mechanism

Post-ingestion safety net to detect and fix overly broad Episodes
(containing multiple unrelated semantic foci).

Key Architecture:
- Section ≡ Facet (one-to-one mapping)
- Split = regroup existing sections/facets (no content regeneration)
- New Episode summary = concatenation of assigned section texts

Usage:
    from m_flow.memory.episodic.episode_size_check import (
        run_episode_size_check,
        EpisodeSizeCheckConfig,
    )

    # Run check with default config
    stats = await run_episode_size_check()

    # Run with custom config
    config = EpisodeSizeCheckConfig(absolute_threshold=25)
    stats = await run_episode_size_check(config)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, Field

from m_flow.shared.logging_utils import get_logger
from m_flow.memory.episodic.env_utils import as_bool_env, as_int_env, as_str_env
from m_flow.adapters.graph import get_graph_provider
from m_flow.adapters.vector import get_vector_provider
from m_flow.shared.llm_concurrency import get_global_llm_semaphore
from m_flow.llm import LLMService
from m_flow.llm.prompts import read_query_prompt
from m_flow.storage.index_memory_nodes import index_memory_nodes
from m_flow.storage.episode_metadata import (
    get_adapted_threshold,
    set_adapted_threshold,
    delete_threshold,
)
from m_flow.context_global_variables import current_dataset_id
from m_flow.core.domain.models.Episode import Episode
from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.core.domain.utils import generate_node_id
from m_flow.memory.episodic.edge_text_generators import (
    make_has_facet_edge_text,
    make_includes_chunk_edge_text,
)
from m_flow.memory.episodic.normalization import truncate

if TYPE_CHECKING:
    pass

logger = get_logger("episodic.size_check")

# ============================================================
# Configuration
# ============================================================


@dataclass
class EpisodeSizeCheckConfig:
    """Episode size check configuration."""

    # Feature toggle
    enabled: bool = True

    # Detection mode: "fixed" (recommended) or "iqr" (legacy, not recommended)
    # - "fixed": Use fixed_threshold as the check threshold (avoids IQR vicious cycle)
    # - "iqr": Use IQR-based dynamic threshold (can lead to threshold inflation)
    detection_mode: str = "fixed"

    # Fixed threshold (used when detection_mode="fixed")
    fixed_threshold: int = 18  # Episodes with facet_count > 18 will be checked

    # Detection thresholds (legacy, used when detection_mode="iqr")
    base_threshold: int = 12  # Default trigger threshold (IQR baseline)
    absolute_threshold: int = 25  # Absolute threshold: must check if exceeded
    max_threshold: int = 50  # Threshold ceiling (prevent adaptive overflow)

    # Statistical parameters (used when detection_mode="iqr")
    min_episodes_for_distribution: int = 5  # Minimum Episodes for distribution detection
    iqr_multiplier: float = 1.5  # IQR outlier coefficient

    # Adaptive increment
    adaptive_increment: int = 5  # Threshold increment when judged reasonable

    # Minimum Episode size for detection (smaller Episodes not checked)
    min_facets_to_check: int = 9

    # LLM configuration
    prompt_file: str = "episode_size_audit.txt"

    # History logging
    history_log_path: str = "logs/episode_split_history.jsonl"


def get_size_check_config() -> EpisodeSizeCheckConfig:
    """
    Get size check configuration from environment variables.

    Environment variable mapping:
        MFLOW_EPISODE_SIZE_CHECK_ENABLED → enabled
        MFLOW_EPISODE_SIZE_CHECK_MODE → detection_mode ("fixed" or "iqr")
        MFLOW_EPISODE_SIZE_CHECK_THRESHOLD → fixed_threshold (default 18)
        MFLOW_EPISODE_SIZE_CHECK_ABSOLUTE → absolute_threshold (default 25)
        MFLOW_EPISODE_SIZE_CHECK_BASE_THRESHOLD → base_threshold (for IQR mode)
        MFLOW_EPISODE_SIZE_CHECK_MAX_THRESHOLD → max_threshold
        MFLOW_EPISODE_SIZE_CHECK_MIN_FACETS → min_facets_to_check
    """
    # Get detection mode (default to "fixed" to avoid IQR vicious cycle)
    detection_mode = as_str_env("MFLOW_EPISODE_SIZE_CHECK_MODE", "fixed")
    if detection_mode not in ("fixed", "iqr"):
        detection_mode = "fixed"  # Fallback to safe mode

    return EpisodeSizeCheckConfig(
        enabled=as_bool_env("MFLOW_EPISODE_SIZE_CHECK_ENABLED", True),
        detection_mode=detection_mode,
        fixed_threshold=as_int_env("MFLOW_EPISODE_SIZE_CHECK_THRESHOLD", 18),
        base_threshold=as_int_env("MFLOW_EPISODE_SIZE_CHECK_BASE_THRESHOLD", 12),
        absolute_threshold=as_int_env("MFLOW_EPISODE_SIZE_CHECK_ABSOLUTE", 25),
        max_threshold=as_int_env("MFLOW_EPISODE_SIZE_CHECK_MAX_THRESHOLD", 50),
        min_facets_to_check=as_int_env("MFLOW_EPISODE_SIZE_CHECK_MIN_FACETS", 9),
    )


# ============================================================
# Data Models
# ============================================================


@dataclass
class EpisodeStats:
    """Episode statistics for size checking."""

    episode_id: str
    episode_name: str
    facet_count: int
    current_threshold: int  # Episode's current trigger threshold (may have been raised)
    user_id: Optional[str] = None
    space_id: Optional[str] = None


class SplitSuggestion(BaseModel):
    """LLM's split suggestion for a group of facets."""

    new_episode_name: str = Field(..., description="Specific, distinguishing name for new Episode")
    facet_indices: List[int] = Field(..., description="0-based indices of facets for this Episode")
    rationale: str = Field(..., description="Why these facets belong together")
    # Optional field from new prompt (backward compatible)
    focus: Optional[str] = Field(
        None, description="One sentence describing the bounded semantic focus of this new Episode"
    )


class AuditResult(BaseModel):
    """LLM audit result for an Episode."""

    decision: str = Field(..., description="KEEP or SPLIT")
    reasoning: str = Field(..., description="Brief explanation of decision")
    splits: Optional[List[SplitSuggestion]] = Field(
        default=None, description="Split suggestions, only if decision is SPLIT"
    )
    # Optional field from new prompt (backward compatible)
    episode_focus: Optional[str] = Field(
        None, description="One sentence describing the current semantic focus (for KEEP)"
    )


@dataclass
class SplitHistoryEntry:
    """Split history record for debugging and auditing."""

    timestamp: datetime
    original_episode_id: str
    original_episode_name: str
    original_facet_count: int
    new_episodes: List[Dict[str, Any]]  # [{id, name, facet_count, facet_indices}]
    llm_reasoning: str
    original_summary_preview: Optional[str] = None  # First 500 chars


# ============================================================
# Detection Logic
# ============================================================


async def detect_oversized_episodes(
    config: EpisodeSizeCheckConfig,
    user_id: Optional[str] = None,
    space_id: Optional[str] = None,
) -> List[EpisodeStats]:
    """
    Detect Episodes with abnormally high facet counts.

    Supports two detection modes:
    - "fixed": Use fixed_threshold (recommended, avoids IQR vicious cycle)
    - "iqr": Use IQR-based dynamic threshold (legacy, not recommended)

    Args:
        config: Size check configuration
        user_id: Optional user filter
        space_id: Optional space filter

    Returns:
        List of EpisodeStats for Episodes that need checking
    """
    # 1. Get all Episodes with facet counts
    episodes = await _get_all_episodes_with_facet_count(user_id, space_id)

    if not episodes:
        return []

    # 2. Filter: small Episodes not checked
    candidates = [ep for ep in episodes if ep.facet_count >= config.min_facets_to_check]

    if not candidates:
        return []

    # 3. Calculate threshold based on detection mode
    if config.detection_mode == "fixed":
        # Fixed mode: Simple, predictable, avoids IQR vicious cycle
        base_threshold = config.fixed_threshold
        logger.debug(f"[size_check] Using fixed threshold: {base_threshold}")
    else:
        # IQR mode (legacy): Dynamic threshold based on current distribution
        # WARNING: This can lead to threshold inflation when large Episodes exist
        if len(candidates) < config.min_episodes_for_distribution:
            base_threshold = config.base_threshold
        else:
            counts = [ep.facet_count for ep in candidates]
            q1, q3 = np.percentile(counts, [25, 75])
            iqr = q3 - q1
            base_threshold = max(config.base_threshold, q3 + config.iqr_multiplier * iqr)
        logger.debug(f"[size_check] Using IQR threshold: {base_threshold:.1f}")

    # 4. Filter abnormal Episodes
    oversized = []
    for ep in candidates:
        # Use Episode's personalized threshold (if previously adapted via LLM KEEP decision)
        effective_threshold = max(ep.current_threshold, base_threshold)

        # Trigger condition: exceed effective_threshold OR exceed absolute_threshold
        should_check = ep.facet_count > effective_threshold or ep.facet_count > config.absolute_threshold

        if should_check:
            oversized.append(ep)

    logger.info(
        f"[size_check] Detected {len(oversized)} oversized Episodes "
        f"(mode={config.detection_mode}, threshold={base_threshold:.1f}, absolute={config.absolute_threshold})"
    )

    return oversized


async def _get_all_episodes_with_facet_count(
    user_id: Optional[str] = None,
    space_id: Optional[str] = None,
) -> List[EpisodeStats]:
    """
    Get all Episodes with their facet counts from the graph database.

    Returns:
        List of EpisodeStats with facet counts
    """

    graph_engine = await get_graph_provider()

    # Query to get Episodes with facet counts
    # Use Node table with type property (Kuzu schema)
    # Note: Only query essential fields that exist on all Episode nodes
    query = """
    MATCH (ep:Node {type: "Episode"})
    OPTIONAL MATCH (ep)-[r:EDGE]->(f:Node {type: "Facet"})
    WHERE r.relationship_name = "has_facet"
    WITH ep, count(f) as facet_count
    RETURN ep.id as episode_id, 
           ep.name as episode_name, 
           facet_count
    """

    try:
        results = await graph_engine.query(query)
    except Exception as e:
        logger.warning(f"[size_check] Failed to query Episodes: {e}")
        return []

    episodes = []
    for row in results:
        # Handle different result formats
        # Note: Only essential fields are queried (id, name, facet_count)
        if isinstance(row, dict):
            ep_id = row.get("episode_id")
            ep_name = row.get("episode_name", "")
            fc = row.get("facet_count", 0)
        else:
            # Tuple format: (episode_id, episode_name, facet_count)
            ep_id, ep_name, fc = row[0], row[1], row[2]

        # Note: user_id/space_id filtering not supported in current schema
        # All Episodes are included

        # Get persisted threshold from SQLite (Phase 1 enhancement)
        persisted_threshold = get_adapted_threshold(ep_id) or 0

        episodes.append(
            EpisodeStats(
                episode_id=ep_id,
                episode_name=ep_name or "",
                facet_count=fc or 0,
                current_threshold=persisted_threshold,  # Now using persisted value
                user_id=None,
                space_id=None,
            )
        )

    return episodes


# ============================================================
# Audit Logic
# ============================================================


async def audit_episode(
    episode: EpisodeStats,
    facets: List[Any],  # List of Facet objects
    config: EpisodeSizeCheckConfig,
    max_retries: int = 1,
) -> AuditResult:
    """
    LLM audit for a single Episode.

    Uses global LLM semaphore to ensure consistent concurrency control
    with existing episodic/procedural flows.

    Args:
        episode: Episode statistics
        facets: List of Facet objects belonging to this Episode
        config: Size check configuration
        max_retries: Maximum number of retries on validation failure (default: 1)

    Returns:
        AuditResult with decision (KEEP/SPLIT) and optional splits
    """

    # 1. Build facet list text (show full search_text, truncate description to 150 chars)
    facet_list = "\n".join(
        [f"  [{i}]: {_get_facet_search_text(f)} → {_get_facet_description(f)[:150]}..." for i, f in enumerate(facets)]
    )

    # 2. Load and fill prompt
    prompt_template = read_query_prompt(config.prompt_file)
    prompt = prompt_template.format(
        episode_name=episode.episode_name,
        facet_count=episode.facet_count,
        facet_list=facet_list,
        max_facet_index=len(facets) - 1,
    )

    # 3. Get global LLM semaphore (shared with episodic/procedural flows)
    semaphore = get_global_llm_semaphore()

    # 4. Call LLM with retry logic
    last_error: Optional[str] = None

    for attempt in range(max_retries + 1):
        # Call LLM under semaphore protection
        async with semaphore:
            try:
                response = await LLMService.extract_structured(
                    text_input=prompt,
                    system_prompt="You are an expert at analyzing memory organization structure.",
                    response_model=AuditResult,
                )
            except Exception as e:
                # JSON parse failure or other error
                last_error = str(e)
                if attempt < max_retries:
                    logger.info(
                        f"[size_check] LLM audit failed for {episode.episode_name}: {e}, "
                        f"retrying ({attempt + 1}/{max_retries})"
                    )
                    continue
                else:
                    logger.warning(
                        f"[size_check] LLM audit failed for {episode.episode_name}: {e}, "
                        "defaulting to KEEP after retries exhausted"
                    )
                    return AuditResult(decision="KEEP", reasoning=f"LLM error: {str(e)}")

        # 5. Validate split suggestions
        if response.decision == "SPLIT" and response.splits:
            try:
                response.splits = validate_splits(response.splits, len(facets))
                # Validation passed, return response
                if attempt > 0:
                    logger.info(f"[size_check] Retry succeeded for {episode.episode_name} on attempt {attempt + 1}")
                return response
            except ValueError as e:
                last_error = str(e)
                if attempt < max_retries:
                    logger.info(
                        f"[size_check] Invalid split suggestion for {episode.episode_name}: {e}, "
                        f"retrying ({attempt + 1}/{max_retries})"
                    )
                    continue
                else:
                    logger.warning(
                        f"[size_check] Invalid split suggestion for {episode.episode_name}: {e}, "
                        "defaulting to KEEP after retries exhausted"
                    )
                    return AuditResult(
                        decision="KEEP",
                        reasoning=f"Invalid split suggestion after {max_retries + 1} attempts: {str(e)}",
                    )
        else:
            # KEEP decision or no splits needed, no validation required
            return response

    # Fallback (should not reach here)
    return AuditResult(decision="KEEP", reasoning=f"Unexpected error: {last_error}")


def _get_facet_search_text(facet: Any) -> str:
    """Get name/search_text from a Facet object or dict."""
    # Handle dict (from Kuzu query) first
    if isinstance(facet, dict):
        return facet.get("name", facet.get("search_text", ""))
    # Kuzu schema uses 'name' field
    if hasattr(facet, "name"):
        return facet.name or ""
    if hasattr(facet, "search_text"):
        return facet.search_text or ""
    if hasattr(facet, "attributes"):
        return facet.attributes.get("name", facet.attributes.get("search_text", ""))
    return ""


def _get_facet_description(facet: Any) -> str:
    """Get description from a Facet object or dict (may be in 'properties' JSON)."""
    # Handle dict (from Kuzu query) first
    if isinstance(facet, dict):
        # Try direct description first
        if facet.get("description"):
            return facet.get("description", "")
        # Try properties JSON
        props = facet.get("properties")
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except (json.JSONDecodeError, TypeError):
                return ""
        if isinstance(props, dict):
            return props.get("description", "")
        return ""
    # Try direct attribute
    if hasattr(facet, "description"):
        return facet.description or ""
    # Try properties JSON
    if hasattr(facet, "properties"):
        props = facet.properties
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except (json.JSONDecodeError, TypeError):
                return ""
        if isinstance(props, dict):
            return props.get("description", "")
    if hasattr(facet, "attributes"):
        return facet.attributes.get("description", "")
    return ""


def _get_facet_type(facet: Any) -> str:
    """Get facet_type from a Facet object or dict."""
    # Handle dict (from Kuzu query) first
    if isinstance(facet, dict):
        return facet.get("facet_type", "")
    if hasattr(facet, "facet_type"):
        return facet.facet_type or ""
    if hasattr(facet, "attributes"):
        return facet.attributes.get("facet_type", "")
    return ""


def validate_splits(
    splits: List[SplitSuggestion],
    total_facets: int,
) -> List[SplitSuggestion]:
    """
    Validate split suggestions for correctness.

    Checks:
    - Index bounds
    - No duplicate indices
    - All facets assigned

    Args:
        splits: List of split suggestions from LLM
        total_facets: Total number of facets in the Episode

    Returns:
        Validated splits

    Raises:
        ValueError: If validation fails
    """
    # Check index bounds
    for s in splits:
        if any(idx < 0 or idx >= total_facets for idx in s.facet_indices):
            raise ValueError(f"Invalid facet index in split: {s.facet_indices}")

    # Check no duplicate indices
    all_indices = [idx for s in splits for idx in s.facet_indices]
    if len(all_indices) != len(set(all_indices)):
        raise ValueError("Duplicate facet indices across splits")

    # Check all facets assigned
    if set(all_indices) != set(range(total_facets)):
        raise ValueError(f"Not all facets assigned: expected {total_facets}, got {len(all_indices)}")

    return splits


# ============================================================
# Split Execution
# ============================================================


async def execute_split(
    original_episode_id: str,
    splits: List[SplitSuggestion],
    llm_reasoning: str,
) -> List[str]:
    """
    Execute Episode split (leveraging Section≡Facet architecture).

    Key: No content regeneration needed, just regroup existing sections.

    Args:
        original_episode_id: ID of Episode to split
        splits: List of split suggestions
        llm_reasoning: LLM's decision reasoning (for history log)

    Returns:
        List of new Episode IDs
    """

    await get_graph_provider()

    # 1. Get all facets for original Episode (maintain order)
    facets = await _get_episode_facets_ordered(original_episode_id)

    # 2. Get original Episode metadata
    original_episode = await _get_episode_by_id(original_episode_id)

    if not original_episode:
        raise ValueError(f"Episode not found: {original_episode_id}")

    new_episode_ids = []
    new_episode_objects = []  # Collect Episode objects for vector indexing

    # 3. Execute split within transaction
    try:
        for split in splits:
            # Get assigned facets
            assigned_facets = [facets[i] for i in split.facet_indices]

            # New Episode summary = section text concatenation
            # Section format: 【heading】text
            # Facet: search_text = heading, description = text
            new_summary = " ".join(
                [f"【{_get_facet_search_text(f)}】{_get_facet_description(f)}" for f in assigned_facets]
            )

            # Time field migration (safe null handling)
            # Aggregate from all assigned Facets
            time_starts = [_get_facet_time_start(f) for f in assigned_facets if _get_facet_time_start(f) is not None]
            time_ends = [_get_facet_time_end(f) for f in assigned_facets if _get_facet_time_end(f) is not None]
            time_confidences = [
                _get_facet_time_confidence(f) for f in assigned_facets if _get_facet_time_confidence(f) is not None
            ]
            time_texts = [_get_facet_time_text(f) for f in assigned_facets if _get_facet_time_text(f) is not None]

            new_time_start = min(time_starts) if time_starts else None
            new_time_end = max(time_ends) if time_ends else None
            # Use average confidence if multiple facets have time
            new_time_confidence = sum(time_confidences) / len(time_confidences) if time_confidences else None
            # Concatenate time texts for evidence
            new_time_text = "; ".join(time_texts) if time_texts else None

            # Inherit dataset_id from original Episode for proper isolation
            # dataset_id may be a direct attribute or in properties JSON
            original_dataset_id = original_episode.get("dataset_id")
            if not original_dataset_id:
                props = original_episode.get("properties", {})
                if isinstance(props, str):
                    import json as _json

                    try:
                        props = _json.loads(props)
                    except (ValueError, TypeError):
                        props = {}
                original_dataset_id = props.get("dataset_id")

            # Create new Episode node with all required fields
            new_ep_id, new_episode_obj = await _create_episode(
                name=split.new_episode_name,
                summary=new_summary,
                mentioned_time_start_ms=new_time_start,  # Already in ms format
                mentioned_time_end_ms=new_time_end,  # Already in ms format
                mentioned_time_confidence=new_time_confidence,  # Aggregated from Facets
                mentioned_time_text=new_time_text,  # Concatenated from Facets
                user_id=original_episode.get("user_id"),
                space_id=original_episode.get("space_id"),
                dataset_id=original_dataset_id,  # Inherit from original Episode
            )

            # Update facet → Episode relationships (pass full facet for edge_text generation)
            for f in assigned_facets:
                await _move_facet_to_episode(f, new_ep_id)

            # Create Episode → Entity edges based on Facet → Entity relationships
            # This ensures the new Episode has proper entity associations for retrieval
            await _create_episode_entity_edges(new_ep_id, assigned_facets)

            # Migrate includes_chunk edges from Facet's supported_by relationships
            # This ensures the new Episode can trace back to source ContentFragments
            await _migrate_includes_chunk_edges(new_ep_id, assigned_facets)

            new_episode_ids.append(new_ep_id)
            new_episode_objects.append(new_episode_obj)

        # 4. Vector indexing for new Episodes (CRITICAL for retrieval!)
        if new_episode_objects:
            try:
                await index_memory_nodes(new_episode_objects)
                logger.info(f"[size_check] Vector indexed {len(new_episode_objects)} new Episodes")
            except Exception as e:
                logger.warning(
                    f"[size_check] Vector indexing failed: {e}. "
                    "Graph structure is intact, but vector search may not find new Episodes."
                )

        # 5. Delete original Episode's vector index entry
        try:
            vector_engine = get_vector_provider()
            await vector_engine.delete_memory_nodes(
                collection_name="Episode_summary",
                memory_node_ids=[original_episode_id],
            )
            logger.info(f"[size_check] Deleted vector index for original Episode {original_episode_id}")
        except Exception as e:
            logger.warning(f"[size_check] Could not delete vector index for original Episode: {e}")

        # 6. Delete original Episode (facets already point to new Episodes)
        await _delete_episode(original_episode_id)

        # 7. Delete original Episode's threshold record from SQLite
        # (After _delete_episode to ensure data consistency - if Episode deletion fails,
        # threshold record is preserved for potential retry)
        delete_threshold(original_episode_id)

    except Exception as e:
        logger.error(f"[size_check] Split execution failed: {e}")
        raise

    # 4. Log split history (outside transaction, non-blocking)
    try:
        history_entry = SplitHistoryEntry(
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            original_episode_id=original_episode_id,
            original_episode_name=original_episode.get("name", ""),
            original_facet_count=len(facets),
            new_episodes=[
                {
                    "id": new_ep_id,
                    "name": split.new_episode_name,
                    "facet_count": len(split.facet_indices),
                    "facet_indices": split.facet_indices,
                }
                for new_ep_id, split in zip(new_episode_ids, splits, strict=True)
            ],
            llm_reasoning=llm_reasoning,
            original_summary_preview=(
                original_episode.get("summary", "")[:500] if original_episode.get("summary") else None
            ),
        )
        await _log_split_history(history_entry)
    except Exception as e:
        logger.warning(f"[size_check] Failed to log split history: {e}")

    logger.info(f"[size_check] Split Episode '{original_episode.get('name')}' into {len(new_episode_ids)} new Episodes")

    return new_episode_ids


async def _get_episode_facets_ordered(episode_id: str) -> List[Any]:
    """Get facets for an Episode in consistent order."""

    graph_engine = await get_graph_provider()

    query = """
    MATCH (ep:Node {type: "Episode", id: $episode_id})-[r:EDGE]->(f:Node {type: "Facet"})
    WHERE r.relationship_name = "has_facet"
    RETURN f
    ORDER BY f.id
    """

    results = await graph_engine.query(query, {"episode_id": episode_id})
    return [r["f"] if isinstance(r, dict) else r[0] for r in results]


async def _get_episode_by_id(episode_id: str) -> Optional[Dict[str, Any]]:
    """Get Episode by ID."""

    graph_engine = await get_graph_provider()

    query = """
    MATCH (ep:Node {type: "Episode", id: $episode_id})
    RETURN ep
    """

    results = await graph_engine.query(query, {"episode_id": episode_id})
    if not results:
        return None

    row = results[0]
    ep = row["ep"] if isinstance(row, dict) else row[0]

    # Convert to dict
    if hasattr(ep, "attributes"):
        return ep.attributes
    return dict(ep) if ep else None


async def _create_episode(
    name: str,
    summary: str,
    mentioned_time_start_ms: Optional[int] = None,
    mentioned_time_end_ms: Optional[int] = None,
    mentioned_time_confidence: Optional[float] = None,
    mentioned_time_text: Optional[str] = None,
    user_id: Optional[str] = None,
    space_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
) -> Tuple[str, Any]:
    """Create a new Episode node using graph engine API.

    Ensures the Episode has all required fields aligned with original ingestion:
    - memory_spaces: Points to Episodic MemorySpace
    - memory_type: Set to "episodic"
    - mentioned_time_start_ms/end_ms: Millisecond timestamps
    - mentioned_time_confidence/text: Time metadata
    - dataset_id: Dataset isolation for Episode Routing

    Returns:
        Tuple of (episode_id, Episode object) for subsequent vector indexing
    """

    graph_engine = await get_graph_provider()

    ep_id = str(uuid.uuid4())

    # Get or create Episodic MemorySpace (deterministic ID)
    episodic_nodeset = MemorySpace(
        id=generate_node_id("MemorySpace:Episodic"),
        name="Episodic",
    )

    # Get dataset_id from ContextVar if not provided
    effective_dataset_id = dataset_id
    if effective_dataset_id is None:
        effective_dataset_id = current_dataset_id.get()

    # Create Episode using domain model with ALL required fields
    episode = Episode(
        id=ep_id,
        name=name,
        summary=summary or "",
        status="open",
        memory_type="episodic",  # Important: mark as episodic memory
        memory_spaces=[episodic_nodeset],  # Required for nodeset filtering
        dataset_id=effective_dataset_id,  # Dataset isolation for Episode Routing
        # Time fields (use correct field names with _ms suffix)
        mentioned_time_start_ms=mentioned_time_start_ms,
        mentioned_time_end_ms=mentioned_time_end_ms,
        mentioned_time_confidence=mentioned_time_confidence,
        mentioned_time_text=mentioned_time_text,
    )

    await graph_engine.add_nodes([episode])

    return ep_id, episode


async def _move_facet_to_episode(facet: Any, new_episode_id: str) -> None:
    """Move a facet to a new Episode (delete old edge, create new edge).

    Args:
        facet: Complete Facet object (to extract edge_text properties)
        new_episode_id: Target Episode ID
    """

    graph_engine = await get_graph_provider()
    facet_id = _get_facet_id(facet)

    # Delete old edge using query
    query_delete = """
    MATCH (ep:Node {type: "Episode"})-[r:EDGE]->(f:Node {type: "Facet", id: $facet_id})
    WHERE r.relationship_name = "has_facet"
    DELETE r
    """
    await graph_engine.query(query_delete, {"facet_id": facet_id})

    # Generate edge_text (critical for vector search!)
    facet_type = _get_facet_type(facet)
    facet_search_text = _get_facet_search_text(facet)
    facet_description = _get_facet_description(facet)
    edge_text = make_has_facet_edge_text(
        facet_type=facet_type,
        facet_search_text=facet_search_text,
        facet_description=facet_description,
    )

    # Create new edge using graph engine API with proper edge_text
    # add_edges expects: List[Tuple[source_id, target_id, relationship_name, properties_dict]]
    edge_tuple = (
        new_episode_id,  # source: Episode
        facet_id,  # target: Facet
        "has_facet",  # relationship_name
        {
            "edge_text": edge_text,
            "relationship_type": "has_facet",
        },
    )
    await graph_engine.add_edges([edge_tuple])


async def _delete_episode(episode_id: str) -> None:
    """Delete an Episode node."""

    graph_engine = await get_graph_provider()

    query = """
    MATCH (ep:Node {type: "Episode", id: $episode_id})
    DETACH DELETE ep
    """
    await graph_engine.query(query, {"episode_id": episode_id})


async def _migrate_includes_chunk_edges(
    new_episode_id: str,
    facets: List[Any],
) -> None:
    """
    Migrate includes_chunk edges to new Episode based on Facet supported_by relationships.

    When an Episode is split, the new Episode should have includes_chunk edges
    to the ContentFragments that support its Facets.

    Strategy:
    1. Query supported_by edges from the assigned Facets
    2. Get unique ContentFragment IDs
    3. Create includes_chunk edges from new Episode to those ContentFragments

    Args:
        new_episode_id: New Episode ID
        facets: List of Facet objects assigned to this Episode
    """

    graph_engine = await get_graph_provider()

    # Get facet IDs
    facet_ids = [_get_facet_id(f) for f in facets if _get_facet_id(f)]

    if not facet_ids:
        return

    # Query supported_by edges to get related ContentFragment IDs
    # Facet → ContentFragment via supported_by relationship
    # Note: chunk_index is stored in properties JSON, not as top-level attribute
    query = """
    MATCH (f:Node {type: "Facet"})-[r:EDGE]->(c:Node {type: "ContentFragment"})
    WHERE f.id IN $facet_ids AND r.relationship_name = 'supported_by'
    RETURN DISTINCT c.id as chunk_id, c.properties as chunk_props
    """

    try:
        results = await graph_engine.query(query, {"facet_ids": facet_ids})
    except Exception as e:
        logger.warning(f"[size_check] Failed to query Facet→ContentFragment: {e}")
        return

    if not results:
        logger.debug(f"[size_check] No ContentFragments found for facets: {facet_ids}")
        return

    # Create includes_chunk edges
    edges_to_create = []

    for row in results:
        if isinstance(row, dict):
            chunk_id = row.get("chunk_id")
            chunk_props = row.get("chunk_props")
        else:
            chunk_id = row[0]
            chunk_props = row[1] if len(row) > 1 else None

        # Extract chunk_index from properties JSON
        chunk_index = -1
        if chunk_props:
            if isinstance(chunk_props, str):
                try:
                    props = json.loads(chunk_props)
                    chunk_index = props.get("chunk_index", -1)
                except (json.JSONDecodeError, TypeError):
                    logger.debug("[size_check] Failed to parse chunk_props JSON")
            elif isinstance(chunk_props, dict):
                chunk_index = chunk_props.get("chunk_index", -1)

        if not chunk_id:
            continue

        # Generate edge_text
        edge_text = make_includes_chunk_edge_text(
            chunk_id=str(chunk_id),
            chunk_index=int(chunk_index) if chunk_index is not None else -1,
        )

        edge_tuple = (
            new_episode_id,  # source: Episode
            chunk_id,  # target: ContentFragment
            "includes_chunk",
            {
                "edge_text": edge_text,
                "relationship_type": "includes_chunk",
            },
        )
        edges_to_create.append(edge_tuple)

    if edges_to_create:
        try:
            await graph_engine.add_edges(edges_to_create)
            logger.debug(
                f"[size_check] Migrated {len(edges_to_create)} includes_chunk edges to Episode {new_episode_id}"
            )
        except Exception as e:
            logger.warning(f"[size_check] Failed to create includes_chunk edges: {e}")


async def _create_episode_entity_edges(
    episode_id: str,
    facets: List[Any],
) -> None:
    """
    Create Episode → Entity edges based on the entities in the assigned Facets.

    When splitting an Episode, the new Episode needs its own involves_entity edges.
    We derive these from the Facet → Entity edges of the assigned Facets.

    Args:
        episode_id: New Episode ID
        facets: List of Facet objects assigned to this Episode
    """

    graph_engine = await get_graph_provider()

    # Collect unique entities from all facets
    facet_ids = [_get_facet_id(f) for f in facets if _get_facet_id(f)]

    if not facet_ids:
        return

    # Query all entities connected to these facets
    # Note: Entity nodes store description in 'properties' JSON, not as direct property
    query = """
    MATCH (f:Node {type: "Facet"})-[r:EDGE]->(e:Node {type: "Entity"})
    WHERE f.id IN $facet_ids AND r.relationship_name = 'involves_entity'
    RETURN DISTINCT e.id as entity_id, e.name as entity_name, e.properties as entity_props
    """

    try:
        results = await graph_engine.query(query, {"facet_ids": facet_ids})
    except Exception as e:
        logger.warning(f"[size_check] Failed to query facet entities: {e}")
        return

    if not results:
        logger.debug(f"[size_check] No entities found for facets: {facet_ids}")
        return

    # Create Episode → Entity edges
    edges_to_create = []

    for row in results:
        if isinstance(row, dict):
            entity_id = row.get("entity_id")
            entity_name = row.get("entity_name", "")
            entity_props = row.get("entity_props")
        else:
            entity_id = row[0]
            entity_name = row[1] or ""
            entity_props = row[2]

        # Extract description from properties JSON
        entity_desc = ""
        if entity_props:
            if isinstance(entity_props, str):
                try:
                    props = json.loads(entity_props)
                    entity_desc = props.get("description", "")
                except (json.JSONDecodeError, TypeError):
                    logger.debug("[size_check] Failed to parse entity_props JSON")
            elif isinstance(entity_props, dict):
                entity_desc = entity_props.get("description", "")

        if not entity_id:
            continue

        # Generate edge_text for Episode → Entity edge
        # Format: "entity_name | description" (same as original ingestion)
        truncated_desc = truncate(entity_desc, 200) if entity_desc else ""
        if truncated_desc:
            edge_text = f"{entity_name} | {truncated_desc}"
        else:
            edge_text = entity_name

        edge_tuple = (
            episode_id,  # source: Episode
            entity_id,  # target: Entity (Entity)
            "involves_entity",
            {
                "edge_text": edge_text,
                "relationship_type": "involves_entity",
            },
        )
        edges_to_create.append(edge_tuple)

    if edges_to_create:
        try:
            await graph_engine.add_edges(edges_to_create)
            logger.debug(f"[size_check] Created {len(edges_to_create)} Episode→Entity edges for Episode {episode_id}")
        except Exception as e:
            logger.warning(f"[size_check] Failed to create Episode→Entity edges: {e}")


def _get_facet_id(facet: Any) -> str:
    """Get ID from a Facet object or dict."""
    # Handle dict (from Kuzu query)
    if isinstance(facet, dict):
        return str(facet.get("id", ""))
    # Handle object with id attribute
    if hasattr(facet, "id"):
        return str(facet.id)
    # Handle object with attributes dict
    if hasattr(facet, "attributes"):
        return str(facet.attributes.get("id", ""))
    return ""


def _get_facet_time_start(facet: Any) -> Optional[int]:
    """Get mentioned_time_start_ms from a Facet object or dict (milliseconds)."""
    # Handle dict (from Kuzu query)
    if isinstance(facet, dict):
        return facet.get("mentioned_time_start_ms") or facet.get("mentioned_time_start")
    # Try _ms suffix first (correct field name)
    if hasattr(facet, "mentioned_time_start_ms"):
        return facet.mentioned_time_start_ms
    # Fallback to non-suffix version for compatibility
    if hasattr(facet, "mentioned_time_start"):
        return facet.mentioned_time_start
    if hasattr(facet, "attributes"):
        return facet.attributes.get("mentioned_time_start_ms") or facet.attributes.get("mentioned_time_start")
    return None


def _get_facet_time_end(facet: Any) -> Optional[int]:
    """Get mentioned_time_end_ms from a Facet object or dict (milliseconds)."""
    # Handle dict (from Kuzu query)
    if isinstance(facet, dict):
        return facet.get("mentioned_time_end_ms") or facet.get("mentioned_time_end")
    # Try _ms suffix first (correct field name)
    if hasattr(facet, "mentioned_time_end_ms"):
        return facet.mentioned_time_end_ms
    # Fallback to non-suffix version for compatibility
    if hasattr(facet, "mentioned_time_end"):
        return facet.mentioned_time_end
    if hasattr(facet, "attributes"):
        return facet.attributes.get("mentioned_time_end_ms") or facet.attributes.get("mentioned_time_end")
    return None


def _get_facet_time_confidence(facet: Any) -> Optional[float]:
    """Get mentioned_time_confidence from a Facet object or dict."""
    if isinstance(facet, dict):
        return facet.get("mentioned_time_confidence")
    if hasattr(facet, "mentioned_time_confidence"):
        return facet.mentioned_time_confidence
    if hasattr(facet, "attributes"):
        return facet.attributes.get("mentioned_time_confidence")
    return None


def _get_facet_time_text(facet: Any) -> Optional[str]:
    """Get mentioned_time_text from a Facet object or dict."""
    if isinstance(facet, dict):
        return facet.get("mentioned_time_text")
    if hasattr(facet, "mentioned_time_text"):
        return facet.mentioned_time_text
    if hasattr(facet, "attributes"):
        return facet.attributes.get("mentioned_time_text")
    return None


# ============================================================
# Adaptive Threshold
# ============================================================


async def adapt_threshold(
    episode_id: str,
    current_facet_count: int,
    config: EpisodeSizeCheckConfig,
) -> int:
    """
    Set Episode's trigger threshold when LLM judges it as reasonable.

    Strategy: threshold = current facet count + margin
    This way only significant growth triggers re-check.

    Example:
    - Episode has 35 facets, judged reasonable
    - New threshold = 35 + 5 = 40
    - Next check only if > 40

    The threshold is persisted to SQLite for cross-session retention.
    """
    # Calculate new threshold
    new_threshold = min(
        current_facet_count + config.adaptive_increment,
        config.max_threshold,
    )

    # Persist to SQLite (Phase 1 enhancement)
    success = set_adapted_threshold(episode_id, new_threshold)

    if success:
        logger.info(
            f"[size_check] Adapted threshold for Episode {episode_id}: {new_threshold} "
            f"(current facets: {current_facet_count}) - PERSISTED"
        )
    else:
        logger.warning(
            f"[size_check] Adapted threshold for Episode {episode_id}: {new_threshold} "
            f"(current facets: {current_facet_count}) - PERSISTENCE FAILED"
        )

    return new_threshold


# ============================================================
# History Logging
# ============================================================


async def _log_split_history(entry: SplitHistoryEntry) -> None:
    """Append split history to log file."""
    config = get_size_check_config()
    log_path = Path(config.history_log_path)

    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": entry.timestamp.isoformat(),
        "original_episode_id": entry.original_episode_id,
        "original_episode_name": entry.original_episode_name,
        "original_facet_count": entry.original_facet_count,
        "new_episodes": entry.new_episodes,
        "llm_reasoning": entry.llm_reasoning,
        "original_summary_preview": entry.original_summary_preview,
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ============================================================
# Main Flow
# ============================================================


async def run_episode_size_check(
    config: Optional[EpisodeSizeCheckConfig] = None,
    user_id: Optional[str] = None,
    space_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Episode size check main flow.

    Args:
        config: Optional configuration (uses defaults if not provided)
        user_id: Optional user filter
        space_id: Optional space filter

    Returns:
        {
            "checked": int,      # Number of Episodes checked
            "split": int,        # Number of Episodes split
            "adapted": int,      # Number of Episodes with raised thresholds
            "errors": List[str]  # Error messages
        }
    """
    config = config or get_size_check_config()

    if not config.enabled:
        logger.info("[size_check] Episode size check is disabled")
        return {"checked": 0, "split": 0, "adapted": 0, "errors": []}

    stats = {"checked": 0, "split": 0, "adapted": 0, "errors": []}

    # 1. Detect oversized Episodes
    oversized = await detect_oversized_episodes(config, user_id, space_id)
    stats["checked"] = len(oversized)

    if not oversized:
        logger.info("[size_check] No oversized Episodes detected")
        return stats

    for ep in oversized:
        try:
            # 2. Get facets
            facets = await _get_episode_facets_ordered(ep.episode_id)

            if not facets:
                continue

            # 3. LLM audit
            result = await audit_episode(ep, facets, config)

            if result.decision == "KEEP":
                # 4a. Reasonable → raise threshold
                await adapt_threshold(ep.episode_id, ep.facet_count, config)
                stats["adapted"] += 1
                logger.info(
                    f"[size_check] Episode '{ep.episode_name}' judged reasonable, "
                    f"threshold adapted to {ep.facet_count + config.adaptive_increment}"
                )

            elif result.decision == "SPLIT" and result.splits:
                # 4b. Split → execute
                await execute_split(ep.episode_id, result.splits, result.reasoning)
                stats["split"] += 1

        except Exception as e:
            error_msg = f"Episode {ep.episode_name}: {str(e)}"
            stats["errors"].append(error_msg)
            logger.error(f"[size_check] Error processing Episode: {error_msg}")

    logger.info(
        f"[size_check] Completed: checked={stats['checked']}, "
        f"split={stats['split']}, adapted={stats['adapted']}, "
        f"errors={len(stats['errors'])}"
    )

    return stats


# ============================================================
# Public API
# ============================================================

__all__ = [
    "EpisodeSizeCheckConfig",
    "get_size_check_config",
    "run_episode_size_check",
    "detect_oversized_episodes",
    "audit_episode",
    "execute_split",
    "adapt_threshold",
    "EpisodeStats",
    "SplitSuggestion",
    "AuditResult",
    "SplitHistoryEntry",
    # Exported for maintenance API
    "_get_all_episodes_with_facet_count",
    "_get_episode_facets_ordered",
]
