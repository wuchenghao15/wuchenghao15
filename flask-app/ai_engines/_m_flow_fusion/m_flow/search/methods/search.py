"""
M-flow Search Module
====================

Core search functionality providing both access-controlled and unrestricted
query modes. Supports multiple recall strategies including vector similarity,
graph traversal, and hybrid approaches.

This module coordinates:
- Query logging and telemetry
- Dataset permission verification
- Context retrieval and completion generation
- Result formatting for API consumers
"""

from __future__ import annotations

import json
import asyncio
from uuid import UUID
from typing import Any, List, Optional, Tuple, Type, Union

from fastapi.encoders import jsonable_encoder

from m_flow.adapters.graph import get_graph_provider
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.utils import send_telemetry
from m_flow.context_global_variables import (
    set_db_context,
    backend_access_control_enabled,
)
from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.search.types import (
    SearchResult,
    CombinedSearchResult,
    SearchResultDataset,
    RecallMode,
)
from m_flow.search.operations import log_query, log_result
from m_flow.auth.models import User
from m_flow.data.models import Dataset
from m_flow.data.methods.get_authorized_existing_datasets import (
    get_authorized_existing_datasets,
)
from m_flow import __version__ as m_flow_version

from .get_recall_mode_tools import get_recall_mode_tools
from .no_access_control_search import no_access_control_search
from ..utils.prepare_search_result import prepare_search_result

_logger = get_logger()


async def search(
    query_text: str,
    query_type: RecallMode,
    dataset_ids: Union[list[UUID], None],
    user: User,
    system_prompt_path: str = "direct_answer.txt",
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: bool = False,
    only_context: bool = False,
    use_combined_context: bool = False,
    session_id: Optional[str] = None,
    wide_search_top_k: Optional[int] = 100,
    triplet_distance_penalty: Optional[float] = 3.5,
    verbose: bool = False,
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
) -> Union[CombinedSearchResult, List[SearchResult]]:
    """
    Execute a semantic search across authorized datasets.

    This is the primary entry point for all search operations in M-flow.
    It handles permission checks, telemetry, and result formatting based
    on the configured access control mode.

    Parameters
    ----------
    query_text : str
        Natural language query to search for.
    query_type : RecallMode
        Search strategy (e.g., VECTOR, GRAPH, HYBRID).
    dataset_ids : list[UUID] | None
        Specific datasets to search, or None for all accessible.
    user : User
        Authenticated user performing the search.
    system_prompt_path : str
        Path to the system prompt template file.
    system_prompt : str | None
        Custom system prompt to override the template.
    top_k : int
        Maximum number of results to retrieve.
    node_type : Type | None
        Filter results by specific node type.
    node_name : list[str] | None
        Filter by node names.
    save_interaction : bool
        Whether to persist the query/response pair.
    only_context : bool
        Return raw context without LLM completion.
    use_combined_context : bool
        Merge contexts from multiple datasets before completion.
    session_id : str | None
        Session identifier for conversation continuity.
    wide_search_top_k : int | None
        Broader retrieval count before re-ranking.
    triplet_distance_penalty : float | None
        Penalty factor for graph distance calculations.
    verbose : bool
        Include detailed graph information in response.

    Returns
    -------
    CombinedSearchResult | list[SearchResult]
        Search results with optional graph metadata.

    Notes
    -----
    Dataset-level filtering requires ENABLE_BACKEND_ACCESS_CONTROL mode.
    """
    # Record query for analytics
    query_record = await log_query(query_text, query_type.value, user.id)

    # Emit telemetry event
    _emit_search_telemetry("STARTED", user)

    # Route to appropriate search implementation
    if backend_access_control_enabled():
        raw_results = await _authorized_search_impl(
            query_type=query_type,
            query_text=query_text,
            user=user,
            dataset_ids=dataset_ids,
            system_prompt_path=system_prompt_path,
            system_prompt=system_prompt,
            top_k=top_k,
            node_type=node_type,
            node_name=node_name,
            save_interaction=save_interaction,
            only_context=only_context,
            use_combined_context=use_combined_context,
            session_id=session_id,
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
    else:
        raw_results = [
            await no_access_control_search(
                query_type=query_type,
                query_text=query_text,
                system_prompt_path=system_prompt_path,
                system_prompt=system_prompt,
                top_k=top_k,
                node_type=node_type,
                node_name=node_name,
                save_interaction=save_interaction,
                only_context=only_context,
                session_id=session_id,
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
        ]

    _emit_search_telemetry("COMPLETED", user)

    # Persist result for analytics
    await _persist_search_result(query_record.id, raw_results, user.id, use_combined_context)

    # Format output based on mode
    if use_combined_context:
        return await _format_combined_result(raw_results)
    else:
        return await _format_standard_results(raw_results, only_context, verbose)


def _emit_search_telemetry(phase: str, user: User) -> None:
    """Send telemetry event for search execution."""
    send_telemetry(
        f"m_flow.search EXECUTION {phase}",
        user.id,
        additional_properties={
            "m_flow_version": m_flow_version,
            "tenant_id": str(user.tenant_id) if user.tenant_id else "Single User Tenant",
        },
    )


async def _persist_search_result(
    query_id: UUID,
    results: list,
    user_id: UUID,
    combined_mode: bool,
) -> None:
    """Log search results for analytics and debugging."""
    first_result = results[0] if isinstance(results, list) else results
    formatted = await prepare_search_result(first_result)

    if combined_mode:
        serialized = json.dumps(jsonable_encoder(formatted), default=str)
    else:
        all_formatted = [await prepare_search_result(r) for r in results]
        serialized = json.dumps(jsonable_encoder(all_formatted), default=str)

    await log_result(query_id, serialized, user_id)


async def _format_combined_result(raw_results: list) -> CombinedSearchResult:
    """Transform raw results into CombinedSearchResult structure."""
    first = raw_results[0] if isinstance(raw_results, list) else raw_results
    prepared = await prepare_search_result(first)
    return CombinedSearchResult(
        result=prepared["result"],
        graphs=prepared["graphs"],
        context=prepared["context"],
        datasets=[SearchResultDataset(id=ds.id, name=ds.name) for ds in prepared["datasets"]],
    )


async def _format_standard_results(
    raw_results: list,
    only_context: bool,
    verbose: bool,
) -> List[SearchResult]:
    """Format results for non-combined search mode."""
    if not backend_access_control_enabled():
        # Format without access control
        formatted = []
        for item in raw_results:
            prepared = await prepare_search_result(item)
            formatted.append(prepared["context"] if only_context else item[0])
        # Flatten single-item list
        if len(formatted) == 1 and isinstance(formatted[0], list):
            return formatted[0]
        return formatted

    # Access-controlled format with dataset metadata
    output = []
    for item in raw_results:
        prepared = await prepare_search_result(item)
        datasets = prepared["datasets"]
        content = prepared["context"] if only_context else prepared["result"]

        entry = {
            "search_result": [content] if content else None,
            "dataset_id": str(datasets[0].id),
            "dataset_name": datasets[0].name,
            "dataset_tenant_id": str(datasets[0].tenant_id) if datasets[0].tenant_id else None,
        }
        if verbose:
            entry["graphs"] = prepared["graphs"]
        output.append(entry)

    return output


async def _authorized_search_impl(
    query_type: RecallMode,
    query_text: str,
    user: User,
    dataset_ids: Optional[list[UUID]] = None,
    system_prompt_path: str = "direct_answer.txt",
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: bool = False,
    only_context: bool = False,
    use_combined_context: bool = False,
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
    collections: Optional[List[str]] = None,
) -> Union[
    Tuple[Any, Union[List[Edge], str], List[Dataset]],
    List[Tuple[Any, Union[List[Edge], str], List[Dataset]]],
]:
    """
    Internal implementation for access-controlled search.

    Verifies user permissions and executes search across authorized datasets.
    """
    # Resolve datasets with read permission
    authorized_datasets = await get_authorized_existing_datasets(
        datasets=dataset_ids,
        permission_type="read",
        user=user,
    )

    if use_combined_context:
        # Gather context from all datasets, then generate single completion
        per_dataset_results = await _execute_multi_dataset_search(
            datasets=authorized_datasets,
            query_type=query_type,
            query_text=query_text,
            system_prompt_path=system_prompt_path,
            system_prompt=system_prompt,
            top_k=top_k,
            node_type=node_type,
            node_name=node_name,
            save_interaction=save_interaction,
            only_context=True,
            session_id=session_id,
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

        # Merge contexts by dataset
        merged_context: dict = {}
        all_datasets: List[Dataset] = []

        for _, ctx, ds_list in per_dataset_results:
            for ds in ds_list:
                merged_context[str(ds.id)] = ctx
            all_datasets.extend(ds_list)

        # Generate completion using merged context
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

        completion_fn = tools[0]
        combined_ctx = _merge_context_values(merged_context)
        answer = await completion_fn(query_text, combined_ctx, session_id=session_id)

        return answer, combined_ctx, all_datasets

    # Standard per-dataset search
    return await _execute_multi_dataset_search(
        datasets=authorized_datasets,
        query_type=query_type,
        query_text=query_text,
        system_prompt_path=system_prompt_path,
        system_prompt=system_prompt,
        top_k=top_k,
        node_type=node_type,
        node_name=node_name,
        save_interaction=save_interaction,
        only_context=only_context,
        session_id=session_id,
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


def _merge_context_values(ctx_by_dataset: dict) -> Union[List[Edge], str]:
    """Combine context fragments from multiple datasets."""
    all_ctx = []
    for fragment in ctx_by_dataset.values():
        if isinstance(fragment, list):
            all_ctx.extend(fragment)
        else:
            all_ctx.append(fragment)

    # If all items are strings, join them
    if all_ctx and all(isinstance(x, str) for x in all_ctx):
        return "\n".join(all_ctx)
    return all_ctx


async def _execute_multi_dataset_search(
    datasets: list[Dataset],
    query_type: RecallMode,
    query_text: str,
    system_prompt_path: str = "direct_answer.txt",
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: bool = False,
    only_context: bool = False,
    context: Optional[Any] = None,
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
    collections: Optional[List[str]] = None,
) -> List[Tuple[Any, Union[str, List[Edge]], List[Dataset]]]:
    """
    Execute search across multiple datasets concurrently.

    Each dataset is searched in its own database context, and results
    are aggregated into a list of tuples.
    """
    coroutines = [
        _search_single_dataset(
            dataset=ds,
            query_type=query_type,
            query_text=query_text,
            system_prompt_path=system_prompt_path,
            system_prompt=system_prompt,
            top_k=top_k,
            node_type=node_type,
            node_name=node_name,
            save_interaction=save_interaction,
            only_context=only_context,
            context=context,
            session_id=session_id,
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
        for ds in datasets
    ]
    return await asyncio.gather(*coroutines)


async def _search_single_dataset(
    dataset: Dataset,
    query_type: RecallMode,
    query_text: str,
    system_prompt_path: str = "direct_answer.txt",
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: bool = False,
    only_context: bool = False,
    context: Optional[Any] = None,
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
    collections: Optional[List[str]] = None,
) -> Tuple[Any, Union[str, List[Edge]], List[Dataset]]:
    """
    Search within a single dataset's database context.

    Sets up the appropriate database connection and executes the search
    using the configured recall mode tools.
    """
    # Configure database context for this dataset
    await set_db_context(dataset.id, dataset.owner_id)

    # Check if graph has data
    graph_db = await get_graph_provider()
    if await graph_db.is_empty():
        await _warn_empty_graph(dataset)

    # Get search tools for the specified recall mode
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

    # Execute based on tool count (context retriever vs. single tool)
    if len(tools) == 2:
        completion_fn, context_fn = tools

        if only_context:
            retrieved_ctx = await context_fn(query_text)
            if query_type == RecallMode.PROCEDURAL and isinstance(retrieved_ctx, list):
                from m_flow.retrieval.procedural_retriever import _build_procedural_structured_json

                try:
                    retrieved_ctx = _build_procedural_structured_json(retrieved_ctx)
                except Exception:
                    pass
            return None, retrieved_ctx, [dataset]

        search_ctx = context if context else await context_fn(query_text)
        answer = await completion_fn(query_text, search_ctx, session_id=session_id)
        return answer, search_ctx, [dataset]

    # Single-tool mode (e.g., direct retrieval)
    single_tool = tools[0]
    result = await single_tool(query_text)
    return result, "", [dataset]


async def _warn_empty_graph(dataset: Dataset) -> None:
    """Log warning when searching an empty knowledge graph."""
    from m_flow.data.methods import fetch_dataset_items

    data_items = await fetch_dataset_items(dataset.id)
    if data_items:
        _logger.warning(
            f"Dataset '{dataset.name}' has {len(data_items)} data item(s) "
            "but the knowledge graph is empty. Run memorize first."
        )
    else:
        _logger.warning("Search attempted on empty knowledge graph - no data has been added to this dataset")


# Backwards compatibility aliases
authorized_search = _authorized_search_impl
search_in_datasets_context = _execute_multi_dataset_search
