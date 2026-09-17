"""
Unrestricted Search Implementation
==================================

Search functionality for environments without access control enabled.
Provides a simplified search path that doesn't require dataset permissions.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Type, Union

from m_flow.adapters.graph import get_graph_provider
from m_flow.data.models.Dataset import Dataset
from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.search.types import RecallMode
from m_flow.shared.logging_utils import get_logger

from .get_recall_mode_tools import get_recall_mode_tools

_logger = get_logger()


async def no_access_control_search(
    query_type: RecallMode,
    query_text: str,
    system_prompt_path: str = "direct_answer.txt",
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: bool = False,
    only_context: bool = False,
    session_id: Optional[str] = None,
    wide_search_top_k: Optional[int] = 100,
    triplet_distance_penalty: Optional[float] = 3.5,
    # Episodic retrieval parameters (Phase 0.4)
    enable_hybrid_search: Optional[bool] = None,
    enable_time_bonus: Optional[bool] = None,
    edge_miss_cost: Optional[float] = None,
    hop_cost: Optional[float] = None,
    full_number_match_bonus: Optional[float] = None,
    enable_adaptive_weights: Optional[bool] = None,
    # Episodic output control
    display_mode: Optional[str] = None,
    max_facets_per_episode: Optional[int] = None,
    max_points_per_facet: Optional[int] = None,
    # Collection control (TRIPLET / EPISODIC)
    collections: Optional[List[str]] = None,
    # Procedural inclusion for TRIPLET mode
) -> Tuple[Any, Union[str, List[Edge]], List[Dataset]]:
    """
    Execute search without permission checks.

    This function is used when ENABLE_BACKEND_ACCESS_CONTROL is disabled.
    It provides direct access to search functionality without verifying
    dataset permissions.

    Parameters
    ----------
    query_type : RecallMode
        Search strategy to employ.
    query_text : str
        User's search query.
    system_prompt_path : str
        Path to system prompt template.
    system_prompt : str | None
        Custom system prompt override.
    top_k : int
        Maximum results to return.
    node_type : Type | None
        Filter by node type.
    node_name : list[str] | None
        Filter by node names.
    save_interaction : bool
        Persist the interaction.
    only_context : bool
        Return context only, skip completion.
    session_id : str | None
        Session for conversation continuity.
    wide_search_top_k : int | None
        Broader retrieval before reranking.
    triplet_distance_penalty : float | None
        Graph distance penalty factor.
    enable_hybrid_search : bool | None
        Enable hybrid search for EPISODIC mode.
    enable_time_bonus : bool | None
        Enable time-based relevance bonus.
    edge_miss_cost : float | None
        Cost for missing edges in graph traversal.
    hop_cost : float | None
        Cost per hop in graph traversal.
    full_number_match_bonus : float | None
        Bonus for exact number matches.
    enable_adaptive_weights : bool | None
        Enable adaptive scoring weights.

    Returns
    -------
    tuple
        (result, context, datasets) - datasets is always empty list.
    """
    # Initialize search tools
    tools = await get_recall_mode_tools(
        query_type=query_type,
        query_text=query_text,
        system_prompt_path=system_prompt_path,
        system_prompt=system_prompt,
        top_k=top_k,
        node_type=node_type,
        node_name=node_name,
        save_interaction=save_interaction,
        wide_search_top_k=wide_search_top_k,
        triplet_distance_penalty=triplet_distance_penalty,
        enable_hybrid_search=enable_hybrid_search,
        enable_time_bonus=enable_time_bonus,
        edge_miss_cost=edge_miss_cost,
        hop_cost=hop_cost,
        full_number_match_bonus=full_number_match_bonus,
        enable_adaptive_weights=enable_adaptive_weights,
        display_mode=display_mode,
        max_facets_per_episode=max_facets_per_episode,
        max_points_per_facet=max_points_per_facet,
        collections=collections,
    )

    # Check graph state
    graph_db = await get_graph_provider()
    if await graph_db.is_empty():
        _logger.warning("Searching an empty knowledge graph")

    # Execute based on available tools
    if len(tools) == 2:
        completion_fn, context_fn = tools

        if only_context:
            ctx = await context_fn(query_text)
            return None, ctx, []

        ctx = await context_fn(query_text)
        answer = await completion_fn(query_text, ctx, session_id=session_id)
        return answer, ctx, []

    # Single tool mode
    single_tool = tools[0]
    answer = await single_tool(query_text)
    return answer, "", []
