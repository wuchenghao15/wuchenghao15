"""
Knowledge Graph Search Module

Provides multi-mode semantic search functionality across the knowledge graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from m_flow.auth.methods import get_seed_user
from m_flow.auth.models import User
from m_flow.context_global_variables import set_session_user_context_variable
from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.data.exceptions import DatasetNotFoundError
from m_flow.data.methods import get_authorized_existing_datasets
from m_flow.search.methods import search as execute_search
from m_flow.search.types import CombinedSearchResult, RecallMode, SearchResult
from m_flow.shared.logging_utils import get_logger

_log = get_logger()

# ============================================================================
# Simplified API Data Classes
# ============================================================================


@dataclass
class QueryResult:
    """
    Simplified query result.

    Attributes:
        answer: LLM-generated answer (only available in triplet mode)
        context: Retrieved context
            - List[Any]: From List[SearchResult].search_result (episodic/chunks mode)
            - Dict[str, Any]: From CombinedSearchResult.context (triplet mode)
        datasets: Source dataset names

    Example:
        >>> result = await m_flow.query("What were the decisions from last week's meeting?")
        >>> print(result.answer)
        >>> for ctx in result.context:
        ...     print(ctx)
    """

    answer: Optional[str] = None
    context: Union[List[Any], Dict[str, Any]] = field(default_factory=list)
    datasets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "answer": self.answer,
            "context": self.context,
            "datasets": self.datasets,
        }

    def has_answer(self) -> bool:
        """Check if there is an LLM-generated answer."""
        return self.answer is not None and len(self.answer) > 0

    def is_empty(self) -> bool:
        """Check if result is empty."""
        if self.answer:
            return False
        if isinstance(self.context, list):
            return len(self.context) == 0
        if isinstance(self.context, dict):
            return len(self.context) == 0
        return True


@dataclass
class SearchConfig:
    """
    Advanced search configuration.

    Bundles less commonly used parameters to simplify search() function signature.

    Attributes:
        system_prompt: Custom system prompt
        system_prompt_path: System prompt file path
        save_interaction: Whether to save interaction results to graph
        use_combined_context: Whether to use combined context from multiple datasets
        wide_search_top_k: Number of candidates for wide search
        triplet_distance_penalty: Distance penalty for triplet search
        verbose: Verbose output mode

    Example:
        >>> config = SearchConfig(verbose=True, top_k=20)
        >>> result = await m_flow.search("query", config=config)
    """

    system_prompt: Optional[str] = None
    system_prompt_path: str = "direct_answer.txt"
    save_interaction: bool = False
    use_combined_context: bool = False
    wide_search_top_k: int = 100
    triplet_distance_penalty: float = 3.5
    verbose: bool = False


def _normalize_datasets(raw: Union[list, str, UUID, None]) -> Optional[list]:
    """Normalize dataset parameter to list format."""
    if raw is None:
        return None
    if isinstance(raw, (str, UUID)):
        return [raw]
    return list(raw)


async def _resolve_dataset_ids(
    ds_names: list,
    current_user: User,
) -> list[UUID]:
    """Resolve dataset names to UUID list."""
    if not ds_names:
        return []

    # Check if all items are strings
    all_strings = all(isinstance(d, str) for d in ds_names)
    if not all_strings:
        return ds_names  # Already UUIDs or mixed types

    authorized = await get_authorized_existing_datasets(ds_names, "read", current_user)
    if not authorized:
        raise DatasetNotFoundError(message="No datasets found.")

    return [ds.id for ds in authorized]


async def search(
    query_text: str,
    query_type: RecallMode = RecallMode.TRIPLET_COMPLETION,
    user: Optional[User] = None,
    datasets: Optional[Union[list[str], str]] = None,
    dataset_ids: Optional[Union[list[UUID], UUID]] = None,
    system_prompt_path: Optional[str] = None,
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: Optional[bool] = None,
    last_k: Optional[int] = 1,  # Deprecated: unused, kept for API compatibility
    only_context: bool = False,
    use_combined_context: Optional[bool] = None,
    session_id: Optional[str] = None,
    wide_search_top_k: Optional[int] = None,
    triplet_distance_penalty: Optional[float] = None,
    verbose: Optional[bool] = None,
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
    # Advanced configuration
    config: Optional[SearchConfig] = None,
) -> Union[List[SearchResult], CombinedSearchResult]:
    """
    Search for information, insights, and relationships in the knowledge graph.

    This is the final step of the M-flow workflow, retrieving information from
    the processed knowledge graph. Supports multiple recall modes optimized
    for different use cases.

    Prerequisites:
        - LLM_API_KEY: Required for TRIPLET_COMPLETION mode
        - Data added: Must first add data via m_flow.add()
        - Knowledge graph built: Must process data via m_flow.memorize()
        - Dataset permissions: User must have read access to target datasets

    Recall Modes:

        TRIPLET_COMPLETION (recommended default):
            Natural language Q&A using full graph context and LLM reasoning.
            Best for: Complex questions, analysis, summarization, insights

        EPISODIC:
            Episodic memory search using Episode/Facet/Entity graph.
            Best for: Event-based recall, contextual memory retrieval

        PROCEDURAL:
            Procedural memory search for step-by-step instructions.
            Best for: How-to guides, workflow retrieval

        CYPHER:
            Direct graph database query using Cypher syntax.
            Best for: Advanced users, specific graph traversals

        CHUNKS_LEXICAL:
            Lexical text chunk search.
            Best for: Exact term matching, stopword-aware lookups

    Args:
        query_text: Natural language question or search query
        query_type: RecallMode enum specifying the search mode
        user: User context for data access permissions
        datasets: Dataset names to search
        dataset_ids: Dataset UUID identifiers (alternative to datasets)
        system_prompt_path: Custom system prompt file for LLM search types
        top_k: Maximum number of results to return
        node_type: Filter results by specific entity type
        node_name: Filter results by specific named entities
        save_interaction: Whether to save interaction results to graph
        session_id: Session identifier for caching Q&A interactions
        verbose: If True, return detailed results including graph representation

    Returns:
        List of search results in format determined by query_type.

    Note:
        When both parameters and config are specified, direct parameters
        take priority over config settings.
        Example: search(..., config=SearchConfig(verbose=True), verbose=False)
        Result: verbose=False (direct parameter takes priority)
    """
    # Merge configuration - direct parameters take priority over config
    # Create default configuration
    effective_config = SearchConfig()

    # If config provided, use its values as base
    if config is not None:
        effective_config = config

    # Direct parameters override config (only when parameter is not None)
    final_system_prompt = system_prompt if system_prompt is not None else effective_config.system_prompt
    final_system_prompt_path = (
        system_prompt_path if system_prompt_path is not None else effective_config.system_prompt_path
    )
    final_save_interaction = save_interaction if save_interaction is not None else effective_config.save_interaction
    final_use_combined_context = (
        use_combined_context if use_combined_context is not None else effective_config.use_combined_context
    )
    final_wide_search_top_k = wide_search_top_k if wide_search_top_k is not None else effective_config.wide_search_top_k
    final_triplet_distance_penalty = (
        triplet_distance_penalty if triplet_distance_penalty is not None else effective_config.triplet_distance_penalty
    )
    final_verbose = verbose if verbose is not None else effective_config.verbose

    # Get or use default user
    active_user = user
    if active_user is None:
        active_user = await get_seed_user()

    # Set session user context
    await set_session_user_context_variable(active_user)

    # Normalize dataset parameters
    ds_list = _normalize_datasets(datasets)

    # Resolve dataset IDs
    resolved_ds_ids = None
    if ds_list is not None:
        resolved_ds_ids = await _resolve_dataset_ids(ds_list, active_user)

    # Determine final dataset IDs
    final_ds_ids = dataset_ids if dataset_ids else resolved_ds_ids

    # Execute search (using merged configuration values)
    results = await execute_search(
        query_text=query_text,
        query_type=query_type,
        dataset_ids=final_ds_ids,
        user=active_user,
        system_prompt_path=final_system_prompt_path,
        system_prompt=final_system_prompt,
        top_k=top_k,
        node_type=node_type,
        node_name=node_name,
        save_interaction=final_save_interaction,
        only_context=only_context,
        use_combined_context=final_use_combined_context,
        session_id=session_id,
        wide_search_top_k=final_wide_search_top_k,
        triplet_distance_penalty=final_triplet_distance_penalty,
        verbose=final_verbose,
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

    return results


# ============================================================================
# Simplified Query Interface
# ============================================================================

# Mode mapping table
_MODE_MAP: Dict[str, RecallMode] = {
    "episodic": RecallMode.EPISODIC,
    "triplet": RecallMode.TRIPLET_COMPLETION,
    "chunks": RecallMode.CHUNKS_LEXICAL,
    "procedural": RecallMode.PROCEDURAL,
    "cypher": RecallMode.CYPHER,
}


async def query(
    question: str,
    datasets: Optional[Union[List[str], str]] = None,
    mode: str = "episodic",
    top_k: int = 10,
) -> QueryResult:
    """
    Simplified query interface.

    This is a simplified version of search(), covering 80% of common use cases.
    For advanced use cases, use search() or search() + SearchConfig.

    Args:
        question: Natural language question
        datasets: Target dataset names (optional)
        mode: Retrieval mode
            - "episodic": Episodic memory retrieval (default, suitable for most cases)
            - "triplet": Triplet + LLM answer (requires LLM API)
            - "chunks": Raw text chunk retrieval (exact matching)
            - "procedural": Procedural memory retrieval (specific scenarios)
            - "cypher": Direct Cypher query (advanced users, question should be Cypher statement)
        top_k: Number of results to return

    Returns:
        QueryResult: Simplified result object
            - answer: LLM-generated answer (triplet mode only)
            - context: Retrieved context
            - datasets: Source datasets

    Example:
        >>> import m_flow
        >>>
        >>> # Simple query (using episodic mode)
        >>> result = await m_flow.query("What were the meeting decisions?")
        >>> print(result.context)
        >>>
        >>> # Use triplet mode to get LLM answer
        >>> result = await m_flow.query("Summarize project progress", mode="triplet")
        >>> print(result.answer)
        >>>
        >>> # Specify dataset
        >>> result = await m_flow.query("meeting notes", datasets="meetings")
    """
    # Parse mode
    recall_mode = _MODE_MAP.get(mode.lower(), RecallMode.EPISODIC)

    if mode.lower() not in _MODE_MAP:
        _log.warning(
            f"[query] Unknown mode '{mode}', falling back to 'episodic'. Valid modes: {list(_MODE_MAP.keys())}"
        )

    # Call underlying search API
    raw_result = await search(
        query_text=question,
        query_type=recall_mode,
        datasets=datasets,
        top_k=top_k,
    )

    # Convert return type
    return _convert_to_query_result(raw_result)


def _convert_to_query_result(
    raw_result: Union[List[SearchResult], CombinedSearchResult],
) -> QueryResult:
    """Convert search() return value to QueryResult."""
    if isinstance(raw_result, CombinedSearchResult):
        # Triplet mode returns CombinedSearchResult
        dataset_names = []
        if raw_result.datasets:
            dataset_names = [d.name for d in raw_result.datasets if hasattr(d, "name")]

        return QueryResult(
            answer=raw_result.result,
            context=raw_result.context if raw_result.context else {},
            datasets=dataset_names,
        )

    elif isinstance(raw_result, list):
        # Episodic/Chunks/Procedural mode returns List[SearchResult]
        if not raw_result:
            return QueryResult(answer=None, context=[], datasets=[])

        context_list = [r.search_result for r in raw_result]
        dataset_names = list({r.dataset_name for r in raw_result if r.dataset_name is not None})

        return QueryResult(
            answer=None,
            context=context_list,
            datasets=dataset_names,
        )

    else:
        # Edge case: unknown type
        _log.warning(f"[query] Unexpected result type: {type(raw_result)}")
        return QueryResult(answer=None, context=[], datasets=[])
