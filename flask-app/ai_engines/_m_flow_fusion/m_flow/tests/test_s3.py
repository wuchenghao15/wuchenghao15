"""
AWS S3 Integration Tests for M-flow.

Tests document ingestion from S3 bucket sources, verifying
knowledge graph construction and expected node/edge types.
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from typing import TYPE_CHECKING

import m_flow
from m_flow.adapters.graph.get_graph_adapter import get_graph_provider
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger()

# ============================================================================
# Test Configuration
# ============================================================================

S3_TEST_BUCKET = "s3://samples3input"

# Expected minimums for graph validation
MIN_TEXT_DOCUMENTS = 2
MIN_CONTENT_FRAGMENTS = 2
MIN_FRAGMENT_DIGESTS = 2
MIN_CONCEPTS = 1
MIN_CONCEPT_TYPES = 1

MIN_IS_PART_OF_EDGES = 2
MIN_MADE_FROM_EDGES = 2
MIN_IS_A_EDGES = 1
MIN_CONTAINS_EDGES = 1


# ============================================================================
# Validation Helpers
# ============================================================================


def count_nodes_by_type(graph_nodes: list) -> Counter:
    """Build counter of node types from graph data."""
    return Counter(node_data[1].get("type", {}) for node_data in graph_nodes)


def count_edges_by_type(graph_edges: list) -> Counter:
    """Build counter of edge types from graph data."""
    return Counter(edge[2] for edge in graph_edges)


def validate_node_count(
    type_counts: Counter,
    node_type: str,
    min_count: int,
    exact: bool = False,
) -> None:
    """Validate that a node type meets expected count."""
    actual = type_counts.get(node_type, 0)

    if exact:
        assert actual == min_count, f"Expected exactly {min_count} {node_type} nodes, found {actual}"
    else:
        assert actual >= min_count, f"Expected at least {min_count} {node_type} nodes, found {actual}"


def validate_edge_count(
    edge_counts: Counter,
    edge_type: str,
    min_count: int,
) -> None:
    """Validate that an edge type meets expected count."""
    actual = edge_counts.get(edge_type, 0)
    assert actual >= min_count, f"Expected at least {min_count} '{edge_type}' edges, found {actual}"


# ============================================================================
# Test Execution
# ============================================================================


async def run_s3_ingestion_test() -> None:
    """Test S3 document ingestion and knowledge graph construction."""

    # Reset system state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Ingest from S3
    await m_flow.add(S3_TEST_BUCKET)

    # Process documents
    await m_flow.memorize()

    # Retrieve graph data
    graph_engine = await get_graph_provider()
    nodes, edges = await graph_engine.get_graph_data()

    # Analyze graph structure
    node_counts = count_nodes_by_type(nodes)
    edge_counts = count_edges_by_type(edges)

    logging.info(f"Node types: {dict(node_counts)}")
    logging.info(f"Edge types: {dict(edge_counts)}")

    # Validate node types
    validate_node_count(node_counts, "TextDocument", MIN_TEXT_DOCUMENTS, exact=True)
    validate_node_count(node_counts, "ContentFragment", MIN_CONTENT_FRAGMENTS)
    validate_node_count(node_counts, "FragmentDigest", MIN_FRAGMENT_DIGESTS)
    validate_node_count(node_counts, "Entity", MIN_CONCEPTS)
    validate_node_count(node_counts, "EntityType", MIN_CONCEPT_TYPES)

    # Validate edge types
    validate_edge_count(edge_counts, "is_part_of", MIN_IS_PART_OF_EDGES)
    validate_edge_count(edge_counts, "made_from", MIN_MADE_FROM_EDGES)
    validate_edge_count(edge_counts, "is_a", MIN_IS_A_EDGES)
    validate_edge_count(edge_counts, "contains", MIN_CONTAINS_EDGES)

    logger.info("S3 ingestion test passed successfully!")


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    asyncio.run(run_s3_ingestion_test())
