import asyncio
import time
from typing import List, Optional, Type

from m_flow.shared.logging_utils import get_logger, ERROR
from m_flow.knowledge.graph_ops.exceptions.exceptions import ConceptNotFoundError
from m_flow.adapters.vector.exceptions import CollectionNotFoundError
from m_flow.adapters.graph import get_graph_provider
from m_flow.adapters.vector import get_vector_provider
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge

# Time enhancement imports
from m_flow.retrieval.time.query_time_parser import parse_query_time, QueryTimeInfo
from m_flow.retrieval.time.time_bonus import compute_time_match, TimeBonusConfig

logger = get_logger(level=ERROR)


def format_triplets(edges):
    logger.debug("Formatting %d triplets", len(edges))

    def filter_attributes(obj, attributes):
        """Helper function to filter out non-None properties, including nested dicts."""
        result = {}
        for attr in attributes:
            value = getattr(obj, attr, None)
            if value is not None:
                # If the value is a dict, extract relevant keys from it
                if isinstance(value, dict):
                    nested_values = {k: v for k, v in value.items() if k in attributes and v is not None}
                    result[attr] = nested_values
                else:
                    result[attr] = value
        return result

    triplets = []
    for edge in edges:
        node1 = edge.node1
        node2 = edge.node2
        edge_attributes = edge.attributes
        node1_attributes = node1.attributes
        node2_attributes = node2.attributes

        # Filter only non-None properties
        node1_info = {key: value for key, value in node1_attributes.items() if value is not None}
        node2_info = {key: value for key, value in node2_attributes.items() if value is not None}
        edge_info = {key: value for key, value in edge_attributes.items() if value is not None}

        # Create the formatted triplet
        triplet = f"Node1: {node1_info}\nEdge: {edge_info}\nNode2: {node2_info}\n\n\n"
        triplets.append(triplet)

    return "".join(triplets)


async def get_memory_fragment(
    properties_to_project: Optional[List[str]] = None,
    node_type: Optional[Type] = None,
    node_name: Optional[List[str]] = None,
    relevant_ids_to_filter: Optional[List[str]] = None,
    triplet_distance_penalty: Optional[float] = 3.5,
) -> MemoryGraph:
    """Creates and initializes a MemoryGraph memory fragment with optional property projections."""
    if properties_to_project is None:
        # Add summary to align with Episodic configuration
        # Include time fields for Episode time display in LLM context
        properties_to_project = [
            "id",
            "description",
            "name",
            "type",
            "text",
            "summary",
            # Time fields for Episode time display
            "mentioned_time_start_ms",
            "mentioned_time_end_ms",
            "mentioned_time_text",
            "created_at",
        ]

    memory_fragment = MemoryGraph()

    try:
        graph_engine = await get_graph_provider()

        await memory_fragment.project_graph_from_db(
            graph_engine,
            node_properties_to_project=properties_to_project,
            edge_properties_to_project=["relationship_name", "edge_text"],
            node_type=node_type,
            node_name=node_name,
            relevant_ids_to_filter=relevant_ids_to_filter,
            triplet_distance_penalty=triplet_distance_penalty,
        )

    except ConceptNotFoundError:
        # This is expected behavior - continue with empty fragment
        pass
    except Exception as e:
        logger.error(f"Error during memory fragment creation: {str(e)}")
        # Still return the fragment even if projection failed
        pass

    return memory_fragment


async def fine_grained_triplet_search(
    query: str,
    top_k: int = 5,
    collections: Optional[List[str]] = None,
    properties_to_project: Optional[List[str]] = None,
    memory_fragment: Optional[MemoryGraph] = None,
    node_type: Optional[Type] = None,
    node_name: Optional[List[str]] = None,
    wide_search_top_k: Optional[int] = 100,
    triplet_distance_penalty: Optional[float] = 3.5,
    memory_type_filter: Optional[str] = None,
    # Time enhancement
    enable_time_bonus: bool = True,
    time_bonus_max: float = 0.06,
    time_score_floor: float = 0.08,
    time_conf_min: float = 0.4,
) -> List[Edge]:
    """
    Performs a brute force search to retrieve the top triplets from the graph.

    Args:
        query (str): The search query.
        top_k (int): The number of top results to retrieve.
        collections (Optional[List[str]]): List of collections to query.
        properties_to_project (Optional[List[str]]): List of properties to project.
        memory_fragment (Optional[MemoryGraph]): Existing memory fragment to reuse.
        node_type: node type to filter
        node_name: node name to filter
        wide_search_top_k (Optional[int]): Number of initial elements to retrieve from collections
        triplet_distance_penalty (Optional[float]): Default distance penalty in graph projection
        memory_type_filter (Optional[str]): Filter entities by memory type.
            - None: Return all entities (default, backward compatible)
            - "atomic": Only return atomic entities (from Atomic Episodes)
            - "episodic": Only return episodic entities (from Episodic Episodes)
            Note: Both atomic and episodic entities now come from Episode → Entity structure,
            distinguished by the Entity.memory_type field which inherits from Episode.memory_type.
        enable_time_bonus (bool): Phase 1 time enhancement - whether to enable time bonus
        time_bonus_max (float): Maximum time bonus
        time_conf_min (float): Time confidence threshold

    Returns:
        list: The top triplet results.
    """
    if not query or not isinstance(query, str):
        raise ValueError("M-Flow search requires a non-blank query string.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    # Validate memory_type_filter
    if memory_type_filter is not None:
        if memory_type_filter not in ("atomic", "episodic"):
            raise ValueError(f"memory_type_filter must be 'atomic', 'episodic', or None, got: '{memory_type_filter}'")

    # Setting wide search limit based on the parameters
    non_global_search = node_name is None

    wide_search_limit = wide_search_top_k if non_global_search else None

    if collections is None:
        # Simplified collections: Episode_summary replaces ContentFragment_text
        # RelationType_relationship_name auto-added below (indexes edge_text)
        collections = [
            "Episode_summary",
            "Entity_name",
            "Concept_name",  # Backward compat: old data may use this collection
        ]

    if "RelationType_relationship_name" not in collections:
        collections.append("RelationType_relationship_name")

    # Time enhancement: parse time expressions in query
    time_info: Optional[QueryTimeInfo] = None
    if enable_time_bonus:
        time_info = parse_query_time(query)
        # Use query with time stripped (avoid date numbers interfering with vector retrieval)
        if time_info.query_wo_time:
            query = time_info.query_wo_time

    try:
        vector_engine = get_vector_provider()
    except Exception as e:
        logger.error("Failed to initialize vector engine: %s", e)
        raise RuntimeError("Initialization error") from e

    query_vector = (await vector_engine.embedding_engine.embed_text([query]))[0]

    # Check if vector engine supports where_filter parameter
    # Only LanceDB currently supports this feature
    import inspect

    try:
        search_sig = inspect.signature(vector_engine.search)
        supports_where_filter = "where_filter" in search_sig.parameters
    except (ValueError, TypeError):
        # Handle mock objects or other non-inspectable callables
        supports_where_filter = False

    # Warn if memory_type_filter is requested but not supported
    effective_memory_type_filter = memory_type_filter
    if memory_type_filter and not supports_where_filter:
        logger.warning(
            f"Vector engine {type(vector_engine).__name__} does not support where_filter. "
            f"memory_type_filter='{memory_type_filter}' will be ignored. "
            f"Consider using LanceDB for memory_type filtering support."
        )
        effective_memory_type_filter = None

    async def search_in_collection(collection_name: str):
        try:
            # Apply memory_type filter only to Entity/Entity name collections
            # and only if the vector engine supports it
            if (
                effective_memory_type_filter
                and collection_name in ("Entity_name", "Concept_name")
                and supports_where_filter
            ):
                where_filter = f"payload.memory_type = '{effective_memory_type_filter}'"
                return await vector_engine.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=wide_search_limit,
                    where_filter=where_filter,
                )
            else:
                # Standard search without filter
                return await vector_engine.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=wide_search_limit,
                )
        except CollectionNotFoundError:
            return []

    try:
        start_time = time.time()

        results = await asyncio.gather(*[search_in_collection(collection_name) for collection_name in collections])

        if all(not item for item in results):
            return []

        # Final statistics
        vector_collection_search_time = time.time() - start_time
        logger.info(
            f"Vector collection retrieval completed: Retrieved distances from {sum(1 for res in results if res)} collections in {vector_collection_search_time:.2f}s"
        )

        node_distances = {collection: result for collection, result in zip(collections, results)}

        edge_distances = node_distances.get("RelationType_relationship_name", None)

        if wide_search_limit is not None:
            relevant_ids_to_filter = list(
                {
                    str(getattr(scored_node, "id"))
                    for collection_name, score_collection in node_distances.items()
                    if collection_name != "RelationType_relationship_name"
                    and isinstance(score_collection, (list, tuple))
                    for scored_node in score_collection
                    if getattr(scored_node, "id", None)
                }
            )
        else:
            relevant_ids_to_filter = None

        if memory_fragment is None:
            memory_fragment = await get_memory_fragment(
                properties_to_project=properties_to_project,
                node_type=node_type,
                node_name=node_name,
                relevant_ids_to_filter=relevant_ids_to_filter,
                triplet_distance_penalty=triplet_distance_penalty,
            )

        await memory_fragment.map_vector_distances_to_graph_nodes(node_distances=node_distances)
        await memory_fragment.map_vector_distances_to_graph_edges(edge_distances=edge_distances)

        # Fetch more results for re-ranking after time enhancement
        fetch_k = top_k * 2 if (time_info and time_info.has_time) else top_k
        results = await memory_fragment.calculate_top_triplet_importances(k=fetch_k)

        # Time enhancement: apply time bonus to results and re-rank
        if time_info and time_info.has_time and time_info.confidence >= time_conf_min:
            time_cfg = TimeBonusConfig(
                enabled=True,
                bonus_max=time_bonus_max,
                score_floor=time_score_floor,
                query_conf_min=time_conf_min,
            )

            # Compute time bonus for each edge
            for edge in results:
                n1_attrs = edge.node1.attributes if edge.node1 else {}
                n2_attrs = edge.node2.attributes if edge.node2 else {}

                bonus1 = compute_time_match({"payload": n1_attrs}, time_info, time_cfg)
                bonus2 = compute_time_match({"payload": n2_attrs}, time_info, time_cfg)
                best_bonus = max(bonus1.bonus, bonus2.bonus)

                if best_bonus > 0:
                    current_importance = edge.attributes.get("triplet_importance", 1.0)
                    # Lower importance is better, so subtract bonus
                    edge.attributes["triplet_importance"] = max(time_score_floor, current_importance - best_bonus)

            # Re-rank
            results.sort(key=lambda e: e.attributes.get("triplet_importance", 1.0))
            results = results[:top_k]

        return results

    except CollectionNotFoundError:
        return []
    except Exception as error:
        logger.error(
            "M-Flow brute-force triplet scan failed for query: %s — %s",
            query,
            error,
        )
        raise error
