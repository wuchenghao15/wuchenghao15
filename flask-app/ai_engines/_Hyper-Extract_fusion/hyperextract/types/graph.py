"""Graph Knowledge Pattern - extracts knowledge graphs with nodes and edges from text.

Provides automatic deduplication for both nodes and edges using OMem.
Supports single-stage and two-stage extraction strategies with consistency validation.
"""

from collections.abc import Callable
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
)

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from ontomem import OMem
from ontomem.merger import BaseMerger, MergeStrategy, create_merger
from ontosight import view_graph
from pydantic import BaseModel, Field, create_model

from hyperextract.utils.logging import get_logger

from .base import BaseAutoType

logger = get_logger(__name__)


NodeSchema = TypeVar("NodeSchema", bound=BaseModel)
EdgeSchema = TypeVar("EdgeSchema", bound=BaseModel)


# ==============================================================================
# Default Prompts - Defined outside the class for clarity and reusability
# ==============================================================================

DEFAULT_GRAPH_PROMPT = (
    "You are an expert knowledge graph extraction assistant. "
    "Extract all entities (nodes) and their relationships (edges) from the following text. "
    "Focus on being comprehensive and capturing the complete knowledge structure.\n\n"
    "CRITICAL CONSTRAINT: Every edge must connect two nodes that are present in the extracted nodes list. "
    "Do not create edges between entities that are not explicitly identified as nodes.\n\n"
    "### Source Text:\n"
    "{source_text}"
)

DEFAULT_NODE_PROMPT = (
    "You are an expert information extraction assistant specialized in entity/node recognition. "
    "Extract ALL relevant entities, concepts, or nodes from the following text with high precision.\n\n"
    "Focus on:\n"
    "- Being EXHAUSTIVE: capture all entity types mentioned\n"
    "- Being PRECISE: extract exact entity names and descriptions\n"
    "- Clarity: provide clear, concise descriptions for each entity\n\n"
    "Do not attempt to extract relationships at this stage, only identify entities.\n\n"
    "### Source Text:\n"
    "{source_text}"
)

DEFAULT_EDGE_PROMPT = (
    "You are an expert relationship extraction assistant. "
    "Extract relationships (edges) between the provided entities.\n\n"
    "CRITICAL RULES:\n"
    "1. ONLY extract edges connecting entities from the known entity list below\n"
    "2. DO NOT invent or hallucinate new entities that are not listed\n"
    "3. If an entity in the text is not in the known list, DO NOT create edges involving it\n"
    "4. Focus on explicit relationships mentioned in the text\n\n"
    "# Provided Entities\n"
    "{known_nodes}\n\n"
    "# Source Text:\n"
    "{source_text}"
)


class GraphEditMixin:
    """Hard-delete and LLM-assisted soft-delete for graph-family AutoTypes.

    Requires on `self`: `_node_memory` / `_edge_memory` (OMem) and the
    `node_key_extractor` / `edge_key_extractor` / `nodes_in_edge_extractor`
    callables. Index updates and LLM-assisted item editing delegate to
    OMem's `sync_index` / `edit` (ontomem >= 0.3.0).
    """

    # ==================== Source Provenance (v0.4.0+) ====================

    def _record_extraction_source(
        self,
        source_id: str | None,
        nodes: list[NodeSchema],
        edges: list[EdgeSchema],
    ) -> None:
        """Record raw (pre-merge) extraction results in the source ledgers.

        Reads ``self._pending_source_id`` (set by parse/feed_text); no-op when
        no source was attributed or the memories don't track sources.
        """
        if not source_id or not self._node_memory.track_sources:
            return
        content_hash = self._pending_content_hash
        self._node_memory.record_source(
            source_id,
            [node.model_dump() for node in nodes],
            content_hash=content_hash,
        )
        self._edge_memory.record_source(
            source_id,
            [edge.model_dump() for edge in edges],
            content_hash=content_hash,
        )

    def _adopt_source_ledger(self, other, source_id: str) -> None:
        """Transfer ledger entries for ``source_id`` from ``other`` to ``self``
        after parse() (the extraction ran on ``other``'s memories)."""
        for src_memory, dst_memory in (
            (other._node_memory, self._node_memory),
            (other._edge_memory, self._edge_memory),
        ):
            if source_id in src_memory._sources:
                dst_memory._sources[source_id] = src_memory._sources[source_id]

    def _dump_provenance(self, root: Path) -> None:
        """Persist the node/edge source ledgers alongside the KA."""
        try:
            self._node_memory.dump_sources(Path(root) / "sources_nodes.json")
            self._edge_memory.dump_sources(Path(root) / "sources_edges.json")
        except Exception as e:
            logger.warning("provenance_dump_failed", error=str(e))

    def _load_provenance(self, root: Path) -> None:
        """Restore the node/edge source ledgers alongside the KA."""
        try:
            node_path = Path(root) / "sources_nodes.json"
            edge_path = Path(root) / "sources_edges.json"
            if node_path.exists():
                self._node_memory.load_sources(node_path)
            if edge_path.exists():
                self._edge_memory.load_sources(edge_path)
        except Exception as e:
            logger.warning("provenance_load_failed", error=str(e))

    def remove_source(self, source_id: str, *, strategy: str = "exact") -> dict:
        """Remove every contribution of one source document (exact rollback).

        Keys contributed solely by the removed document are deleted; keys
        shared with other documents are re-merged from the surviving sources'
        raw results. The search index is patched in place when built.

        Args:
            source_id: Identifier used when the document was fed
                (``feed_text(text, source_id=...)`` / ``he feed --source``).
            strategy: "exact" (re-merge survivors) or "touched" (delete all
                affected keys).

        Returns:
            Combined node/edge report dict.
        """
        node_report = self._node_memory.remove_source(source_id, strategy=strategy)
        edge_report = self._edge_memory.remove_source(source_id, strategy=strategy)
        return {
            "source_id": source_id,
            "removed_nodes": node_report["removed_keys"],
            "remerged_nodes": node_report["remerged_keys"],
            "removed_edges": edge_report["removed_keys"],
            "remerged_edges": edge_report["remerged_keys"],
            "index_patched": node_report["index_patched"]
            and edge_report["index_patched"],
        }

    # ==================== Source Ledger (read) ====================

    def sources(self) -> dict[str, dict[str, Any]]:
        """Summarize the source ledger (node and edge memories combined).

        Returns:
            Dict mapping source_id to {raw_items, content_hash}. Raw-item
            counts are from the node ledger; edges share the same sources.
        """
        summary: dict[str, dict[str, Any]] = {}
        for source_id, info in self._node_memory.sources().items():
            summary[source_id] = dict(info)
        # Edge memories may know sources the node ledger lacks (empty-node
        # extractions); surface them too.
        for source_id, info in self._edge_memory.sources().items():
            if source_id not in summary:
                summary[source_id] = dict(info)
        return summary

    def source_content_hash(self, source_id: str) -> str | None:
        """Return the recorded content hash of a source (None if unknown)."""
        record = self._node_memory._sources.get(
            source_id
        ) or self._edge_memory._sources.get(source_id)
        return record.content_hash if record else None

    def source_tags(self, source_id: str) -> list[str]:
        """Return the tags of one source (empty if unknown/untagged)."""
        for memory in (self._node_memory, self._edge_memory):
            if source_id in memory._sources:
                return memory.source_tags(source_id)
        return []

    def tag_source(
        self,
        source_id: str,
        *,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> list[str]:
        """Add/remove tags on one source across both ledgers.

        Tags are applied to every ledger that knows the source so scoped
        search stays consistent on the node and edge sides.

        Raises:
            KeyError: If no ledger knows ``source_id``.
        """
        tags: list[str] = []
        for memory in (self._node_memory, self._edge_memory):
            if source_id in memory._sources:
                tags = memory.tag_source(source_id, add=add, remove=remove)
        if not tags and source_id not in self.sources():
            raise KeyError(f"Unknown source_id: {source_id!r}")
        return tags

    # ==================== Document Upsert ====================

    def feed_text(
        self,
        text: str,
        *,
        source_id: str | None = None,
        content_hash: str | None = None,
    ) -> "AutoGraph":
        """Feed text with document-level upsert semantics.

        When ``source_id`` was attributed before, the previous version's
        contributions are rolled back first (exact re-merge from surviving
        sources), so facts removed from the updated document do not linger.
        First-time attribution behaves like a normal feed.
        """
        if (
            source_id
            and self._node_memory.track_sources
            and source_id in self.sources()
        ):
            logger.info("stage=source_upsert rollback source=%s", source_id)
            if source_id in self._node_memory.sources():
                self._node_memory.remove_source(source_id)
            if source_id in self._edge_memory.sources():
                self._edge_memory.remove_source(source_id)
        return super().feed_text(text, source_id=source_id, content_hash=content_hash)

    # ==================== Removal ====================

    def remove_nodes(self, *keys: str) -> dict:
        """Hard-delete nodes by key, together with any edges they anchor.

        Edges touching a removed node would dangle, so every such edge is
        removed as well. When the search index is built, it is patched in
        place (only the affected vectors are deleted) instead of discarded.

        Args:
            keys: Node keys (as produced by `node_key_extractor`).

        Returns:
            Report dict with `removed_nodes`, `not_found_nodes`,
            `removed_orphan_edges`, and `index_patched`.
        """
        node_had = self._node_memory.has_index()
        edge_had = self._edge_memory.has_index()

        removed, not_found = self._node_memory.remove_many(keys)
        removed_node_keys = set(removed)

        orphaned: list = []
        if removed_node_keys:
            orphan_candidates = []
            for edge in list(self._edge_memory.items):
                endpoints = set(self.nodes_in_edge_extractor(edge))
                if endpoints & removed_node_keys:
                    orphan_candidates.append(self.edge_key_extractor(edge))
            orphaned, _ = self._edge_memory.remove_many(orphan_candidates)

        node_ok = (
            self._node_memory.sync_index(removed_keys=removed_node_keys)
            if node_had
            else False
        )
        edge_ok = (
            self._edge_memory.sync_index(removed_keys=set(orphaned))
            if edge_had and orphaned
            else True
        )
        index_patched = (node_had or edge_had) and node_ok and edge_ok

        logger.info(
            "stage=remove_nodes removed=%d not_found=%d orphan_edges=%d index_patched=%s",
            len(removed),
            len(not_found),
            len(orphaned),
            index_patched,
        )
        return {
            "removed_nodes": removed,
            "not_found_nodes": not_found,
            "removed_orphan_edges": orphaned,
            "index_patched": index_patched,
        }

    def remove_edges(self, *keys: str) -> dict:
        """Hard-delete edges by key.

        When the search index is built, it is patched in place (only the
        affected vectors are deleted) instead of discarded.

        Args:
            keys: Edge keys (as produced by `edge_key_extractor`).

        Returns:
            Report dict with `removed_edges`, `not_found_edges`, and
            `index_patched`.
        """
        edge_had = self._edge_memory.has_index()

        removed, not_found = self._edge_memory.remove_many(keys)

        edge_ok = (
            self._edge_memory.sync_index(removed_keys=set(removed))
            if edge_had
            else False
        )
        index_patched = edge_had and edge_ok

        logger.info(
            "stage=remove_edges removed=%d not_found=%d", len(removed), len(not_found)
        )
        return {
            "removed_edges": removed,
            "not_found_edges": not_found,
            "index_patched": index_patched,
        }

    # ==================== Soft Delete (LLM-assisted) ====================

    def edit_node(
        self,
        key: str,
        *,
        remove_fact: str | None = None,
        instruction: str | None = None,
        dry_run: bool = False,
    ) -> dict:
        """Soft-delete a fact from a node via LLM-assisted rewrite.

        Delegates to `OMem.edit` on the node memory: the item is rewritten
        under the same schema and replaced (merge bypassed), the key must
        stay unchanged, and the built index is patched in place.

        Args:
            key: Node key to edit.
            remove_fact: Fact to remove from the node (exclusive with
                `instruction`).
            instruction: Free-form edit instruction (exclusive with
                `remove_fact`).
            dry_run: Return the proposed rewrite without applying it.

        Returns:
            Report dict with `changed`, `applied`, `old`, `new`, and
            `index_patched`.
        """
        return self._node_memory.edit(
            key,
            remove_fact=remove_fact,
            instruction=instruction,
            dry_run=dry_run,
        )

    def edit_edge(
        self,
        key: str,
        *,
        remove_fact: str | None = None,
        instruction: str | None = None,
        dry_run: bool = False,
    ) -> dict:
        """Soft-delete a fact from an edge via LLM-assisted rewrite.

        Delegates to `OMem.edit` on the edge memory (see `edit_node`).

        Args:
            key: Edge key to edit.
            remove_fact: Fact to remove from the edge (exclusive with
                `instruction`).
            instruction: Free-form edit instruction (exclusive with
                `remove_fact`).
            dry_run: Return the proposed rewrite without applying it.

        Returns:
            Report dict with `changed`, `applied`, `old`, `new`, and
            `index_patched`.
        """
        return self._edge_memory.edit(
            key,
            remove_fact=remove_fact,
            instruction=instruction,
            dry_run=dry_run,
        )


class GraphIndexMixin:
    """Shared merge / index / search for graph-family AutoTypes.

    Lives beside :class:`GraphEditMixin` so ``AutoGraph`` and
    ``AutoHypergraph`` cannot drift on search-scope forwarding (#90).

    Requires on ``self``: ``_node_memory`` / ``_edge_memory``,
    ``graph_schema``, ``node_schema``, ``edge_schema``, ``node_merger``,
    ``edge_merger``, and ``empty()``.

    Public ``search()`` still returns ``(nodes, edges)``. Display shaping
    (SearchHits) stays in the CLI / MCP layer.
    """

    def merge_batch_data(
        self,
        data_list_or_tuple: list[Any]
        | tuple[list[list[NodeSchema]], list[list[EdgeSchema]]],
    ) -> Any:
        """Merge multiple graphs or node/edge tuples into one.

        Supports two input formats:
        - List of graph schema objects (standard format)
        - Tuple of (List[List[NodeSchema]], List[List[EdgeSchema]])
        """
        if not data_list_or_tuple:
            logger.warning("stage=merge_batch_empty input_is_empty")
            return self.graph_schema(nodes=[], edges=[])

        if isinstance(data_list_or_tuple, list):
            data_list_or_tuple = [g for g in data_list_or_tuple if g is not None]
            if not data_list_or_tuple:
                return self.graph_schema(nodes=[], edges=[])

        logger.debug(
            "stage=merge_batch_start input_type=%s",
            "tuple"
            if not isinstance(data_list_or_tuple[0], self.graph_schema)
            else "list",
        )

        if isinstance(data_list_or_tuple[0], self.graph_schema):
            all_nodes, all_edges = [], []
            for graph in data_list_or_tuple:
                all_nodes.extend(graph.nodes)
                all_edges.extend(graph.edges)
        else:
            assert len(data_list_or_tuple) == 2, (
                "Invalid input format for batch merging"
            )
            nodes_lists, edges_lists = data_list_or_tuple[0], data_list_or_tuple[1]

            if not nodes_lists and not edges_lists:
                logger.warning("stage=merge_batch_empty_tuple nodes_and_edges_empty")
                return self.graph_schema(nodes=[], edges=[])

            if nodes_lists and nodes_lists[0]:
                assert isinstance(nodes_lists[0][0], self.node_schema), (
                    "Invalid node list format for batch merging"
                )
            if edges_lists and edges_lists[0]:
                assert isinstance(edges_lists[0][0], self.edge_schema), (
                    "Invalid edge list format for batch merging"
                )

            all_nodes, all_edges = [], []
            for node_list, edge_list in zip(nodes_lists, edges_lists):
                all_nodes.extend(node_list)
                all_edges.extend(edge_list)

        logger.debug(
            "stage=merge_batch_raw total_nodes=%d total_edges=%d",
            len(all_nodes),
            len(all_edges),
        )
        merged_nodes = self.node_merger.merge(all_nodes) if all_nodes else []
        merged_edges = self.edge_merger.merge(all_edges) if all_edges else []
        logger.debug(
            "stage=merge_batch_complete merged_nodes=%d merged_edges=%d "
            "deduped_nodes=%d deduped_edges=%d",
            len(merged_nodes),
            len(merged_edges),
            len(all_nodes) - len(merged_nodes),
            len(all_edges) - len(merged_edges),
        )
        return self.graph_schema(nodes=merged_nodes, edges=merged_edges)

    def build_index(self, index_nodes: bool = True, index_edges: bool = True):
        """Build vector index for graph search.

        By default, builds indices for both nodes and edges.

        Args:
            index_nodes: Whether to index nodes (default: True).
            index_edges: Whether to index edges (default: True).
        """
        if index_nodes:
            self.build_node_index()

        if index_edges:
            self.build_edge_index()

    def build_node_index(self) -> None:
        """Build vector index specifically for nodes."""
        if not self.empty():
            self._node_memory.build_index()

    def build_edge_index(self) -> None:
        """Build vector index specifically for edges."""
        if not self.empty():
            self._edge_memory.build_index()

    def search(
        self,
        query: str,
        top_k_nodes: int = 3,
        top_k_edges: int = 3,
        top_k: int | None = None,
        *,
        source_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> tuple[list[NodeSchema], list[EdgeSchema]]:
        """Unified graph search interface.

        Always returns a tuple of (nodes, edges). Display layers must not
        treat this as a flat result list.
        """
        if top_k is not None:
            top_k_nodes = top_k
            top_k_edges = top_k

        if top_k_nodes <= 0 and top_k_edges <= 0:
            raise ValueError(
                "At least one of top_k_nodes or top_k_edges must be positive."
            )

        nodes: list[NodeSchema] = []
        edges: list[EdgeSchema] = []

        if top_k_nodes > 0:
            if not self._node_memory.has_index():
                raise ValueError("Node index not built. Call build_index() first.")
            nodes = self.search_nodes(
                query, top_k=top_k_nodes, source_ids=source_ids, tags=tags
            )

        if top_k_edges > 0:
            if not self._edge_memory.has_index():
                raise ValueError("Edge index not built. Call build_index() first.")
            edges = self.search_edges(
                query, top_k=top_k_edges, source_ids=source_ids, tags=tags
            )

        return nodes, edges

    def search_nodes(
        self,
        query: str,
        top_k: int = 3,
        *,
        source_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[NodeSchema]:
        """Semantic search for nodes/entities only."""
        return self._node_memory.search(
            query=query, top_k=top_k, source_ids=source_ids, tags=tags
        )

    def search_edges(
        self,
        query: str,
        top_k: int = 3,
        *,
        source_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[EdgeSchema]:
        """Semantic search for edges/relationships only."""
        return self._edge_memory.search(
            query=query, top_k=top_k, source_ids=source_ids, tags=tags
        )


class AutoGraphSchema(BaseModel, Generic[NodeSchema, EdgeSchema]):
    """Generic schema container for graph-based knowledge patterns."""

    nodes: list[NodeSchema] = Field(
        default_factory=list, description="Graph nodes/entities"
    )
    edges: list[EdgeSchema] = Field(
        default_factory=list, description="Graph edges/relationships"
    )


class NodeListSchema(BaseModel, Generic[NodeSchema]):
    """Intermediate schema for batch node extraction."""

    items: list[NodeSchema] = Field(
        default_factory=list,
        description="List of identified entities or nodes found in the text.",
    )


class EdgeListSchema(BaseModel, Generic[EdgeSchema]):
    """Intermediate schema for batch edge extraction."""

    items: list[EdgeSchema] = Field(
        default_factory=list,
        description="List of identified relationships or edges found in the text.",
    )


class AutoGraph(
    GraphEditMixin,
    GraphIndexMixin,
    BaseAutoType[AutoGraphSchema[NodeSchema, EdgeSchema]],
    Generic[NodeSchema, EdgeSchema],
):
    """AutoGraph - extracts knowledge graphs with nodes and edges from text.

    This pattern extracts structured knowledge graphs consisting of entities (nodes) and
    their relationships (edges). Suitable for entity relationship extraction, knowledge
    graph construction, and semantic network building.

    Key characteristics:
        - Extraction target: Graph structure with nodes and edges
        - Deduplication: Automatic deduplication for both nodes and edges using OMem
        - Node merge strategy: Configurable (LLM-powered intelligent merging by default)
        - Edge merge strategy: Configurable (simple merge by default)
        - Extraction modes:
            * one_stage: Extract nodes and edges simultaneously (faster, simpler prompt)
            * two_stage: Extract nodes first, then edges with node context (more accurate)
        - Consistency validation: Ensures edges only connect existing nodes

    Example:
        >>> class Entity(BaseModel):
        ...     name: str
        ...     type: str
        ...     properties: dict = {}
        >>>
        >>> class Relation(BaseModel):
        ...     source: str
        ...     target: str
        ...     relation_type: str
        >>>
        >>> graph = AutoGraph(
        ...     node_schema=Entity,
        ...     edge_schema=Relation,
        ...     node_key_extractor=lambda x: x.name,
        ...     edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
        ...     nodes_in_edge_extractor=lambda x: (x.source, x.target),
        ...     llm_client=llm,
        ...     embedder=embedder,
        ...     extraction_mode="two_stage"
        ... )
    """

    if TYPE_CHECKING:
        graph_schema: type[AutoGraphSchema[NodeSchema, EdgeSchema]]

    def __init__(
        self,
        node_schema: type[NodeSchema],
        edge_schema: type[EdgeSchema],
        node_key_extractor: Callable[[NodeSchema], str],
        edge_key_extractor: Callable[[EdgeSchema], str],
        nodes_in_edge_extractor: Callable[[EdgeSchema], tuple[str, str]],
        llm_client: BaseChatModel,
        embedder: Embeddings,
        *,
        extraction_mode: str = "one_stage",
        node_strategy_or_merger: MergeStrategy
        | BaseMerger = MergeStrategy.LLM.BALANCED,
        edge_strategy_or_merger: MergeStrategy
        | BaseMerger = MergeStrategy.LLM.BALANCED,
        prompt: str = "",
        prompt_for_node_extraction: str = "",
        prompt_for_edge_extraction: str = "",
        node_label_extractor: Callable[[NodeSchema], str] | None = None,
        edge_label_extractor: Callable[[EdgeSchema], str] | None = None,
        chunk_size: int = 2048,
        chunk_overlap: int = 256,
        max_workers: int = 10,
        verbose: bool = False,
        node_fields_for_index: list[str] | None = None,
        edge_fields_for_index: list[str] | None = None,
        **kwargs: Any,
    ):
        """Initialize AutoGraph with node/edge schemas and configuration.

        Args:
            node_schema: Pydantic BaseModel for nodes/entities.
            edge_schema: Pydantic BaseModel for edges/relationships.
            node_key_extractor: Function to extract unique key from node (e.g., lambda x: x.id).
            edge_key_extractor: Function to extract unique key from edge (e.g., lambda x: f"{x.src}-{x.rel}-{x.dst}").
            nodes_in_edge_extractor: Function to extract (source_key, target_key) node keys from an edge for validation.
            llm_client: Language model client for extraction.
            embedder: Embedding model for vector indexing.
            extraction_mode: "one_stage" (extract nodes+edges together) or "two_stage" (nodes first, then edges).
            node_strategy_or_merger: Merge strategy for duplicate nodes (default: LLM.BALANCED).
            edge_strategy_or_merger: Merge strategy for duplicate edges (default: LLM.BALANCED).
            prompt: Custom extraction prompt for one-stage mode.
            prompt_for_node_extraction: Custom extraction prompt for two-stage node extraction.
            prompt_for_edge_extraction: Custom extraction prompt for two-stage edge extraction.
            node_label_extractor: Optional function to extract label from node for visualization.
            edge_label_extractor: Optional function to extract label from edge for visualization.
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Overlapping characters between chunks.
            max_workers: Maximum concurrent extraction tasks.
            verbose: Whether to log progress.
            node_fields_for_index: Optional list of field names in node_schema to include in vector index.
                                   If None, all text fields are indexed by default.
                                   Example: ['name', 'description'] (only index these node fields)
            edge_fields_for_index: Optional list of field names in edge_schema to include in vector index.
                                   If None, all text fields are indexed by default.
                                   Example: ['relation_type', 'description'] (only index these edge fields)
            **kwargs: Additional arguments passed to create_merger() when strategy_or_merger is
                      a MergeStrategy enum. Ignored if strategy_or_merger is a BaseMerger instance.
        """

        # Store schemas and extractors
        self.node_schema = node_schema
        self.edge_schema = edge_schema
        self.node_key_extractor = node_key_extractor
        self.edge_key_extractor = edge_key_extractor
        self.nodes_in_edge_extractor = nodes_in_edge_extractor
        self.extraction_mode = extraction_mode
        self.node_fields_for_index = node_fields_for_index
        self.edge_fields_for_index = edge_fields_for_index
        # Persist kwargs for reconstruction
        self._constructor_kwargs = kwargs

        graph_prompt = prompt or self._default_prompt()
        # Create dynamic GraphSchema containers
        graph_schema_name = f"{node_schema.__name__}{edge_schema.__name__}Graph"
        self.graph_schema = create_model(
            graph_schema_name,
            nodes=(list[node_schema], Field(default_factory=list)),
            edges=(list[edge_schema], Field(default_factory=list)),
        )

        # Create schema for list extraction (two-stage mode) with 'items' field
        self.node_list_schema = create_model(
            "NodeList",
            items=(
                list[node_schema],
                Field(default_factory=list, description="Extracted nodes"),
            ),
        )
        self.edge_list_schema = create_model(
            "EdgeList",
            items=(
                list[edge_schema],
                Field(default_factory=list, description="Extracted edges"),
            ),
        )

        # Initialize Node Merger
        if isinstance(node_strategy_or_merger, BaseMerger):
            self.node_merger = node_strategy_or_merger
        else:
            self.node_merger = create_merger(
                strategy=node_strategy_or_merger,
                key_extractor=node_key_extractor,
                llm_client=llm_client,
                item_schema=node_schema,
                **kwargs,  # Pass additional arguments to create_merger
            )

        # Initialize Edge Merger
        if isinstance(edge_strategy_or_merger, BaseMerger):
            self.edge_merger = edge_strategy_or_merger
        else:
            self.edge_merger = create_merger(
                strategy=edge_strategy_or_merger,
                key_extractor=edge_key_extractor,
                llm_client=llm_client,
                item_schema=edge_schema,
                **kwargs,  # Pass additional arguments to create_merger
            )

        # Initialize OMem instances (Before super().__init__)
        self._node_memory = OMem(
            memory_schema=node_schema,
            key_extractor=node_key_extractor,
            llm_client=llm_client,
            embedder=embedder,
            strategy_or_merger=self.node_merger,
            verbose=verbose,
            fields_for_index=node_fields_for_index,  # Pass node field selection to OMem
            track_sources=True,  # source ledger for per-document rollback (#84)
        )

        self._edge_memory = OMem(
            memory_schema=edge_schema,
            key_extractor=edge_key_extractor,
            llm_client=llm_client,
            embedder=embedder,
            strategy_or_merger=self.edge_merger,
            verbose=verbose,
            fields_for_index=edge_fields_for_index,  # Pass edge field selection to OMem
            track_sources=True,  # source ledger for per-document rollback (#84)
        )

        # Store label extractors for visualization
        self._node_label_extractor = node_label_extractor
        self._edge_label_extractor = edge_label_extractor

        # Call parent init
        super().__init__(
            data_schema=self.graph_schema,
            llm_client=llm_client,
            embedder=embedder,
            prompt=graph_prompt,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            max_workers=max_workers,
            verbose=verbose,
        )

        # Initialize prompts (use custom if provided, otherwise use defaults)
        self.node_prompt = prompt_for_node_extraction or DEFAULT_NODE_PROMPT
        self.edge_prompt = prompt_for_edge_extraction or DEFAULT_EDGE_PROMPT

        # Two-stage mode: initialize extractors
        self.prompt_template = ChatPromptTemplate.from_template(self.node_prompt)
        self.node_extractor = (
            self.prompt_template
            | self.llm_client.with_structured_output(
                self.node_list_schema, method="function_calling"
            )
        )

        self.edge_prompt_template = ChatPromptTemplate.from_template(self.edge_prompt)
        self.edge_extractor = (
            self.edge_prompt_template
            | self.llm_client.with_structured_output(
                self.edge_list_schema, method="function_calling"
            )
        )

    def _default_prompt(self) -> str:
        """Returns the default prompt for one-stage graph extraction."""
        return DEFAULT_GRAPH_PROMPT

    def _create_empty_instance(self) -> "AutoGraph[NodeSchema, EdgeSchema]":
        """Creates a new empty AutoGraph instance with the same configuration as this one.

        Overrides parent method to handle AutoGraph-specific parameters.

        Returns:
            A new empty AutoGraph instance with identical configuration.
        """
        return self.__class__(
            node_schema=self.node_schema,
            edge_schema=self.edge_schema,
            node_key_extractor=self.node_key_extractor,
            edge_key_extractor=self.edge_key_extractor,
            nodes_in_edge_extractor=self.nodes_in_edge_extractor,
            llm_client=self.llm_client,
            embedder=self.embedder,
            extraction_mode=self.extraction_mode,
            node_strategy_or_merger=self.node_merger,
            edge_strategy_or_merger=self.edge_merger,
            prompt=self.prompt,
            prompt_for_node_extraction=self.node_prompt,
            prompt_for_edge_extraction=self.edge_prompt,
            node_label_extractor=self._node_label_extractor,
            edge_label_extractor=self._edge_label_extractor,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            max_workers=self.max_workers,
            verbose=self.verbose,
            node_fields_for_index=self.node_fields_for_index,
            edge_fields_for_index=self.edge_fields_for_index,
            **self._constructor_kwargs,  # Propagate additional arguments
        )

    @property
    def data(self) -> AutoGraphSchema[NodeSchema, EdgeSchema]:
        """Returns the current graph state (nodes and edges).

        Returns:
            AutoGraphSchema containing all nodes and edges.
        """
        return self.graph_schema(
            nodes=self._node_memory.items, edges=self._edge_memory.items
        )

    @property
    def nodes(self) -> list[NodeSchema]:
        """Returns the current node collection.

        Returns:
            List of nodes.
        """
        return self._node_memory.items

    @property
    def edges(self) -> list[EdgeSchema]:
        """Returns the current edge collection.

        Returns:
            List of edges.
        """
        return self._edge_memory.items

    def empty(self) -> bool:
        """Checks if the graph is empty (no nodes).

        Returns:
            True if node collections are empty, False otherwise.
        """
        return self._node_memory.empty()

    # ==================== State Management Lifecycle Hooks ====================

    def _init_data_state(self) -> None:
        """Initialize or reset graph data structures."""
        self._node_memory.clear()
        self._edge_memory.clear()

    def _init_index_state(self) -> None:
        """Initialize vector index to empty state."""
        self._node_memory.clear_index()
        self._edge_memory.clear_index()

    def _set_data_state(self, data: AutoGraphSchema[NodeSchema, EdgeSchema]) -> None:
        """Replace graph data with new data (full reset).

        Args:
            data: New graph data to set.
        """
        self._node_memory.clear()
        self._edge_memory.clear()

        if data.nodes:
            self._node_memory.add(data.nodes)
        if data.edges:
            self._edge_memory.add(data.edges)

        self.clear_index()

    def _update_data_state(
        self, incoming_data: AutoGraphSchema[NodeSchema, EdgeSchema]
    ) -> None:
        """Merge incoming graph data into current state.

        The vector index is patched in place: only the incoming nodes/edges
        are re-embedded, instead of dropping the whole index.

        Args:
            incoming_data: Incremental graph data to merge.
        """
        if self.empty():
            self._set_data_state(incoming_data)
            return

        # Suspend index invalidation while merging; re-embed only the
        # affected keys afterwards.
        with self._node_memory.suspended_index(), self._edge_memory.suspended_index():
            if incoming_data.nodes:
                self._node_memory.add(incoming_data.nodes)
            if incoming_data.edges:
                self._edge_memory.add(incoming_data.edges)

        if incoming_data.nodes:
            node_keys = {self.node_key_extractor(n) for n in incoming_data.nodes}
            self._node_memory.sync_index(upserted_keys=node_keys)
        if incoming_data.edges:
            edge_keys = {self.edge_key_extractor(e) for e in incoming_data.edges}
            self._edge_memory.sync_index(upserted_keys=edge_keys)

    # ==================== Extraction Pipeline ====================

    def _extract_data(self, text: str) -> AutoGraphSchema[NodeSchema, EdgeSchema]:
        """Main extraction logic dispatcher.

        Args:
            text: Input text to extract graph from.

        Returns:
            Extracted and validated graph.
        """
        if self.extraction_mode == "one_stage":
            raw_graph = self._extract_data_by_one_stage(text)
        elif self.extraction_mode == "two_stage":
            raw_graph = self._extract_data_by_two_stage(text)
        else:
            raise ValueError(f"Invalid extraction_mode: {self.extraction_mode}")

        # Prune dangling edges to ensure graph consistency
        return self._prune_dangling_edges(raw_graph)

    def _extract_data_by_one_stage(
        self, text: str
    ) -> AutoGraphSchema[NodeSchema, EdgeSchema]:
        """Extract nodes and edges simultaneously using single LLM call.

        Args:
            text: Input text.

        Returns:
            Raw extracted graph data.
        """
        logger.debug("stage=one_stage_start mode=%s", self.extraction_mode)

        if len(text) <= self.chunk_size:
            logger.debug("stage=one_stage_single_invoke")
            graph = self._invoke_safe(
                self.data_extractor, {"source_text": text}, stage="one_stage"
            )
            graph_list = self._filter_none_results(
                [graph],
                default_factory=lambda: self.graph_schema(nodes=[], edges=[]),
            )
        else:
            chunks = self.text_splitter.split_text(text)
            logger.debug("stage=one_stage_split num_chunks=%d", len(chunks))
            inputs = [{"source_text": chunk} for chunk in chunks]
            logger.debug(
                "stage=one_stage_batch_start max_concurrency=%d", self.max_workers
            )
            graph_list = self._batch_safe(
                self.data_extractor, inputs, stage="one_stage"
            )
            graph_list = self._filter_none_results(
                graph_list,
                default_factory=lambda: self.graph_schema(nodes=[], edges=[]),
            )
            logger.debug("stage=one_stage_batch_complete graphs=%d", len(graph_list))

        logger.debug("stage=one_stage_merge_start")
        # Provenance: record the raw (pre-merge) chunk results under the
        # pending source id (no-op when parse/feed_text had no source_id).
        self._record_extraction_source(
            self._pending_source_id,
            [node for graph in graph_list for node in graph.nodes],
            [edge for graph in graph_list for edge in graph.edges],
        )
        result = self.merge_batch_data(graph_list)
        logger.debug(
            "stage=one_stage_merge_complete nodes=%d edges=%d",
            len(result.nodes),
            len(result.edges),
        )
        return result

    def _extract_data_by_two_stage(
        self, text: str
    ) -> AutoGraphSchema[NodeSchema, EdgeSchema]:
        """Extract nodes first, then edges with node context (batch processing).

        Process:
        1. Split text into chunks.
        2. Batch extract nodes for all chunks.
        3. Batch extract edges for all chunks (using chunk-specific nodes as context).
        4. Construct partial graphs (tuples of nodes/edges).
        5. Merge all partial graphs into one global graph.

        Args:
            text: Input text.

        Returns:
            Extracted and validated graph.
        """
        logger.debug("stage=two_stage_start mode=%s", self.extraction_mode)

        # 1. Prepare chunks
        if len(text) <= self.chunk_size:
            chunks = [text]
        else:
            chunks = self.text_splitter.split_text(text)
        logger.debug("stage=two_stage_chunks num_chunks=%d", len(chunks))

        # 2. Batch Extract Nodes (returns List[NodeListSchema] + per-chunk failure mask)
        logger.debug("stage=two_stage_node_extraction_start")
        chunk_node_lists, node_failed = self._extract_nodes_batch(chunks)
        total_nodes = sum(len(nl.items) for nl in chunk_node_lists)
        logger.debug(
            "stage=two_stage_node_extraction_complete chunks=%d total_nodes=%d",
            len(chunk_node_lists),
            total_nodes,
        )

        # 3. Batch Extract Edges (Context-aware, returns List[EdgeListSchema]).
        # Chunks whose node extraction failed are skipped — do not prompt the
        # LLM with an empty node list. Results are padded back to the full
        # chunk length because merge_batch_data zips the node/edge lists.
        logger.debug("stage=two_stage_edge_extraction_start")
        edge_indices = [i for i, failed in enumerate(node_failed) if not failed]
        edge_results = (
            self._extract_edges_batch(
                [chunks[i] for i in edge_indices],
                [chunk_node_lists[i] for i in edge_indices],
            )
            if edge_indices
            else []
        )
        pending_edges = iter(edge_results)
        chunk_edge_lists = [
            next(pending_edges) if not failed else self.edge_list_schema(items=[])
            for failed in node_failed
        ]
        total_edges = sum(len(el.items) for el in chunk_edge_lists)
        logger.debug(
            "stage=two_stage_edge_extraction_complete chunks=%d total_edges=%d",
            len(chunk_edge_lists),
            total_edges,
        )

        # 4. Construct Partial Graphs (Tuple format for merge optimization)
        partial_graphs = (
            [node_list.items for node_list in chunk_node_lists],
            [edge_list.items for edge_list in chunk_edge_lists],
        )

        # Provenance: record the raw (pre-merge) node/edge results under the
        # pending source id (no-op when parse/feed_text had no source_id).
        self._record_extraction_source(
            self._pending_source_id,
            [node for node_list in chunk_node_lists for node in node_list.items],
            [edge for edge_list in chunk_edge_lists for edge in edge_list.items],
        )

        # 5. Global Merge (passes tuples to merge_batch_data)
        logger.debug("stage=two_stage_merge_start")
        result = self.merge_batch_data(partial_graphs)
        logger.debug(
            "stage=two_stage_merge_complete nodes=%d edges=%d",
            len(result.nodes),
            len(result.edges),
        )
        return result

    def _extract_nodes_batch(
        self, chunks: list[str]
    ) -> tuple[list[NodeListSchema[NodeSchema]], list[bool]]:
        """Batch extract nodes from multiple text chunks.

        Args:
            chunks: List of text chunks.

        Returns:
            Tuple of (node list schemas aligned with chunks, per-chunk failure
            mask where True marks a chunk whose node extraction failed).
        """
        inputs = [{"source_text": chunk} for chunk in chunks]
        results = self._batch_safe(self.node_extractor, inputs, stage="two_stage_nodes")
        node_failed = [r is None for r in results]
        node_lists = self._filter_none_results(
            results,
            default_factory=lambda: self.node_list_schema(items=[]),
        )
        return node_lists, node_failed

    def _extract_edges_batch(
        self, chunks: list[str], node_lists: list[NodeListSchema[NodeSchema]]
    ) -> list[EdgeListSchema[EdgeSchema]]:
        """Batch extract edges using corresponding node lists as context.

        Args:
            chunks: List of text chunks.
            node_lists: List of NodeListSchema objects (one per chunk).

        Returns:
            List of EdgeListSchema objects with extracted edges.
        """
        inputs = []
        for chunk, node_list in zip(chunks, node_lists):
            nodes = node_list.items if node_list else []
            if not nodes:
                known_nodes = "No specific entities identified in this chunk."
            else:
                node_keys = [self.node_key_extractor(n) for n in nodes]
                known_nodes = "\n- ".join(node_keys)

            inputs.append({"source_text": chunk, "known_nodes": known_nodes})

        results = self._batch_safe(self.edge_extractor, inputs, stage="two_stage_edges")
        return self._filter_none_results(
            results,
            default_factory=lambda: self.edge_list_schema(items=[]),
        )

    def _prune_dangling_edges(
        self, graph: AutoGraphSchema[NodeSchema, EdgeSchema]
    ) -> AutoGraphSchema[NodeSchema, EdgeSchema]:
        """Prune edges that connect to non-existent nodes (Consistency Check).

        Ensures graph consistency by removing any edges where either endpoint
        (source or target) does not exist in the node list.

        Args:
            graph: Raw graph that may contain dangling edges.

        Returns:
            Graph with only valid edges (endpoints must strictly exist in nodes).
        """
        valid_nodes = graph.nodes
        valid_node_keys = {self.node_key_extractor(n) for n in valid_nodes}

        refined_edges = []
        dropped_count = 0

        for edge in graph.edges:
            src_key, dst_key = self.nodes_in_edge_extractor(edge)

            # Check if both endpoints exist
            src_exists = src_key in valid_node_keys or src_key in self._node_memory.keys
            dst_exists = dst_key in valid_node_keys or dst_key in self._node_memory.keys

            if src_exists and dst_exists:
                refined_edges.append(edge)
            else:
                dropped_count += 1
                logger.debug(
                    f"Pruning dangling edge: {src_key} -> {dst_key} "
                    f"(src_exists={src_exists}, dst_exists={dst_exists})"
                )

        if dropped_count > 0:
            logger.info(
                f"Pruned {dropped_count} dangling edges to ensure graph consistency."
            )

        return self.graph_schema(nodes=valid_nodes, edges=refined_edges)

    # merge / index / search: GraphIndexMixin

    def chat(
        self,
        query: str,
        top_k: int | None = None,
        top_k_nodes: int = 3,
        top_k_edges: int = 3,
        *,
        source_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> AIMessage:
        """Performs a chat-like interaction using graph knowledge.

        Retrieves relevant nodes and/or edges based on the query and retrieval counts,
        formats them into a structured context with clear headers, and generates an answer.

        Args:
            query: User query string.
            top_k: Number of relevant items to retrieve for both nodes and edges (default: 3).
                If provided, sets both top_k_nodes and top_k_edges to this value.
            top_k_nodes: Number of relevant nodes to retrieve (default: 3). Set to 0 to disable node context.
            top_k_edges: Number of relevant edges to retrieve (default: 3). Set to 0 to disable edge context.
            source_ids: Optional scope — only nodes/edges contributed by these source documents.
            tags: Optional scope — only nodes/edges from sources carrying these tags.

        Returns:
            An AIMessage object containing the LLM-generated response.
            Access the text content via response.content.

        Example:
            >>> # Chat using 5 nodes and 2 edges as context
            >>> response = ka.chat("What is X?", top_k_nodes=5, top_k_edges=2)
            >>> print(response.content)  # Print the generated answer
        """
        if top_k is not None:
            top_k_nodes = top_k
            top_k_edges = top_k

        if top_k_nodes <= 0 and top_k_edges <= 0:
            raise ValueError(
                "At least one of top_k_nodes or top_k_edges must be positive."
            )

        context_parts = []

        # Step 2: Retrieve and format nodes context
        nodes = []
        if top_k_nodes > 0:
            nodes = self.search_nodes(
                query, top_k=top_k_nodes, source_ids=source_ids, tags=tags
            )
            if nodes:
                context_parts.append("=== Relevant Nodes ===")
                for node in nodes:
                    assert isinstance(node, BaseModel), (
                        "Node must be a Pydantic BaseModel"
                    )
                    context_parts.append(node.model_dump_json(indent=2))

        # Step 3: Retrieve and format edges context
        edges = []
        if top_k_edges > 0:
            edges = self.search_edges(
                query, top_k=top_k_edges, source_ids=source_ids, tags=tags
            )
            if edges:
                context_parts.append("=== Relevant Edges ===")
                for edge in edges:
                    assert isinstance(edge, BaseModel), (
                        "Edge must be a Pydantic BaseModel"
                    )
                    context_parts.append(edge.model_dump_json(indent=2))

        # Step 4: Combine context or use fallback
        if not context_parts:
            context = "No relevant information found in the knowledge abstract."
        else:
            context = "\n\n".join(context_parts)

        # Step 5: Invoke LLM with structured context
        qa_prompt = ChatPromptTemplate.from_template(
            "Based on the following Graph Knowledge, answer the user's question.\n\n"
            "{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )

        qa_chain = qa_prompt | self.llm_client
        response = qa_chain.invoke({"context": context, "question": query})

        # Step 6: Inject retrieved nodes and edges into response metadata
        if not response.additional_kwargs:
            response.additional_kwargs = {}
        response.additional_kwargs["retrieved_nodes"] = nodes
        response.additional_kwargs["retrieved_edges"] = edges

        return response

    # ==================== Serialization ====================

    def dump_index(self, folder_path: str | Path) -> None:
        """Save indices to disk."""
        folder = Path(folder_path)
        folder.mkdir(parents=True, exist_ok=True)

        # Save node index
        node_index_path = folder / "node_index"
        node_index_path.mkdir(exist_ok=True)
        try:
            self._node_memory.dump_index(str(node_index_path))
        except Exception as e:
            logger.warning(f"Failed to save node index: {e}")

        # Save edge index
        edge_index_path = folder / "edge_index"
        edge_index_path.mkdir(exist_ok=True)
        try:
            self._edge_memory.dump_index(str(edge_index_path))
        except Exception as e:
            logger.warning(f"Failed to save edge index: {e}")

    def load_index(self, folder_path: str | Path) -> None:
        """Load indices from disk."""
        folder = Path(folder_path)

        # Load node index
        node_index_path = folder / "node_index"
        if node_index_path.exists():
            try:
                self._node_memory.load_index(str(node_index_path))
            except Exception as e:
                logger.warning(f"Failed to load node index: {e}")

        # Load edge index
        edge_index_path = folder / "edge_index"
        if edge_index_path.exists():
            try:
                self._edge_memory.load_index(str(edge_index_path))
            except Exception as e:
                logger.warning(f"Failed to load edge index: {e}")

    def show(
        self,
        node_label_extractor: Callable[[NodeSchema], str] | None = None,
        edge_label_extractor: Callable[[EdgeSchema], str] | None = None,
        *,
        top_k_nodes_for_search: int = 3,
        top_k_edges_for_search: int = 3,
        top_k_nodes_for_chat: int = 3,
        top_k_edges_for_chat: int = 3,
    ) -> None:
        """Visualize the graph using OntoSight.

        Args:
            node_label_extractor: Optional function to extract label from node for visualization.
                If not provided, uses the one from __init__.
            edge_label_extractor: Optional function to extract label from edge for visualization.
                If not provided, uses the one from __init__.
            top_k_nodes_for_search: Number of nodes to retrieve for search callback (default: 3).
            top_k_edges_for_search: Number of edges to retrieve for search callback (default: 3).
            top_k_nodes_for_chat: Number of nodes to retrieve for chat callback (default: 3).
            top_k_edges_for_chat: Number of edges to retrieve for chat callback (default: 3).
        """
        if node_label_extractor is None:
            node_label_extractor = self._node_label_extractor
        if edge_label_extractor is None:
            edge_label_extractor = self._edge_label_extractor

        if self._node_memory.has_index() and self._edge_memory.has_index():
            logger.info(
                "Visualizing graph with search and chat capabilities (indices detected)."
            )

            def search_callback(query: str) -> None:
                # search() may return (nodes, edges) or, in subclasses like
                # Graph_RAG, (nodes, edges, context); ontosight only wants the
                # first two.
                result = self.search(
                    query,
                    top_k_nodes=top_k_nodes_for_search,
                    top_k_edges=top_k_edges_for_search,
                )
                return result[0], result[1]

            def chat_callback(question: str) -> None:
                response = self.chat(
                    question,
                    top_k_nodes=top_k_nodes_for_chat,
                    top_k_edges=top_k_edges_for_chat,
                )
                content = response.content
                retrieved_nodes = response.additional_kwargs.get("retrieved_nodes", [])
                retrieved_edges = response.additional_kwargs.get("retrieved_edges", [])
                return content, (retrieved_nodes, retrieved_edges)
        else:
            logger.info(
                "Visualizing graph without search and chat capabilities (no indices detected)."
            )
            search_callback = None
            chat_callback = None

        view_graph(
            node_list=self.nodes,
            edge_list=self.edges,
            node_schema=self.node_schema,
            edge_schema=self.edge_schema,
            node_id_extractor=self.node_key_extractor,
            node_ids_in_edge_extractor=self.nodes_in_edge_extractor,
            node_label_extractor=node_label_extractor,
            edge_label_extractor=edge_label_extractor,
            on_search=search_callback,
            on_chat=chat_callback,
        )

    # ==================== Obsidian Export ====================

    def export_obsidian(
        self,
        folder_path: str | Path,
        *,
        node_label_extractor: Callable[[NodeSchema], str] | None = None,
        edge_label_extractor: Callable[[EdgeSchema], str] | None = None,
        vault_name: str = "Knowledge Vault",
        include_index: bool = True,
        overwrite: bool = False,
    ) -> Path:
        """Export the graph as an Obsidian vault.

        Writes one Markdown note per node (fields stored as YAML front-matter)
        and renders every edge as an internal ``[[wikilink]]`` under its source
        note. The resulting folder can be opened directly in Obsidian, where the
        graph view reflects the extracted knowledge structure.

        Args:
            folder_path: Destination vault directory.
            node_label_extractor: Optional node -> display title. Defaults to the
                one from ``__init__``, then common fields, then the node id.
            edge_label_extractor: Optional edge -> relationship label. Defaults to
                the one from ``__init__``, then common fields, then "related to".
            vault_name: Title used for the generated index note.
            include_index: Whether to write an index/map-of-content note.
            overwrite: Allow writing into an existing, non-empty directory.

        Returns:
            The vault directory :class:`~pathlib.Path`.
        """
        from hyperextract.utils.obsidian import export_to_obsidian

        if node_label_extractor is None:
            node_label_extractor = self._node_label_extractor
        if edge_label_extractor is None:
            edge_label_extractor = self._edge_label_extractor

        return export_to_obsidian(
            nodes=self.nodes,
            edges=self.edges,
            node_id_extractor=self.node_key_extractor,
            incident_nodes_extractor=self.nodes_in_edge_extractor,
            folder_path=folder_path,
            node_label_extractor=node_label_extractor,
            edge_label_extractor=edge_label_extractor,
            vault_name=vault_name,
            include_index=include_index,
            overwrite=overwrite,
        )
