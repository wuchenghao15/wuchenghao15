"""
Episodic subgraph projection

Project subgraph of Episodic MemorySpace from graph database for retrieval.
"""

from typing import Dict, List, Optional

from m_flow.shared.logging_utils import get_logger, ERROR
from m_flow.knowledge.graph_ops.exceptions.exceptions import ConceptNotFoundError
from m_flow.adapters.graph import get_graph_provider
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
from m_flow.core.domain.models.memory_space import MemorySpace

from .config import EpisodicConfig, get_episodic_config

logger = get_logger(level=ERROR)


async def get_episodic_memory_fragment(
    episodic_nodeset_name: Optional[str] = None,
    properties_to_project: Optional[List[str]] = None,
    relevant_ids_to_filter: Optional[List[str]] = None,
    triplet_distance_penalty: Optional[float] = None,
    strict_nodeset_filtering: Optional[bool] = None,
    config: Optional[EpisodicConfig] = None,
) -> MemoryGraph:
    """
    Project Episodic subgraph.

    Args:
        episodic_nodeset_name: MemorySpace name (default read from config)
        properties_to_project: Node properties to project
        relevant_ids_to_filter: List of IDs for filtering
        triplet_distance_penalty: Distance penalty value
        strict_nodeset_filtering: Whether to strictly filter
        config: Config object (optional, auto-loaded if not provided)

    Returns:
        MemoryGraph: Projected subgraph
    """
    if config is None:
        config = get_episodic_config()

    # Use config default values
    nodeset_name = episodic_nodeset_name or config.episodic_nodeset_name
    props = properties_to_project or config.properties_to_project
    penalty = triplet_distance_penalty if triplet_distance_penalty is not None else config.triplet_distance_penalty
    strict = strict_nodeset_filtering if strict_nodeset_filtering is not None else config.strict_nodeset_filtering

    memory_fragment = MemoryGraph()

    try:
        graph_engine = await get_graph_provider()

        try:
            await memory_fragment.project_graph_from_db(
                graph_engine,
                node_properties_to_project=props,
                edge_properties_to_project=["relationship_name", "edge_text"],
                node_type=MemorySpace,
                node_name=[nodeset_name],
                relevant_ids_to_filter=relevant_ids_to_filter,
                triplet_distance_penalty=penalty,
                strict_nodeset_filtering=strict,
            )
        except TypeError:
            # Fallback: old version doesn't support strict_nodeset_filtering
            await memory_fragment.project_graph_from_db(
                graph_engine,
                node_properties_to_project=props,
                edge_properties_to_project=["relationship_name", "edge_text"],
                node_type=MemorySpace,
                node_name=[nodeset_name],
                relevant_ids_to_filter=relevant_ids_to_filter,
                triplet_distance_penalty=penalty,
            )

    except ConceptNotFoundError:
        pass
    except Exception as e:
        logger.error(f"Error during episodic memory fragment creation: {str(e)}")

    return memory_fragment


def compute_best_node_distances(node_distances: Dict[str, list]) -> Dict[str, float]:
    """
    When the same node id is hit in multiple collections, take min(score).

    Avoids ranking jitter caused by overwrites.

    Args:
        node_distances: {collection_name: [VectorSearchHit, ...]}

    Returns:
        Dict[str, float]: {node_id: best_score}
    """
    best: Dict[str, float] = {}

    for collection_name, scored_results in (node_distances or {}).items():
        if collection_name == "RelationType_relationship_name":
            continue
        if not scored_results:
            continue

        for r in scored_results:
            rid = str(getattr(r, "id", "") or "")
            if not rid:
                continue
            score = float(getattr(r, "score", 1.0))
            prev = best.get(rid)
            best[rid] = score if prev is None else min(prev, score)

    return best
