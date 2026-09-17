# m_flow/api/v1/manual/models.py
"""
Manual Ingestion Data Models

Pydantic models for user-defined episodic memory structures.
These models allow users to bypass the LLM extraction pipeline
and directly specify graph node contents for ingestion.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# FacetPoint Input Model
# ============================================================


class ManualFacetPointInput(BaseModel):
    """
    User-defined FacetPoint (fine-grained information point).

    FacetPoint represents a single proposition, fact, or detail
    that can be independently vectorized and retrieved.
    """

    search_text: str = Field(
        ...,
        description="Main retrieval handle. This will be indexed for search.",
        min_length=1,
    )
    aliases: Optional[List[str]] = Field(
        default=None,
        description="Optional synonyms/paraphrases for fallback recall.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional explanatory expansion (for RAG context, not indexed).",
    )
    display_only: Optional[str] = Field(
        default=None,
        description="Display-only content shown when retrieved but NOT indexed. No length limit.",
    )


# ============================================================
# Facet Input Model
# ============================================================


class ManualFacetInput(BaseModel):
    """
    User-defined Facet (detail anchor for Episode).

    Facet is the detail anchor for Episode, used for precise positioning
    in coarse-grained retrieval.
    """

    facet_type: Optional[str] = Field(
        default="chapter",
        description="Facet category: chapter/article/decision/risk/outcome/metric/issue/plan/constraint/cause...",
    )
    search_text: str = Field(
        ...,
        description="Main retrieval handle. This will be indexed for search.",
        min_length=1,
    )
    aliases: Optional[List[str]] = Field(
        default=None,
        description="Optional synonyms/paraphrases for fallback recall.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description (for RAG context expansion).",
    )
    anchor_text: Optional[str] = Field(
        default=None,
        description="Middle-layer rich semantic field (participates in vectorization). Can equal description.",
    )
    display_only: Optional[str] = Field(
        default=None,
        description="Display-only content shown when retrieved but NOT indexed. No length limit.",
    )
    points: Optional[List[ManualFacetPointInput]] = Field(
        default=None,
        description="Fine-grained points under this facet.",
    )


# ============================================================
# Entity/Entity Input Model
# ============================================================


class ManualConceptInput(BaseModel):
    """
    User-defined Entity (entity extracted from content).

    Entity represents an atomic concept (name, person, organization,
    location, tool, number, date, etc.).
    """

    name: str = Field(
        ...,
        description="Entity name as it should appear in the graph.",
        min_length=1,
    )
    description: str = Field(
        ...,
        description="Context-specific description of this entity.",
        min_length=1,
    )
    canonical_name: Optional[str] = Field(
        default=None,
        description="Normalized name for cross-episode matching (lowercase, no spaces).",
    )
    entity_type: Optional[str] = Field(
        default="Thing",
        description="Entity type: Person/Organization/Location/Event/Product/Entity/Thing...",
    )
    display_only: Optional[str] = Field(
        default=None,
        description="Display-only content shown when retrieved but NOT indexed. No length limit.",
    )


# ============================================================
# Episode Input Model
# ============================================================


class ManualEpisodeInput(BaseModel):
    """
    User-defined Episode (coarse-grained memory anchor).

    Episode is the anchor for coarse-grained memory, used for information
    aggregation. It contains facets and involves entities.
    """

    name: str = Field(
        ...,
        description="Short title for the episode (used as node name in graph).",
        min_length=1,
    )
    summary: str = Field(
        ...,
        description="Main content summary of the Episode (participates in vectorization).",
        min_length=1,
    )
    signature: Optional[str] = Field(
        default=None,
        description="Stable short handle for quick identification.",
    )
    status: Optional[str] = Field(
        default="open",
        description="Status marker: open/closed/...",
    )
    memory_type: Optional[str] = Field(
        default="episodic",
        description="Memory type: 'episodic' (event) or 'atomic' (single fact).",
    )
    display_only: Optional[str] = Field(
        default=None,
        description="Display-only content shown when retrieved but NOT indexed. No length limit.",
    )
    facets: Optional[List[ManualFacetInput]] = Field(
        default=None,
        description="Facets associated with this episode.",
    )
    entities: Optional[List[ManualConceptInput]] = Field(
        default=None,
        description="Entities involved in this episode.",
    )


# ============================================================
# Batch Ingestion Request Model
# ============================================================


class ManualIngestRequest(BaseModel):
    """
    Request model for manual episodic memory ingestion.

    Allows users to directly specify one or more Episodes with their
    associated Facets, FacetPoints, and Entities for ingestion.
    """

    episodes: List[ManualEpisodeInput] = Field(
        ...,
        description="List of episodes to ingest.",
        min_length=1,
    )
    dataset_name: str = Field(
        default="main_dataset",
        description="Target dataset name.",
    )
    dataset_id: Optional[UUID] = Field(
        default=None,
        description="Target dataset UUID (overrides dataset_name if provided).",
    )
    embed_triplets: bool = Field(
        default=False,
        description="Whether to create triplet embeddings for edge relationships.",
    )


# ============================================================
# Response Models
# ============================================================


class ManualIngestResult(BaseModel):
    """Result of manual ingestion operation."""

    success: bool = Field(description="Whether the operation succeeded.")
    episodes_created: int = Field(description="Number of episodes created.")
    facets_created: int = Field(description="Number of facets created.")
    facet_points_created: int = Field(description="Number of facet points created.")
    entities_created: int = Field(description="Number of entities created.")
    errors: Optional[List[str]] = Field(
        default=None,
        description="List of error messages if any.",
    )


# ============================================================
# Node Update Models
# ============================================================


class PatchNodeRequest(BaseModel):
    """
    Request model for updating specific node fields.

    Only display_only is currently supported for patching.
    Other fields may be added in the future.
    """

    node_id: UUID = Field(
        ...,
        description="UUID of the node to update.",
    )
    node_type: str = Field(
        ...,
        description="Type of node: Episode/Facet/FacetPoint/Entity.",
    )
    display_only: Optional[str] = Field(
        default=None,
        description="New value for display_only field. Set to empty string to clear.",
    )


class PatchNodeResult(BaseModel):
    """Result of node patch operation."""

    success: bool = Field(description="Whether the operation succeeded.")
    node_id: UUID = Field(description="ID of the updated node.")
    node_type: str = Field(description="Type of the updated node.")
    message: Optional[str] = Field(
        default=None,
        description="Additional message or error details.",
    )
