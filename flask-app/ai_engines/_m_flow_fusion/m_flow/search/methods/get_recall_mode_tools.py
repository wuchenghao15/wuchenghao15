import os
from typing import Callable, List, Optional, Type

from m_flow.core.domain.models.memory_space import MemorySpace
from m_flow.search.types import RecallMode
from m_flow.search.exceptions import UnsupportedRecallModeError

# Retrievers
from m_flow.retrieval.unified_triplet_search import UnifiedTripletSearch
from m_flow.retrieval.jaccard_retrival import JaccardChunksRetriever
from m_flow.retrieval.cypher_search_retriever import CypherSearchRetriever
from m_flow.retrieval.episodic_retriever import EpisodicRetriever
from m_flow.retrieval.episodic import EpisodicConfig
from m_flow.retrieval.procedural_retriever import ProceduralRetriever


async def get_recall_mode_tools(
    query_type: RecallMode,
    query_text: str,
    system_prompt_path: str = "direct_answer.txt",
    system_prompt: Optional[str] = None,
    top_k: int = 10,
    node_type: Optional[Type] = MemorySpace,
    node_name: Optional[List[str]] = None,
    save_interaction: bool = False,
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
) -> list:
    # Build the UnifiedTripletSearch instance once
    _triplet_search = UnifiedTripletSearch(
        system_prompt_path=system_prompt_path,
        top_k=top_k,
        node_type=node_type,
        node_name=node_name,
        save_interaction=save_interaction,
        system_prompt=system_prompt,
        wide_search_top_k=wide_search_top_k,
        triplet_distance_penalty=triplet_distance_penalty,
        collections=collections,
    )

    # Build EpisodicConfig with optional overrides (Phase 0.4)
    episodic_config_kwargs = {
        "top_k": top_k,
        "episodic_nodeset_name": (node_name[0] if node_name else "Episodic"),
        "wide_search_top_k": wide_search_top_k or 100,
        "triplet_distance_penalty": triplet_distance_penalty or 3.5,
    }
    # Apply optional overrides if provided
    if enable_hybrid_search is not None:
        episodic_config_kwargs["enable_hybrid_search"] = enable_hybrid_search
    if enable_time_bonus is not None:
        episodic_config_kwargs["enable_time_bonus"] = enable_time_bonus
    if edge_miss_cost is not None:
        episodic_config_kwargs["edge_miss_cost"] = edge_miss_cost
    if hop_cost is not None:
        episodic_config_kwargs["hop_cost"] = hop_cost
    if full_number_match_bonus is not None:
        episodic_config_kwargs["full_number_match_bonus"] = full_number_match_bonus
    if enable_adaptive_weights is not None:
        episodic_config_kwargs["enable_adaptive_weights"] = enable_adaptive_weights
    # Episodic output control
    if display_mode is not None:
        episodic_config_kwargs["display_mode"] = display_mode
    if max_facets_per_episode is not None:
        episodic_config_kwargs["max_facets_per_episode"] = max_facets_per_episode
    if max_points_per_facet is not None:
        episodic_config_kwargs["max_points_per_facet"] = max_points_per_facet
    if collections is not None:
        episodic_config_kwargs["collections"] = collections

    # Build retriever instances once (avoid double instantiation)
    _cypher = CypherSearchRetriever()
    _jaccard = JaccardChunksRetriever(top_k=top_k)
    _episodic = EpisodicRetriever(
        system_prompt_path=system_prompt_path,
        top_k=top_k,
        system_prompt=system_prompt,
        config=EpisodicConfig(**episodic_config_kwargs),
    )
    # Build procedural config with time bonus support
    procedural_kwargs = {
        "system_prompt_path": system_prompt_path,
        "top_k": top_k,
        "system_prompt": system_prompt,
        "procedural_nodeset_name": (node_name[0] if node_name else "Procedural"),
        "wide_search_top_k": wide_search_top_k or 50,
    }
    if enable_time_bonus is not None:
        procedural_kwargs["enable_time_bonus"] = enable_time_bonus

    _procedural = ProceduralRetriever(**procedural_kwargs)

    search_tasks: dict[RecallMode, List[Callable]] = {
        RecallMode.TRIPLET_COMPLETION: [
            _triplet_search.get_completion,
            _triplet_search.get_context,
        ],
        RecallMode.CYPHER: [
            _cypher.get_completion,
            _cypher.get_context,
        ],
        RecallMode.CHUNKS_LEXICAL: [
            _jaccard.get_completion,
            _jaccard.get_context,
        ],
        RecallMode.EPISODIC: [
            _episodic.get_completion,
            _episodic.get_context,
        ],
        RecallMode.PROCEDURAL: [
            _procedural.get_completion,
            _procedural.get_context,
        ],
    }

    if query_type == RecallMode.CYPHER and os.getenv("ALLOW_CYPHER_QUERY", "true").lower() == "false":
        raise UnsupportedRecallModeError("Cypher query search type is disabled.")

    from m_flow.retrieval.registered_community_retrievers import (
        registered_community_retrievers,
    )

    if query_type in registered_community_retrievers:
        retriever = registered_community_retrievers[query_type]
        retriever_instance = retriever(top_k=top_k)
        recall_mode_tools = [
            retriever_instance.get_completion,
            retriever_instance.get_context,
        ]
    else:
        recall_mode_tools = search_tasks.get(query_type)

    if not recall_mode_tools:
        raise UnsupportedRecallModeError(str(query_type))

    return recall_mode_tools
