"""
Search result formatting.

Transforms raw search results into structured response format.
"""

from __future__ import annotations

from typing import List, cast
from uuid import NAMESPACE_OID, uuid5

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.knowledge.graph_ops.utils import resolve_edges_to_text
from m_flow.search.types.SearchResult import SearchResultDataset
from m_flow.search.utils.transform_context_to_graph import transform_context_to_graph
from m_flow.search.utils.transform_insights_to_graph import transform_insights_to_graph


async def prepare_search_result(search_result) -> dict:
    """
    Format search result for API response.

    Converts context and results into graph visualizations
    and text representations.

    Args:
        search_result: Tuple of (results, context, datasets).

    Returns:
        Formatted response dict with graphs and context.
    """
    results, context, datasets = search_result

    graphs = None
    result_graph = None
    context_texts = {}

    # Default dataset if empty
    if isinstance(datasets, list) and not datasets:
        datasets = [
            SearchResultDataset(
                id=uuid5(NAMESPACE_OID, "*"),
                name="all available datasets",
            )
        ]

    ds_label = ", ".join(ds.name for ds in datasets)

    # Process context based on type
    if _is_insight_context(context):
        graphs = {ds_label: transform_insights_to_graph(context)}
        results = None

    elif _is_edge_context(context):
        graphs = {ds_label: transform_context_to_graph(context)}
        context_texts = {ds_label: await resolve_edges_to_text(context)}

    elif isinstance(context, str):
        context_texts = {ds_label: context}

    elif _is_string_list(context):
        context_texts = {ds_label: "\n".join(cast(List[str], context))}

    # Process results
    if _is_edge_list(results):
        result_graph = transform_context_to_graph(results)

    # Format final result
    final_result = result_graph or (results[0] if results and len(results) == 1 else results)

    return {
        "result": final_result,
        "graphs": graphs,
        "context": context_texts,
        "datasets": datasets,
    }


def _is_insight_context(ctx) -> bool:
    """Check if context contains insight tuples."""
    return isinstance(ctx, List) and len(ctx) > 0 and isinstance(ctx[0], tuple) and ctx[0][1].get("relationship_name")


def _is_edge_context(ctx) -> bool:
    """Check if context contains Edge objects."""
    return isinstance(ctx, List) and len(ctx) > 0 and isinstance(ctx[0], Edge)


def _is_string_list(ctx) -> bool:
    """Check if context is list of strings."""
    return isinstance(ctx, List) and len(ctx) > 0 and isinstance(ctx[0], str)


def _is_edge_list(results) -> bool:
    """Check if results contain Edge objects."""
    return isinstance(results, List) and len(results) > 0 and isinstance(results[0], Edge)
