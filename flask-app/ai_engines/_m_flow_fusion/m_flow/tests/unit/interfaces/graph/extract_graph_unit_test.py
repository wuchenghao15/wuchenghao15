"""
Graph Extraction Unit Tests
===========================
m_flow.tests.unit.interfaces.graph.extract_graph_unit_test

Unit tests for extract_graph utility that extracts graph
structures (nodes and edges) from Pydantic model hierarchies.
"""

import pytest
from typing import List, Any
from m_flow.core import MemoryNode, Edge
from m_flow.knowledge.graph_ops.utils import extract_graph


# =============================================================================
# Test Model Definitions
# =============================================================================


class DocumentNode(MemoryNode):
    """Represents a document in the knowledge graph."""

    path: str
    metadata: dict = {"index_fields": []}


class TextFragment(MemoryNode):
    """Represents a chunk of text within a document."""

    source: DocumentNode
    content: str
    references: List["SemanticConcept"] = None
    metadata: dict = {"index_fields": ["content"]}


class ConceptCategory(MemoryNode):
    """Classification category for semantic concepts."""

    label: str
    metadata: dict = {"index_fields": ["label"]}


class SemanticConcept(MemoryNode):
    """A semantic concept extracted from text."""

    label: str
    category: ConceptCategory
    metadata: dict = {"index_fields": ["label"]}


class Organization(MemoryNode):
    """Represents an organization with employee relationships."""

    title: str
    staff: List[Any] = None  # Supports flexible edge tuples
    metadata: dict = {"index_fields": ["title"]}


class TeamMember(MemoryNode):
    """Individual team member entity."""

    name: str
    position: str
    metadata: dict = {"index_fields": ["name"]}


# Rebuild models for forward reference resolution
TextFragment.model_rebuild()
Organization.model_rebuild()


# =============================================================================
# Test Cases
# =============================================================================


@pytest.mark.asyncio
async def test_basic_node_relationship():
    """Validates node and edge extraction from a simple two-node relationship."""
    category = ConceptCategory(label="TestCategory")
    concept = SemanticConcept(label="TestConcept", category=category)

    node_registry = {}
    edge_registry = {}
    prop_tracker = {}

    extracted_nodes, extracted_edges = await extract_graph(concept, node_registry, edge_registry, prop_tracker)

    assert len(extracted_nodes) == 2, f"Should extract 2 nodes, found {len(extracted_nodes)}"
    assert len(extracted_edges) == 1, f"Should extract 1 edge, found {len(extracted_edges)}"

    expected_edge_key = f"{str(concept.id)}_{str(category.id)}_category"
    assert expected_edge_key in edge_registry, f"Missing edge: {expected_edge_key}"


@pytest.mark.asyncio
async def test_document_with_multiple_concepts():
    """Tests extraction of document-chunk-concept hierarchies."""
    doc = DocumentNode(path="test/document.txt")
    fragment = TextFragment(source=doc, content="Sample text fragment", references=[])

    cat = ConceptCategory(label="Person")
    concept_a = SemanticConcept(label="Alice", category=cat)
    concept_b = SemanticConcept(label="Bob", category=cat)

    fragment.references.append(concept_a)
    fragment.references.append(concept_b)

    node_registry = {}
    edge_registry = {}
    prop_tracker = {}

    extracted_nodes, extracted_edges = await extract_graph(fragment, node_registry, edge_registry, prop_tracker)

    assert len(extracted_nodes) == 5, f"Expected 5 nodes, found {len(extracted_nodes)}"
    assert len(extracted_edges) == 5, f"Expected 5 edges, found {len(extracted_edges)}"


@pytest.mark.asyncio
async def test_duplicate_object_handling():
    """Verifies that duplicate object references don't create duplicate nodes."""
    doc = DocumentNode(path="duplicate/test.txt")
    fragment = TextFragment(source=doc, content="Fragment with duplicates", references=[])

    cat = ConceptCategory(label="Animal")
    shared_concept = SemanticConcept(label="Cat", category=cat)

    # Add same concept multiple times
    fragment.references.extend([shared_concept, shared_concept, shared_concept])

    node_registry = {}
    edge_registry = {}
    prop_tracker = {}

    extracted_nodes, extracted_edges = await extract_graph(fragment, node_registry, edge_registry, prop_tracker)

    assert len(extracted_nodes) == 4, f"Expected 4 unique nodes, found {len(extracted_nodes)}"
    assert len(extracted_edges) == 3, f"Expected 3 edges, found {len(extracted_edges)}"


@pytest.mark.asyncio
async def test_deeply_nested_structure():
    """Tests extraction from a complex multi-level nested graph structure."""
    doc = DocumentNode(path="nested/structure.txt")

    frag_1 = TextFragment(source=doc, content="First fragment", references=[])
    frag_2 = TextFragment(source=doc, content="Second fragment", references=[])

    vehicle_cat = ConceptCategory(label="Vehicle")
    person_cat = ConceptCategory(label="Person")

    car = SemanticConcept(label="Car", category=vehicle_cat)
    bike = SemanticConcept(label="Bike", category=vehicle_cat)
    person = SemanticConcept(label="Alice", category=person_cat)

    frag_1.references.extend([car, bike])
    frag_2.references.append(person)

    node_registry = {}
    edge_registry = {}
    prop_tracker = {}

    nodes_1, edges_1 = await extract_graph(frag_1, node_registry, edge_registry, prop_tracker)
    nodes_2, edges_2 = await extract_graph(frag_2, node_registry, edge_registry, prop_tracker)

    total_nodes = nodes_1 + nodes_2
    total_edges = edges_1 + edges_2

    assert len(total_nodes) == 8, f"Expected 8 nodes total, found {len(total_nodes)}"
    assert len(total_edges) == 8, f"Expected 8 edges total, found {len(total_edges)}"


@pytest.mark.asyncio
async def test_empty_reference_list():
    """Tests extraction when the references list is empty."""
    doc = DocumentNode(path="empty/refs.txt")
    fragment = TextFragment(source=doc, content="No concepts here", references=[])

    node_registry = {}
    edge_registry = {}
    prop_tracker = {}

    extracted_nodes, extracted_edges = await extract_graph(fragment, node_registry, edge_registry, prop_tracker)

    assert len(extracted_nodes) == 2, f"Expected 2 nodes, found {len(extracted_nodes)}"
    assert len(extracted_edges) == 1, f"Expected 1 edge, found {len(extracted_edges)}"


@pytest.mark.asyncio
async def test_weighted_edge_relationships():
    """Tests the flexible edge system with weighted relationships."""
    # Create team members
    lead = TeamMember(name="Tech Lead", position="Lead")
    dev_1 = TeamMember(name="Developer One", position="Developer")
    dev_2 = TeamMember(name="Developer Two", position="Developer")
    support_a = TeamMember(name="Support A", position="Support")
    support_b = TeamMember(name="Support B", position="Support")

    # Create organization with various relationship types
    org = Organization(
        title="Engineering Team",
        staff=[
            # Single weighted edge
            (Edge(weight=0.9, relationship_type="leads"), lead),
            # Multi-weight edge
            (
                Edge(weights={"skill": 0.8, "tenure": 0.7}, relationship_type="employs"),
                dev_1,
            ),
            # Direct relationship (no explicit edge)
            dev_2,
            # Group relationship
            (
                Edge(weights={"efficiency": 0.8}, relationship_type="supports"),
                [support_a, support_b],
            ),
        ],
    )

    node_registry = {}
    edge_registry = {}
    prop_tracker = {}

    extracted_nodes, extracted_edges = await extract_graph(org, node_registry, edge_registry, prop_tracker)

    # 6 nodes: 1 organization + 5 team members
    assert len(extracted_nodes) == 6, f"Expected 6 nodes, found {len(extracted_nodes)}"
    # 5 edges: one for each team member
    assert len(extracted_edges) == 5, f"Expected 5 edges, found {len(extracted_edges)}"

    # Verify all team members are connected
    member_ids = {str(m.id) for m in [lead, dev_1, dev_2, support_a, support_b]}
    connected_ids = {str(e[1]) for e in extracted_edges}
    assert member_ids.issubset(connected_ids), "All team members should be connected"
