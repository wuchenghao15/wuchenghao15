# m_flow/api/v1/manual/__init__.py
"""
Manual Episodic Memory Ingestion API

This module provides APIs for:
1. Manual ingestion: Directly specify Episode/Facet/FacetPoint/Entity contents
   without using LLM extraction.
2. Node patching: Update display_only field on existing nodes.

Usage:
    from m_flow.api.v1.manual import manual_ingest, patch_node, manual_add_episode

    # Manual ingestion with full control
    result = await manual_ingest(ManualIngestRequest(...))

    # Convenience function for single episode
    result = await manual_add_episode(
        name="Meeting Notes",
        summary="Discussed technical solutions...",
        facets=[{"facet_type": "decision", "search_text": "Adopt Solution A", ...}],
        entities=[{"name": "John", "description": "Tech Lead"}],
    )

    # Update display_only field
    result = await patch_node(PatchNodeRequest(...))
"""

from .manual import manual_ingest, patch_node, manual_add_episode
from .models import (
    ManualEpisodeInput,
    ManualFacetInput,
    ManualFacetPointInput,
    ManualConceptInput,
    ManualIngestRequest,
    ManualIngestResult,
    PatchNodeRequest,
    PatchNodeResult,
)

__all__ = [
    # Core functions
    "manual_ingest",
    "patch_node",
    "manual_add_episode",
    # Input models
    "ManualEpisodeInput",
    "ManualFacetInput",
    "ManualFacetPointInput",
    "ManualConceptInput",
    "ManualIngestRequest",
    # Result models
    "ManualIngestResult",
    "PatchNodeRequest",
    "PatchNodeResult",
]
