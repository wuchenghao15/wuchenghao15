"""
Procedural Memory Fragment - Project Procedural subgraph

Follows the pattern of episodic's get_episodic_memory_fragment,
used for isolated subgraph projection of Procedural MemorySpace.

Triplet structure (new, no Pack):
- Procedure (anchor) → has_context_point → ContextPoint
- Procedure (anchor) → has_key_point → KeyPoint

Legacy structure (old data, backward compat):
- Procedure → ContextPack → ContextPoint
- Procedure → StepsPack → StepPoint
"""

from typing import List, Optional

from m_flow.shared.logging_utils import get_logger, ERROR
from m_flow.knowledge.graph_ops.exceptions.exceptions import ConceptNotFoundError
from m_flow.adapters.graph import get_graph_provider
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
from m_flow.core.domain.models.memory_space import MemorySpace

logger = get_logger(level=ERROR)


async def get_procedural_memory_fragment(
    procedural_nodeset_name: str = "Procedural",
    properties_to_project: Optional[List[str]] = None,
    relevant_ids_to_filter: Optional[List[str]] = None,
    triplet_distance_penalty: float = 3.5,
    strict_nodeset_filtering: bool = True,
) -> MemoryGraph:
    """
    Project procedural subgraph (MemorySpace isolation).

    Completely follows the pattern of get_episodic_memory_fragment, used for:
    - Projecting Procedural MemorySpace during retrieval
    - Two-hop closure (Procedure -> Pack -> Point)
    - Forced dual retrieval (context + steps)

    Args:
        procedural_nodeset_name: MemorySpace name, default "Procedural"
        properties_to_project: List of node properties to project
        relevant_ids_to_filter: List of IDs for filtering (limit projection scope)
        triplet_distance_penalty: Distance penalty value
        strict_nodeset_filtering: Whether to strictly filter MemorySpace

    Returns:
        MemoryGraph: Projected procedural subgraph
    """
    if properties_to_project is None:
        properties_to_project = [
            "id",
            "name",
            "type",
            # Procedure
            "summary",
            "signature",
            "search_text",
            "context_text",  # Display attribute (replaces ContextPack.anchor_text)
            "points_text",  # Display attribute (replaces StepsPack.anchor_text)
            "version",
            "status",
            "confidence",
            # Points
            "point_type",
            "point_index",  # New field name
            "step_number",
            "description",
            # Time
            "mentioned_time_start_ms",
            "mentioned_time_end_ms",
            "mentioned_time_confidence",
            # Generic (rendering fallback)
            "text",
            # Legacy (old Pack nodes, transition period)
            "anchor_text",
        ]

    memory_fragment = MemoryGraph()

    try:
        graph_engine = await get_graph_provider()

        # Compatibility: strict_nodeset_filtering parameter
        try:
            await memory_fragment.project_graph_from_db(
                graph_engine,
                node_properties_to_project=properties_to_project,
                edge_properties_to_project=["relationship_name", "edge_text"],
                node_type=MemorySpace,
                node_name=[procedural_nodeset_name],
                relevant_ids_to_filter=relevant_ids_to_filter,
                triplet_distance_penalty=triplet_distance_penalty,
                strict_nodeset_filtering=strict_nodeset_filtering,
            )
        except TypeError:
            # Fallback: old version doesn't support strict_nodeset_filtering
            await memory_fragment.project_graph_from_db(
                graph_engine,
                node_properties_to_project=properties_to_project,
                edge_properties_to_project=["relationship_name", "edge_text"],
                node_type=MemorySpace,
                node_name=[procedural_nodeset_name],
                relevant_ids_to_filter=relevant_ids_to_filter,
                triplet_distance_penalty=triplet_distance_penalty,
            )

    except ConceptNotFoundError:
        # Return empty graph when MemorySpace doesn't exist
        pass
    except Exception as e:
        logger.error(f"Error during procedural memory fragment creation: {str(e)}")
        pass

    return memory_fragment
