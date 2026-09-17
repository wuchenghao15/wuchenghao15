# m_flow/memory/episodic/models.py
"""
Stage 5.9+: Episodic Memory LLM Output Schema

Pydantic models for write_episodic_memories task.

Enhancements:
- EpisodicFacetDraft.aliases: 2-5 short aliases for recall fallback
- EpisodicAliasUpdate: alias additions for existing facets
- ConceptContextInfo: entity with context-specific description
- RoutingType: Constants for content routing (episodic/atomic)
- EpisodicSegment: Segment definition for document-internal splitting
- ContentRoutingResult: LLM output schema for content routing
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================
# Content Routing Models (Episodic/Atomic Classification)
# ============================================================


class RoutingType:
    """
    Routing type constants for content classification.

    Use string constants instead of Enum to avoid circular import issues
    when FragmentDigest (in summarization module) needs to reference these values.

    Usage:
        from m_flow.memory.episodic.models import RoutingType
        summary.routing_type = RoutingType.EPISODIC
    """

    EPISODIC = "episodic"
    ATOMIC = "atomic"


class EpisodicSegment(BaseModel):
    """
    A coherent episodic content segment within a document.

    Documents may contain multiple distinct topics that should be stored
    as separate Episodes. Each segment groups related chunks together.
    """

    chunk_indices: List[int] = Field(
        ...,
        description="Indices of chunks belonging to this segment (0-based, must be within range)",
    )
    suggested_topic: str = Field(
        ..., description="Short topic label for this segment (used for Episode routing/naming)"
    )


class ContentRoutingResult(BaseModel):
    """
    LLM output schema for content routing decision.

    Classifies document chunks into:
    - Episodic segments: Coherent content with clear themes
    - Atomic chunks: Isolated, independent content fragments

    Rules:
    - Every chunk index must appear exactly ONCE
    - No index overlap between episodic_segments and atomic_chunk_indices
    - Indices must be within [0, total_chunks-1]
    """

    episodic_segments: List[EpisodicSegment] = Field(
        default_factory=list,
        description="List of episodic segments, each with chunk indices and topic",
    )
    atomic_chunk_indices: List[int] = Field(
        default_factory=list,
        description="Indices of chunks classified as Atomic (isolated, independent)",
    )

    def validate_indices(self, total_chunks: int) -> bool:
        """
        Validate all indices are within range and no duplicates.

        Args:
            total_chunks: Total number of chunks in the document

        Returns:
            True if valid, False otherwise
        """
        all_indices = set()

        # Check episodic segment indices
        for seg in self.episodic_segments:
            for idx in seg.chunk_indices:
                if idx < 0 or idx >= total_chunks:
                    return False
                if idx in all_indices:
                    return False
                all_indices.add(idx)

        # Check atomic indices
        for idx in self.atomic_chunk_indices:
            if idx < 0 or idx >= total_chunks:
                return False
            if idx in all_indices:
                return False
            all_indices.add(idx)

        return True

    def is_complete(self, total_chunks: int) -> bool:
        """
        Check if all chunks are accounted for.

        Args:
            total_chunks: Total number of chunks in the document

        Returns:
            True if all indices covered, False otherwise
        """
        covered = set()
        for seg in self.episodic_segments:
            covered.update(seg.chunk_indices)
        covered.update(self.atomic_chunk_indices)
        return len(covered) == total_chunks


class ConceptContextInfo(BaseModel):
    """
    Entity with its context-specific description in this episode.

    The context_description should explain the entity's role/value in this
    specific episode, NOT a generic definition of the entity.
    """

    name: str = Field(
        ...,
        description="Entity name (must match a CANDIDATE_ENTITIES name).",
    )
    context_description: str = Field(
        ...,
        description="Context-specific description: what this entity means/does in THIS episode. E.g., 'GPT-4o-mini: selected as base LLM for 80% cost reduction and <500ms latency'. NOT a generic definition.",
    )


class EpisodicFacetDraft(BaseModel):
    """
    LLM-generated Facet draft.

    Facet is a detail anchor point for Episode, used for precise positioning.
    - facet_type: Type classification
    - search_text: Short and sharp retrieval anchor
    - aliases: 5-10 aliases for fallback recall
    - description: Longer explanatory text

    NOTE: related_entities has been moved to separate Entity Selection module
    """

    facet_type: str = Field(
        ...,
        description="Facet category: any descriptive label.",
    )
    search_text: str = Field(
        ...,
        description="TOPIC LABEL ONLY (15-50 chars). A short phrase naming the topic. NO facts, NO numbers, NO lists.",
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="1-3 entries: REPHRASE ONLY - alternative phrasings, synonyms, abbreviations. NO data points.",
    )
    description: Optional[str] = Field(
        None,
        description="Dense, complete facts with semicolons. NOTHING may be omitted.",
    )


class EpisodicAliasUpdate(BaseModel):
    """
    Stage 5.9: Alias supplement for existing facets.

    When a new chunk introduces new phrasings for existing facets, LLM can directly propose alias supplements,
    rather than creating a new facet.
    """

    target_facet_search_text: str = Field(
        ...,
        description="Existing facet search_text to update (must match an existing facet).",
    )
    new_aliases: List[str] = Field(
        default_factory=list,
        description="2-5 short aliases to add to the existing facet.",
    )


class EpisodicWriteDraft(BaseModel):
    """
    LLM-generated Episode draft.

    Episode is a coarse-grained memory anchor point, used for information aggregation across multiple ContentFragments.
    - title: Short title
    - signature: Stable short handle
    - summary: Main content summary of Episode (participates in vectorization)
    - facets: Associated Facet list
    - alias_updates: Alias supplements for existing facets
    """

    title: str = Field(
        ...,
        description=(
            "Specific, distinguishing title for the episode. "
            "Must include key entities and concrete subject. "
            "NEVER use broad categories like 'Daily Activities' or 'Work Matters'. "
            "When updating an existing title, encompass the broadened scope while staying specific."
        ),
    )
    signature: str = Field(
        ...,
        description="Stable short handle (can be similar to title but even shorter, like a tag).",
    )
    summary: str = Field(
        ...,
        description="Episode anchor summary. Should be information-dense and capture the key facts, decisions, progress, and constraints.",
    )
    facets: List[EpisodicFacetDraft] = Field(
        default_factory=list,
        description="List of NEW facets extracted from this episode. Do NOT include facets that duplicate or paraphrase existing ones.",
    )
    # Alias updates
    alias_updates: List[EpisodicAliasUpdate] = Field(
        default_factory=list,
        description="Updates to existing facets: when new text introduces new alternative phrasings for existing facets, add them here instead of creating new facets.",
    )


# ============================================================
# Entity Selection Models (separated from Facet generation)
# ============================================================


class FacetConceptMapping(BaseModel):
    """Entity selection for a single facet."""

    facet_search_text: str = Field(
        ...,
        description="The search_text of the facet these entities belong to.",
    )
    entities: List[ConceptContextInfo] = Field(
        default_factory=list,
        description="Selected entities with context-specific descriptions for this facet.",
    )


class ConceptSelectionResult(BaseModel):
    """Result of the entity selection pass."""

    facet_entities: List[FacetConceptMapping] = Field(
        default_factory=list,
        description="Entity selections for each facet.",
    )


# ============================================================
# Route Decision Models (LLM-based episode routing)
# ============================================================


class EpisodeCandidate(BaseModel):
    """A candidate episode for routing decision."""

    episode_id: str = Field(..., description="The unique ID of the candidate episode.")
    episode_name: str = Field(..., description="The name/title of the candidate episode.")
    episode_summary: str = Field(..., description="The summary of the candidate episode (may be truncated).")
    top_facets: List[str] = Field(
        default_factory=list,
        description="Top facet search_texts from this episode (for quick reference).",
    )
    match_signals: str = Field(
        default="",
        description="Brief description of why this candidate was retrieved (e.g., 'summary similarity', 'shared entities').",
    )
    facet_count: int = Field(
        default=0,
        description="Total number of facets in this episode.",
    )


class RouteDecision(BaseModel):
    """
    LLM decision for episode routing.

    Determines whether to create a new episode or merge into an existing one.
    """

    decision: str = Field(
        ...,
        description="Either 'CREATE_NEW' (create a brand new episode) or 'MERGE_TO_EXISTING' (merge into an existing episode).",
    )
    target_episode_id: Optional[str] = Field(
        None,
        description="If decision is 'MERGE_TO_EXISTING', the episode_id to merge into. Must match one of the candidate episode IDs.",
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for the decision (1-3 sentences).",
    )
    # Optional fields from new prompt (backward compatible)
    primary_focus: Optional[str] = Field(
        None,
        description="One sentence describing the bounded semantic focus of the new content.",
    )
    merge_evidence: Optional[List[str]] = Field(
        None,
        description="Evidence supporting MERGE_TO_EXISTING decision.",
    )
    create_evidence: Optional[List[str]] = Field(
        None,
        description="Evidence supporting CREATE_NEW decision.",
    )


# ============================================================
# FacetPoint Extraction Models
# ============================================================


class FacetPointDraft(BaseModel):
    """
    Fine-grained point under a Facet.

    search_text must be a sharp retrieval handle (short, specific, queryable).
    """

    search_text: str = Field(
        ...,
        alias="name",
        description="Short, specific retrieval handle for one distinct fact/claim/detail under the facet.",
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="Optional short rephrasings/synonyms for recall fallback.",
    )
    description: Optional[str] = Field(
        None,
        description="Optional short explanation. This is for RAG expansion, not required.",
    )

    class Config:
        populate_by_name = True


class FacetPointExtractionResult(BaseModel):
    """
    Extraction result for one facet.
    """

    facet_search_text: str = Field(
        ...,
        alias="facet_name",
        description="Echo of the input facet name.",
    )
    points: List[FacetPointDraft] = Field(
        default_factory=list,
        description="FacetPoints extracted from the facet description.",
    )

    class Config:
        populate_by_name = True


# ============================================================
# Entity Description Models (all entities, no selection)
# ============================================================


class ConceptDescription(BaseModel):
    """Single entity with its description and type."""

    name: str = Field(..., description="Entity name (must match input entity name).")
    description: str = Field(
        ...,
        description="Two-part description: 'Definition; Role in this text.'",
    )
    entity_type: str = Field(
        default="Thing",
        description="Entity type category, e.g., 'Person', 'Organization', 'Location', 'Event', 'Product', 'Entity', 'Thing'.",
    )


class ConceptDescriptionResult(BaseModel):
    """Result of entity description writing."""

    descriptions: List[ConceptDescription] = Field(
        default_factory=list,
        description="Descriptions for all input entities.",
    )


# ============================================================
# Entity Name Extraction Models (using extract_entity_names.txt)
# ============================================================


class ConceptNamesResult(BaseModel):
    """Result of entity name extraction from text."""

    names: List[str] = Field(
        default_factory=list,
        description="List of extracted entity names from the text.",
    )


# ============================================================
# Sentence-Level Routing Models
# ============================================================


class SentenceClassification(BaseModel):
    """
    Classification result for a single sentence within a chunk.

    Stored in ContentFragment.metadata["sentence_classifications"].

    This enables fine-grained routing where a single chunk can contain
    both episodic events and atomic sentences.
    """

    sentence_idx: int = Field(
        ...,
        description="Index of the sentence within the chunk (0-based)",
    )
    text: str = Field(
        ...,
        description="Original sentence text",
    )
    routing_type: str = Field(
        ...,
        description="Classification: 'episodic' or 'atomic'",
    )
    event_id: Optional[str] = Field(
        None,
        description="For episodic sentences: ID of the event this sentence belongs to",
    )
    event_topic: Optional[str] = Field(
        None,
        description="For episodic sentences: suggested topic for the event",
    )
    event_focus: Optional[str] = Field(
        None,
        description="For episodic sentences: semantic focus description for the event",
    )


class EventClassification(BaseModel):
    """
    LLM output: a single episodic event grouping related sentences.

    Used in SentenceRoutingResult.events.
    """

    sentence_indices: List[int] = Field(
        ...,
        description="Indices of sentences belonging to this event (0-based)",
    )
    focus: str = Field(
        ...,
        description="One sentence describing the bounded semantic focus of this event.",
    )
    suggested_topic: str = Field(
        ...,
        description=(
            "Specific, distinguishing topic label for this event. "
            "Include key entities, actors, or concrete subjects. "
            "NEVER use broad categories like 'Daily Activities' or 'Work'."
        ),
    )


class SentenceRoutingResult(BaseModel):
    """
    LLM output schema for sentence-level content routing.

    This routing model operates at sentence granularity,
    allowing a single chunk to be split into multiple events and atomic sentences.

    Rules:
    - Every sentence index must appear exactly ONCE
    - No index overlap between events or between events and atomic_indices
    - Indices must be within [0, total_sentences-1]
    """

    events: List[EventClassification] = Field(
        default_factory=list,
        description="List of episodic events, each grouping related sentences",
    )
    atomic_indices: List[int] = Field(
        default_factory=list,
        description="Indices of isolated sentences (atomic content)",
    )

    def validate_indices(self, total_sentences: int) -> bool:
        """
        Validate all sentence indices are within range and no duplicates.

        Args:
            total_sentences: Total number of sentences in the chunk

        Returns:
            True if valid, False otherwise
        """
        all_indices = set()

        # Check event indices
        for event in self.events:
            for idx in event.sentence_indices:
                if idx < 0 or idx >= total_sentences:
                    return False
                if idx in all_indices:
                    return False
                all_indices.add(idx)

        # Check atomic indices
        for idx in self.atomic_indices:
            if idx < 0 or idx >= total_sentences:
                return False
            if idx in all_indices:
                return False
            all_indices.add(idx)

        return True

    def is_complete(self, total_sentences: int) -> bool:
        """
        Check if all sentences are accounted for.

        Args:
            total_sentences: Total number of sentences in the chunk

        Returns:
            True if all indices covered, False otherwise
        """
        covered = set()
        for event in self.events:
            covered.update(event.sentence_indices)
        covered.update(self.atomic_indices)
        return covered == set(range(total_sentences))
