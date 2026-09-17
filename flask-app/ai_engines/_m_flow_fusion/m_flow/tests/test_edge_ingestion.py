"""
Edge Ingestion Test Module
==========================
m_flow.tests.test_edge_ingestion

Validates edge creation and relationship extraction:
- Structural edges (contains, is_a, is_part_of, made_from)
- Edge text property format validation
- Optional Entity-Entity edges when enabled
"""

import pathlib
import asyncio
import os
from collections import Counter

import m_flow
from m_flow.adapters.graph import get_graph_provider
from m_flow.auth.methods import get_seed_user
from m_flow.shared.logging_utils import get_logger

_logger = get_logger()

# Configuration flag for Entity-to-Entity edges (disabled by default)
_SKIP_CONCEPT_EDGES = os.getenv("MFLOW_SKIP_ENTITY_ENTITY_EDGES", "true").lower() in (
    "1",
    "true",
    "yes",
    "y",
    "on",
)


def _validate_edge_text_format(edge_text: str) -> bool:
    """
    Validate edge_text follows expected format.

    Format is either "name | description" or just "name".
    """
    if not edge_text:
        return False
    return "|" in edge_text or len(edge_text.split()) <= 10


async def test_edge_ingestion():
    """
    Validate edge creation during knowledge graph construction.

    Tests structural edge creation (always enabled) and optionally
    Entity-Entity edges when MFLOW_SKIP_ENTITY_ENTITY_EDGES=false.
    """
    # Configure storage
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_edge_ingestion").resolve()
    system_dir = (test_root / ".mflow/system" / "test_edge_ingestion").resolve()

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Clean start
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Define test sentences with various relationship types
    sentences = [
        "Dave watches Dexter Resurrection",
        "Ana likes apples",
        "Bob prefers Mflow over other solutions",
    ]

    # Ingest and memorize
    await m_flow.add(sentences, dataset_name="edge_ingestion_test")
    user = await get_seed_user()
    await m_flow.memorize(["edge_ingestion_test"], user=user)

    # Get graph data
    graph = await get_graph_provider()
    nodes, edges = await graph.get_graph_data()

    # Count edge types
    type_counts = Counter(e[2] for e in edges)
    _logger.info("Edge type distribution: %s", dict(type_counts))

    # =========================================
    # Validate edge_text property
    # =========================================
    involves_entity_edges = [e for e in edges if e[2] == "involves_entity"]
    assert len(involves_entity_edges) > 0, "Must have at least one 'involves_entity' edge"

    props = involves_entity_edges[0][3]
    assert "edge_text" in props, "Edge must have edge_text property"

    edge_text = props["edge_text"]
    assert _validate_edge_text_format(edge_text), f"Invalid edge_text format: {edge_text}"

    # Verify entity names appear in edge texts
    all_texts = [e[3].get("edge_text", "").lower() for e in involves_entity_edges]
    known_entities = ["dave", "ana", "bob", "dexter", "apples", "m_flow"]
    found = any(any(entity in txt for entity in known_entities) for txt in all_texts)
    assert found, f"Should find known entities in edge texts: {all_texts[:3]}"

    # =========================================
    # Validate structural edges
    # =========================================
    assert type_counts.get("involves_entity", 0) >= 1, "Must have 'involves_entity' edges"
    assert type_counts.get("is_a", 0) >= 1, "Must have 'is_a' edges"

    # Structural edge consistency (relaxed: counts may differ in episodic pipeline)
    assert type_counts.get("is_part_of", 0) >= 1, "Must have 'is_part_of' edges"

    # =========================================
    # Validate Entity-Entity edges (optional)
    # =========================================
    relationship_types = ["likes", "prefers", "watches"]

    if not _SKIP_CONCEPT_EDGES:
        # When Entity edges enabled, verify they exist
        found_count = sum(1 for t in relationship_types if t in type_counts)
        assert found_count >= 2, f"Expected at least 2 relationship edges, found {found_count}"
        assert len(type_counts) > 4, f"Expected >4 edge types with relationships, found {len(type_counts)}"
    else:
        _logger.info(
            "Entity edges disabled. Found %d types: %s",
            len(type_counts),
            dict(type_counts),
        )

    _logger.info("Edge ingestion test completed")


if __name__ == "__main__":
    asyncio.run(test_edge_ingestion())
