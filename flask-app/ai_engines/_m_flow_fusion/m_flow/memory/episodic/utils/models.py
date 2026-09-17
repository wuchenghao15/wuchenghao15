# m_flow/memory/episodic/utils/models.py
"""
Data classes for episodic memory writing pipeline.

This module contains data classes used by the episodic memory writing
pipeline for routing results and facet updates.

Extracted as part of large file refactoring (Phase 2).

Classes:
    - RoutingResult: Result of routing documents to Episodes
    - FacetUpdate: Internal facet update tracking record
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from m_flow.knowledge.summarization.models import FragmentDigest


@dataclass
class RoutingResult:
    """
    Routing stage output.

    Result of routing documents to Episodes, containing:
    - by_episode: Episode ID -> FragmentDigest list mapping
    - episode_doc_titles: Episode ID -> document title list mapping
    - doc_entity_cache: Document ID -> Entity name list cache (for Loop 2 to avoid duplicate extraction)
    - original_event_routing_types: Original event_id -> routing_type mapping
    - routing_decisions: episode_id -> routing_decision mapping ("new" | "existing" | "disabled")
    - episode_memory_types: episode_id -> memory_type mapping, used to set Episode.memory_type
    - episode_source_events: episode_id -> [event_id, ...] mapping (for Event-Level Sections)

    Attributes:
        by_episode: Mapping from Episode ID to list of FragmentDigest objects
        episode_doc_titles: Mapping from Episode ID to list of document titles
        doc_entity_cache: Cache of entity names per document (to avoid duplicate extraction)
        original_event_routing_types: Mapping from event_id to routing type ("episodic" or "atomic")
        routing_decisions: Mapping from episode_id to routing decision ("new", "existing", or "disabled")
        episode_memory_types: Mapping from episode_id to memory type
        episode_source_events: Mapping from episode_id to list of source event_ids
    """

    by_episode: Dict[str, List["FragmentDigest"]]
    episode_doc_titles: Dict[str, List[str]]
    doc_entity_cache: Dict[str, List[str]]
    # New: for tracking Episode memory_type
    original_event_routing_types: Dict[str, str] = field(default_factory=dict)  # event_id -> "episodic" | "atomic"
    routing_decisions: Dict[str, str] = field(default_factory=dict)  # episode_id -> "new" | "existing" | "disabled"
    episode_memory_types: Dict[str, str] = field(default_factory=dict)  # episode_id -> "episodic" | "atomic"
    # Event-Level Sections: reverse lookup from episode_id to original event_ids
    episode_source_events: Dict[str, List[str]] = field(default_factory=dict)  # episode_id -> [event_id, ...]


@dataclass
class FacetUpdate:
    """
    Internal facet update tracking record.

    Used to track which facets need to be updated during the episodic
    memory writing process.

    Attributes:
        id: Facet node ID
        facet_type: Type of the facet (e.g., "topic")
        search_text: Search text for the facet
        description: Optional description of the facet
        aliases: List of alias strings for the facet
        touched: Whether this facet was modified in the current batch
        mentioned_time_start_ms: Facet's own time start (independent of Episode)
        mentioned_time_end_ms: Facet's own time end (independent of Episode)
        mentioned_time_confidence: Confidence of the extracted time
        mentioned_time_text: Original time text evidence
    """

    id: str
    facet_type: str
    search_text: str
    description: Optional[str]
    aliases: List[str] = field(default_factory=list)
    touched: bool = False  # Whether this batch needs output writeback
    # Facet's own time fields (independent of Episode time)
    mentioned_time_start_ms: Optional[int] = None
    mentioned_time_end_ms: Optional[int] = None
    mentioned_time_confidence: Optional[float] = None
    mentioned_time_text: Optional[str] = None


# Backwards compatibility alias
_FacetUpdate = FacetUpdate


# ============================================================
# Module exports
# ============================================================

__all__ = [
    "RoutingResult",
    "FacetUpdate",
    "_FacetUpdate",  # Backwards compatibility
]
