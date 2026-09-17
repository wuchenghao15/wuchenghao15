from __future__ import annotations

import pytest

from axon.core.graph.graph import KnowledgeGraph
from axon.core.graph.model import GraphNode, NodeLabel, RelType, generate_id
from axon.core.ingestion.heritage import process_heritage
from axon.core.ingestion.parser_phase import FileParseData
from axon.core.ingestion.symbol_lookup import build_name_index
from axon.core.parsers.base import ParseResult

_HERITAGE_LABELS = (NodeLabel.CLASS, NodeLabel.INTERFACE)

@pytest.fixture()
def graph() -> KnowledgeGraph:
    """Return a KnowledgeGraph pre-populated with Class and Interface nodes.

    Layout:
    - Class:src/models.py:Animal
    - Class:src/models.py:Dog
    - Interface:src/types.ts:Serializable
    - Class:src/models.ts:User
    """
    g = KnowledgeGraph()

    # Python class nodes
    g.add_node(
        GraphNode(
            id=generate_id(NodeLabel.CLASS, "src/models.py", "Animal"),
            label=NodeLabel.CLASS,
            name="Animal",
            file_path="src/models.py",
        )
    )
    g.add_node(
        GraphNode(
            id=generate_id(NodeLabel.CLASS, "src/models.py", "Dog"),
            label=NodeLabel.CLASS,
            name="Dog",
            file_path="src/models.py",
        )
    )

    # TypeScript interface node
    g.add_node(
        GraphNode(
            id=generate_id(NodeLabel.INTERFACE, "src/types.ts", "Serializable"),
            label=NodeLabel.INTERFACE,
            name="Serializable",
            file_path="src/types.ts",
        )
    )

    # TypeScript class node
    g.add_node(
        GraphNode(
            id=generate_id(NodeLabel.CLASS, "src/models.ts", "User"),
            label=NodeLabel.CLASS,
            name="User",
            file_path="src/models.ts",
        )
    )

    return g

def _make_parse_data(
    file_path: str,
    heritage: list[tuple[str, str, str]],
) -> FileParseData:
    """Create a FileParseData with only heritage tuples populated."""
    return FileParseData(
        file_path=file_path,
        language="python",
        parse_result=ParseResult(heritage=heritage),
    )

class TestBuildSymbolIndex:
    def test_build_symbol_index(self, graph: KnowledgeGraph) -> None:
        index = build_name_index(graph, _HERITAGE_LABELS)

        assert "Animal" in index
        assert "Dog" in index
        assert "Serializable" in index
        assert "User" in index

    def test_index_values_are_node_ids(self, graph: KnowledgeGraph) -> None:
        index = build_name_index(graph, _HERITAGE_LABELS)

        for name, node_ids in index.items():
            assert isinstance(node_ids, list)
            for node_id in node_ids:
                node = graph.get_node(node_id)
                assert node is not None
                assert node.name == name

    def test_index_excludes_non_heritage_labels(
        self, graph: KnowledgeGraph
    ) -> None:
        # Add a function node -- it should NOT appear in the index.
        graph.add_node(
            GraphNode(
                id=generate_id(NodeLabel.FUNCTION, "src/models.py", "helper"),
                label=NodeLabel.FUNCTION,
                name="helper",
                file_path="src/models.py",
            )
        )
        index = build_name_index(graph, _HERITAGE_LABELS)
        assert "helper" not in index

class TestProcessHeritageExtends:
    def test_process_heritage_extends(self, graph: KnowledgeGraph) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Dog", "extends", "Animal")],
            ),
        ]
        process_heritage(parse_data, graph)

        extends_rels = graph.get_relationships_by_type(RelType.EXTENDS)
        assert len(extends_rels) == 1

        rel = extends_rels[0]
        assert rel.source == generate_id(NodeLabel.CLASS, "src/models.py", "Dog")
        assert rel.target == generate_id(NodeLabel.CLASS, "src/models.py", "Animal")

    def test_extends_relationship_id_format(
        self, graph: KnowledgeGraph
    ) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Dog", "extends", "Animal")],
            ),
        ]
        process_heritage(parse_data, graph)

        extends_rels = graph.get_relationships_by_type(RelType.EXTENDS)
        rel = extends_rels[0]
        assert rel.id.startswith("extends:")
        assert "->" in rel.id

class TestProcessHeritageImplements:
    def test_process_heritage_implements(self, graph: KnowledgeGraph) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.ts",
                [("User", "implements", "Serializable")],
            ),
        ]
        process_heritage(parse_data, graph)

        impl_rels = graph.get_relationships_by_type(RelType.IMPLEMENTS)
        assert len(impl_rels) == 1

        rel = impl_rels[0]
        assert rel.source == generate_id(NodeLabel.CLASS, "src/models.ts", "User")
        assert rel.target == generate_id(
            NodeLabel.INTERFACE, "src/types.ts", "Serializable"
        )

    def test_implements_relationship_type(
        self, graph: KnowledgeGraph
    ) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.ts",
                [("User", "implements", "Serializable")],
            ),
        ]
        process_heritage(parse_data, graph)

        impl_rels = graph.get_relationships_by_type(RelType.IMPLEMENTS)
        assert impl_rels[0].type == RelType.IMPLEMENTS

class TestProcessHeritageUnresolvedParent:
    def test_process_heritage_unresolved_parent(
        self, graph: KnowledgeGraph
    ) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Dog", "extends", "UnknownBase")],
            ),
        ]
        # Should not raise.
        process_heritage(parse_data, graph)

        extends_rels = graph.get_relationships_by_type(RelType.EXTENDS)
        assert len(extends_rels) == 0

    def test_unresolved_child_also_skipped(
        self, graph: KnowledgeGraph
    ) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Phantom", "extends", "Animal")],
            ),
        ]
        process_heritage(parse_data, graph)

        extends_rels = graph.get_relationships_by_type(RelType.EXTENDS)
        assert len(extends_rels) == 0

class TestProcessHeritageMultiple:
    def test_multiple_heritage(self, graph: KnowledgeGraph) -> None:
        # Add a second interface for the test.
        graph.add_node(
            GraphNode(
                id=generate_id(NodeLabel.INTERFACE, "src/types.ts", "Printable"),
                label=NodeLabel.INTERFACE,
                name="Printable",
                file_path="src/types.ts",
            )
        )
        # User extends Animal (cross-file), implements Serializable, implements Printable
        # For cross-file extends to work we need Animal in the graph (it is).
        parse_data = [
            _make_parse_data(
                "src/models.ts",
                [
                    ("User", "extends", "Animal"),
                    ("User", "implements", "Serializable"),
                    ("User", "implements", "Printable"),
                ],
            ),
        ]
        process_heritage(parse_data, graph)

        extends_rels = graph.get_relationships_by_type(RelType.EXTENDS)
        impl_rels = graph.get_relationships_by_type(RelType.IMPLEMENTS)

        assert len(extends_rels) == 1
        assert len(impl_rels) == 2

        # Total: 3 heritage relationships.
        total = len(extends_rels) + len(impl_rels)
        assert total == 3

    def test_multiple_heritage_sources_are_correct(
        self, graph: KnowledgeGraph
    ) -> None:
        graph.add_node(
            GraphNode(
                id=generate_id(NodeLabel.INTERFACE, "src/types.ts", "Printable"),
                label=NodeLabel.INTERFACE,
                name="Printable",
                file_path="src/types.ts",
            )
        )
        parse_data = [
            _make_parse_data(
                "src/models.ts",
                [
                    ("User", "extends", "Animal"),
                    ("User", "implements", "Serializable"),
                    ("User", "implements", "Printable"),
                ],
            ),
        ]
        process_heritage(parse_data, graph)

        user_id = generate_id(NodeLabel.CLASS, "src/models.ts", "User")

        all_rels = graph.get_relationships_by_type(
            RelType.EXTENDS
        ) + graph.get_relationships_by_type(RelType.IMPLEMENTS)

        for rel in all_rels:
            assert rel.source == user_id

class TestProtocolAnnotation:
    def test_protocol_parent_annotates_child(self, graph: KnowledgeGraph) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Animal", "extends", "Protocol")],
            ),
        ]
        process_heritage(parse_data, graph)

        animal_id = generate_id(NodeLabel.CLASS, "src/models.py", "Animal")
        animal = graph.get_node(animal_id)
        assert animal is not None
        assert animal.properties.get("is_protocol") is True

    def test_abc_parent_annotates_child(self, graph: KnowledgeGraph) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Animal", "extends", "ABC")],
            ),
        ]
        process_heritage(parse_data, graph)

        animal_id = generate_id(NodeLabel.CLASS, "src/models.py", "Animal")
        animal = graph.get_node(animal_id)
        assert animal is not None
        assert animal.properties.get("is_protocol") is True

    def test_non_protocol_parent_not_annotated(self, graph: KnowledgeGraph) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Dog", "extends", "UnknownBase")],
            ),
        ]
        process_heritage(parse_data, graph)

        dog_id = generate_id(NodeLabel.CLASS, "src/models.py", "Dog")
        dog = graph.get_node(dog_id)
        assert dog is not None
        assert dog.properties.get("is_protocol") is None

    def test_protocol_annotation_does_not_create_edge(self, graph: KnowledgeGraph) -> None:
        parse_data = [
            _make_parse_data(
                "src/models.py",
                [("Animal", "extends", "Protocol")],
            ),
        ]
        process_heritage(parse_data, graph)

        extends_rels = graph.get_relationships_by_type(RelType.EXTENDS)
        assert len(extends_rels) == 0
