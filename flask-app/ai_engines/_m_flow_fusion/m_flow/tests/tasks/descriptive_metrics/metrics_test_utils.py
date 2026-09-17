"""
Graph Metrics Test Utilities for M-flow.

Provides test graph construction helpers and metric validation
for testing graph database metrics functionality.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import m_flow
from m_flow.adapters.graph import get_graph_provider
from m_flow.core import MemoryNode
from m_flow.storage.add_memory_nodes import persist_memory_nodes

if TYPE_CHECKING:
    from typing import Any


# ============================================================================
# Test Data Models
# ============================================================================


class Document(MemoryNode):
    """Test document node."""

    path: str
    metadata: dict = {"index_fields": []}


class ContentFragment(MemoryNode):
    """Test content fragment node."""

    part_of: Document
    text: str
    contains: Optional[list["Entity"]] = None
    metadata: dict = {"index_fields": ["text"]}


class EntityType(MemoryNode):
    """Test concept type node."""

    name: str
    metadata: dict = {"index_fields": ["name"]}


class Entity(MemoryNode):
    """Test concept node."""

    name: str
    is_type: EntityType
    metadata: dict = {"index_fields": ["name"]}


# Enable forward references
ContentFragment.model_rebuild()


# ============================================================================
# Test Graph Builders
# ============================================================================


async def build_disconnected_graph() -> None:
    """
    Create a test graph with two disconnected subgraphs.

    Graph structure:
    - doc1 -> chunk1 -> [alice, alice2] -> person_type
    - doc2 -> chunk2 -> [bob] -> person_type2
    """
    # First subgraph
    doc1 = Document(path="test/path")
    person_type = EntityType(name="Person")
    alice = Entity(name="Alice", is_type=person_type)
    alice2 = Entity(name="Alice2", is_type=person_type)
    chunk1 = ContentFragment(
        part_of=doc1,
        text="This is a chunk of text",
        contains=[alice, alice2],
    )

    # Second subgraph (disconnected)
    doc2 = Document(path="test/path2")
    person_type2 = EntityType(name="Person")
    bob = Entity(name="Bob", is_type=person_type2)
    chunk2 = ContentFragment(
        part_of=doc2,
        text="This is a chunk of text",
        contains=[bob],
    )

    await persist_memory_nodes([chunk1, chunk2])


async def build_connected_graph() -> None:
    """
    Create a test graph with a self-loop for testing cycle detection.

    Graph structure:
    - doc -> chunk -> [alice, alice2, chunk] -> person_type
    Note: chunk contains itself (self-loop)
    """
    doc = Document(path="test/path")
    person_type = EntityType(name="Person")
    alice = Entity(name="Alice", is_type=person_type)
    alice2 = Entity(name="Alice2", is_type=person_type)

    chunk = ContentFragment(
        part_of=doc,
        text="This is a chunk of text",
        contains=[],
    )
    # Add self-loop for testing self-loop counting
    chunk.contains = [alice, alice2, chunk]

    await persist_memory_nodes([chunk])


# ============================================================================
# Metric Validation
# ============================================================================


def load_ground_truth() -> dict[str, Any]:
    """Load expected metrics from ground truth JSON."""
    gt_file = Path(__file__).parent / "ground_truth_metrics.json"
    with open(gt_file, "r", encoding="utf-8") as f:
        return json.load(f)


async def fetch_metrics(provider: str, extended: bool = True) -> dict[str, Any]:
    """
    Configure provider, build test graph, and fetch metrics.

    Args:
        provider: Graph database provider name
        extended: If True, use connected graph; else disconnected

    Returns:
        Dictionary of graph metrics
    """
    m_flow.config.set_graph_database_provider(provider)

    engine = await get_graph_provider()
    await engine.delete_graph()

    if extended:
        await build_connected_graph()
    else:
        await build_disconnected_graph()

    return await engine.get_graph_metrics(extended=extended)


async def validate_metrics(provider: str, extended: bool = True) -> None:
    """
    Validate graph metrics against ground truth.

    Args:
        provider: Graph database provider name
        extended: If True, use connected ground truth; else disconnected

    Raises:
        AssertionError: If metrics don't match expected values
    """
    actual = await fetch_metrics(provider=provider, extended=extended)

    ground_truth = load_ground_truth()
    expected = ground_truth["connected"] if extended else ground_truth["disconnected"]

    # Check for key differences
    actual_keys = set(actual.keys())
    expected_keys = set(expected.keys())

    if actual_keys != expected_keys:
        diff = actual_keys.symmetric_difference(expected_keys)
        raise AssertionError(f"Metric key mismatch: {diff}")

    # Compare values
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if actual_value != expected_value:
            raise AssertionError(
                f"Metric '{key}' mismatch with {provider}: expected {expected_value}, got {actual_value}"
            )
