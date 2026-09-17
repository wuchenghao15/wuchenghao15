"""
Retrieval modules for m_flow.

Includes:
- Base retrievers
- Memory orchestrator (P5)
- Procedural retrieval pipeline
- Formatters, query builders, injectors

Note: To avoid circular imports, use lazy imports when needed.
Import directly from submodules when possible.
"""

# Only export type names; actual imports are lazy to avoid circular import issues
__all__ = [
    # Base
    "BaseRetriever",
    "BaseGraphRetriever",
    # Procedural retriever
    "ProceduralRetriever",
    # Memory orchestrator
    "OrchestratorConfig",
    "OrchestratorResult",
    "MemoryOrchestrator",
    "orchestrated_search",
    "get_orchestrated_context",
    "get_partitioned_context",
    "search_with_suggestion",
    "generate_procedural_suggestion",
    # Query Builder (simplified)
    "QuerySpec",
    "build_procedural_queries",
    # Recaller
    "ProcedureHit",
    "ProceduralRecaller",
    "recall_procedures",
    # Injector
    "ProceduralInjectionResult",
    "ProceduralInjector",
    "inject_procedures",
    # Formatter
    "ProcedureCard",
    "ProceduralCardFormatter",
    "format_procedure_cards",
    "cards_to_prompt_block",
]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name in ("BaseRetriever",):
        from m_flow.retrieval.base_retriever import BaseRetriever

        return BaseRetriever

    if name in ("BaseGraphRetriever",):
        from m_flow.retrieval.base_graph_retriever import BaseGraphRetriever

        return BaseGraphRetriever

    if name in ("ProceduralRetriever",):
        from m_flow.retrieval.procedural_retriever import ProceduralRetriever

        return ProceduralRetriever

    if name in (
        "OrchestratorConfig",
        "OrchestratorResult",
        "MemoryOrchestrator",
        "orchestrated_search",
        "get_orchestrated_context",
        "get_partitioned_context",
        "search_with_suggestion",
        "generate_procedural_suggestion",
    ):
        from m_flow.retrieval import memory_orchestrator

        return getattr(memory_orchestrator, name)

    if name in ("QuerySpec", "build_procedural_queries"):
        from m_flow.retrieval.querying import procedural_query_builder

        return getattr(procedural_query_builder, name)

    if name in ("ProcedureHit", "ProceduralRecaller", "recall_procedures"):
        from m_flow.retrieval.orchestrators import procedural_recaller

        return getattr(procedural_recaller, name)

    if name in ("ProceduralInjectionResult", "ProceduralInjector", "inject_procedures"):
        from m_flow.retrieval.injection import procedural_injector

        return getattr(procedural_injector, name)

    if name in (
        "ProcedureCard",
        "ProceduralCardFormatter",
        "format_procedure_cards",
        "cards_to_prompt_block",
    ):
        from m_flow.retrieval.formatters import procedural_card_formatter

        return getattr(procedural_card_formatter, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
