"""
M-flow search result schemas.

Contains Pydantic models for representing search API responses
including individual results and combined/aggregated results.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SearchResultDataset(BaseModel):
    """Reference to source dataset."""

    id: UUID = Field(description="Dataset UUID")
    name: str = Field(description="Human-readable dataset name")


class CombinedSearchResult(BaseModel):
    """Aggregated search response with metadata."""

    result: Any | None = Field(default=None, description="Primary search result")
    context: dict[str, Any] = Field(description="Additional context data")
    graphs: dict[str, Any] | None = Field(default_factory=dict, description="Graph visualizations")
    datasets: list[SearchResultDataset] | None = Field(default=None, description="Source datasets")


class SearchResult(BaseModel):
    """Single search result with provenance."""

    search_result: Any = Field(description="The actual result content")
    dataset_id: UUID | None = Field(default=None, description="Source dataset ID")
    dataset_name: str | None = Field(default=None, description="Source dataset name")
