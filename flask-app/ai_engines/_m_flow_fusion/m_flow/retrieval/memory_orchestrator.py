"""
Memory Orchestrator - multi-memory type parallel retrieval + soft routing + partitioned output.

Core functions:
1. Parallel retrieval: atomic + episodic + procedural
2. Soft routing: dynamically adjust top_k per type based on query intent
3. Complete pipeline: Trigger -> QueryBuilder -> Recaller -> Injector -> Formatter
4. Partitioned prompt output: procedural / episodic / atomic three blocks

Design principles:
- Don't break existing episodic/atomic effectiveness
- Procedural as "method layer" supplements when needed
- Avoid procedural flooding in non-method questions
- Associative auto-suggestion mode

Default budget allocation:
- atomic: 6
- episodic: 4
- procedural: 2

When query has strong procedural intent:
- procedural: 5
- episodic: 3
"""

import asyncio
import os
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.tracing import TraceManager
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge

# P5 imports
# Procedural retrieval controlled by config.enable_procedural
from m_flow.retrieval.querying.procedural_query_builder import (
    build_procedural_queries,
)
from m_flow.retrieval.orchestrators.procedural_recaller import (
    ProcedureHit,
    recall_procedures,
)
from m_flow.retrieval.injection.procedural_injector import (
    ProceduralInjectionResult,
    inject_procedures,
)
from m_flow.retrieval.formatters.procedural_card_formatter import (
    ProcedureCard,
)

logger = get_logger("MemoryOrchestrator")


@dataclass
class OrchestratorConfig:
    """Configuration for memory orchestrator."""

    # Default budgets
    atomic_top_k: int = 6
    episodic_top_k: int = 4
    procedural_top_k: int = 2

    # Procedural intent budgets
    procedural_intent_procedural_top_k: int = 5
    procedural_intent_episodic_top_k: int = 3

    # Feature flags
    enable_atomic: bool = True
    enable_episodic: bool = True
    enable_procedural: bool = True

    # Soft routing
    enable_soft_routing: bool = True

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Load config from environment variables."""
        return cls(
            atomic_top_k=int(os.getenv("MFLOW_ATOMIC_TOP_K", "6")),
            episodic_top_k=int(os.getenv("MFLOW_EPISODIC_TOP_K", "4")),
            procedural_top_k=int(os.getenv("MFLOW_PROCEDURAL_TOP_K", "2")),
            procedural_intent_procedural_top_k=int(os.getenv("MFLOW_PROCEDURAL_INTENT_PROCEDURAL_TOP_K", "5")),
            procedural_intent_episodic_top_k=int(os.getenv("MFLOW_PROCEDURAL_INTENT_EPISODIC_TOP_K", "3")),
            enable_atomic=os.getenv("MFLOW_ENABLE_ATOMIC", "true").lower() == "true",
            enable_episodic=os.getenv("MFLOW_ENABLE_EPISODIC", "true").lower() == "true",
            enable_procedural=os.getenv("MFLOW_ENABLE_PROCEDURAL", "true").lower() == "true",
            enable_soft_routing=os.getenv("MFLOW_ENABLE_SOFT_ROUTING", "true").lower() == "true",
        )


@dataclass
class OrchestratorResult:
    """Result from memory orchestrator."""

    query: str

    # Retrieved edges by type
    atomic_edges: List[Edge] = field(default_factory=list)
    episodic_edges: List[Edge] = field(default_factory=list)
    procedural_edges: List[Edge] = field(default_factory=list)

    # Merged edges (deduplicated, ordered by relevance)
    merged_edges: List[Edge] = field(default_factory=list)

    # Metadata
    procedural_intent_detected: bool = False
    budgets_used: Dict[str, int] = field(default_factory=dict)

    procedure_hits: List[ProcedureHit] = field(default_factory=list)
    injection_result: Optional[ProceduralInjectionResult] = None
    procedure_cards: List[ProcedureCard] = field(default_factory=list)

    # Partitioned prompt text
    procedural_block: str = ""
    episodic_block: str = ""
    atomic_block: str = ""

    @property
    def total_edges(self) -> int:
        return len(self.merged_edges)

    def get_all_edges(self) -> List[Edge]:
        """Get all edges in priority order: procedural > episodic > atomic."""
        return self.merged_edges

    def get_partitioned_context(self) -> str:
        """
        Get partitioned prompt context.

        Order: procedural -> episodic -> atomic
        Includes instructions.
        """
        parts = []

        if self.procedural_block:
            parts.append(self.procedural_block)

        if self.episodic_block:
            parts.append(f"### [EPISODE] Related Event Memory\n\n{self.episodic_block}")

        if self.atomic_block:
            parts.append(f"### [FACT] Related Facts\n\n{self.atomic_block}")

        return "\n\n---\n\n".join(parts)


class MemoryOrchestrator:
    """
    Multi-memory type orchestrator.

    Coordinates parallel retrieval across atomic, episodic, and procedural
    memory systems with soft routing based on query intent.

    Complete pipeline:
    1. Trigger: Determine whether to recall procedural
    2. QueryBuilder: Build multi-level queries
    3. Recaller: Multi-query recall + merge
    4. Injector: Decide injection strategy
    5. Formatter: Format output
    """

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        enable_p5_pipeline: bool = True,
        suggestion_mode: str = "implicit",  # P5-6: "implicit" | "explicit"
    ):
        self.config = config or OrchestratorConfig.from_env()
        self.enable_p5_pipeline = enable_p5_pipeline
        self.suggestion_mode = suggestion_mode

    async def retrieve(
        self,
        query: str,
        override_budgets: Optional[Dict[str, int]] = None,
        conversation_ctx: Optional[List[str]] = None,
    ) -> OrchestratorResult:
        """
        Retrieve from all memory types in parallel.

        Args:
            query: Search query
            override_budgets: Optional dict to override top_k per type
                e.g., {"atomic": 10, "episodic": 5, "procedural": 3}
            conversation_ctx: Optional conversation context for P5 trigger

        Returns:
            OrchestratorResult with edges from all memory types
        """
        # P6: Start trace
        TraceManager.start(
            "rag.retrieve",
            meta={
                "query": query[:200],
                "enable_p5": self.enable_p5_pipeline,
            },
        )

        result = OrchestratorResult(query=query)

        # Note: procedural_intent_detected is NOT set from config.
        # Without a real intent classifier, default to False (standard priority order).
        # Procedural retrieval is still executed when config.enable_procedural=True,
        # but edges are merged in standard priority: episodic > atomic > procedural.
        result.procedural_intent_detected = False

        budgets = self._compute_budgets(overrides=override_budgets)
        result.budgets_used = budgets

        logger.info(
            f"[orchestrator] Query: '{query[:50]}...', "
            f"procedural_intent={result.procedural_intent_detected}, "
            f"budgets={budgets}"
        )

        # Parallel retrieval for atomic and episodic
        tasks = []
        task_names = []

        if self.config.enable_atomic and budgets.get("atomic", 0) > 0:
            tasks.append(self._retrieve_atomic(query, budgets["atomic"]))
            task_names.append("atomic")

        if self.config.enable_episodic and budgets.get("episodic", 0) > 0:
            tasks.append(self._retrieve_episodic(query, budgets["episodic"]))
            task_names.append("episodic")

        # Pipeline for procedural (controlled by config.enable_procedural)
        if self.config.enable_procedural and budgets.get("procedural", 0) > 0:
            if self.enable_p5_pipeline:
                tasks.append(
                    self._retrieve_procedural_p5(
                        query,
                        budgets["procedural"],
                        conversation_ctx,
                    )
                )
                task_names.append("procedural_p5")
            else:
                tasks.append(self._retrieve_procedural(query, budgets["procedural"]))
                task_names.append("procedural")

        if not tasks:
            logger.warning("[orchestrator] No retrieval tasks to execute")
            return result

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, res in zip(task_names, results):
            if isinstance(res, Exception):
                logger.warning(f"[orchestrator] {name} retrieval failed: {res}")
                continue

            if name == "atomic":
                result.atomic_edges = res
            elif name == "episodic":
                result.episodic_edges = res
            elif name == "procedural":
                result.procedural_edges = res
            elif name == "procedural_p5":
                # Returns richer results
                p5_result = res
                result.procedural_edges = p5_result.get("edges", [])
                result.procedure_hits = p5_result.get("hits", [])
                result.injection_result = p5_result.get("injection", None)
                result.procedure_cards = p5_result.get("cards", [])
                result.procedural_block = p5_result.get("block", "")

        # Merge edges
        result.merged_edges = self._merge_edges(result)

        # Build partitioned blocks
        await self._build_partition_blocks(result)

        # Record final result
        TraceManager.event(
            "rag.retrieve.done",
            {
                "atomic_count": len(result.atomic_edges),
                "episodic_count": len(result.episodic_edges),
                "procedural_count": len(result.procedural_edges),
                "merged_count": len(result.merged_edges),
                "procedure_hits": len(result.procedure_hits),
                "injected": result.injection_result.should_inject if result.injection_result else False,
            },
        )
        TraceManager.end("ok")

        logger.info(
            f"[orchestrator] Retrieved: atomic={len(result.atomic_edges)}, "
            f"episodic={len(result.episodic_edges)}, "
            f"procedural={len(result.procedural_edges)}, "
            f"merged={len(result.merged_edges)}"
        )

        return result

    def _compute_budgets(
        self,
        overrides: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        """Compute budgets based on config and overrides."""
        # Simple budget computation - no intent-based adjustment
        # Procedural retrieval is controlled by config.enable_procedural
        budgets = {
            "atomic": self.config.atomic_top_k,
            "episodic": self.config.episodic_top_k,
            "procedural": self.config.procedural_top_k if self.config.enable_procedural else 0,
        }

        # Apply overrides
        if overrides:
            budgets.update(overrides)

        return budgets

    async def _retrieve_atomic(self, query: str, top_k: int) -> List[Edge]:
        """Retrieve from atomic memory."""
        try:
            from m_flow.retrieval.unified_triplet_search import UnifiedTripletSearch

            retriever = UnifiedTripletSearch(top_k=top_k)
            edges = await retriever.get_context(query)
            return edges or []
        except Exception as e:
            logger.debug(f"[orchestrator] Atomic retrieval error: {e}")
            return []

    async def _retrieve_episodic(self, query: str, top_k: int) -> List[Edge]:
        """Retrieve from episodic memory."""
        try:
            from m_flow.retrieval.episodic_retriever import EpisodicRetriever

            retriever = EpisodicRetriever(top_k=top_k)
            edges = await retriever.get_context(query)
            return edges or []
        except Exception as e:
            logger.debug(f"[orchestrator] Episodic retrieval error: {e}")
            return []

    async def _retrieve_procedural(self, query: str, top_k: int) -> List[Edge]:
        """Retrieve from procedural memory (legacy mode)."""
        try:
            from m_flow.retrieval.procedural_retriever import ProceduralRetriever

            retriever = ProceduralRetriever(top_k=top_k)
            edges = await retriever.get_context(query)
            return edges or []
        except Exception as e:
            logger.debug(f"[orchestrator] Procedural retrieval error: {e}")
            return []

    async def _retrieve_procedural_p5(
        self,
        query: str,
        top_k: int,
        conversation_ctx: Optional[List[str]],
    ) -> Dict:
        """
        Complete pipeline: QueryBuilder -> Recaller -> Injector -> Formatter.
        Note: Trigger logic removed - procedural retrieval is controlled by config.
        """
        try:
            # Build multi-level queries (no trigger_result needed)
            queries = build_procedural_queries(
                user_msg=query,
                conversation_ctx=conversation_ctx,
                trigger_result=None,
                max_queries=4,
            )

            if not queries:
                return {"edges": [], "hits": [], "injection": None, "cards": [], "block": ""}

            # Multi-query recall
            hits = await recall_procedures(
                queries=queries,
                top_k_per_query=min(3, top_k),
                max_total=top_k,
            )

            if not hits:
                return {"edges": [], "hits": [], "injection": None, "cards": [], "block": ""}

            # Injection decision (no trigger_result needed)
            injection = inject_procedures(
                hits=hits,
                trigger_result=None,
                max_procedures=2,
            )

            # Collect all edges
            all_edges = []
            for hit in hits:
                all_edges.extend(hit.edges)

            # Format cards and block
            block = ""
            if injection.should_inject:
                block = injection.cards_text

            return {
                "edges": all_edges,
                "hits": hits,
                "injection": injection,
                "cards": injection.cards if injection else [],
                "block": block,
            }

        except Exception as e:
            logger.debug(f"[orchestrator] P5 procedural retrieval error: {e}")
            return {"edges": [], "hits": [], "injection": None, "cards": [], "block": ""}

    async def _build_partition_blocks(self, result: OrchestratorResult) -> None:
        """
        Build partitioned prompt blocks.

        Partition by type: procedural / episodic / atomic.
        """
        # procedural_block already built in pipeline
        # Only need to build episodic_block and atomic_block here

        from m_flow.knowledge.graph_ops.utils.resolve_edges_to_text import (
            resolve_edges_to_text,
        )

        if result.episodic_edges:
            try:
                result.episodic_block = await resolve_edges_to_text(result.episodic_edges)
            except Exception as e:
                logger.debug(f"[orchestrator] Failed to resolve episodic edges: {e}")
                result.episodic_block = ""

        if result.atomic_edges:
            try:
                result.atomic_block = await resolve_edges_to_text(result.atomic_edges)
            except Exception as e:
                logger.debug(f"[orchestrator] Failed to resolve atomic edges: {e}")
                result.atomic_block = ""

    def _merge_edges(self, result: OrchestratorResult) -> List[Edge]:
        """
        Merge edges from all memory types.

        Priority order when procedural intent detected:
        1. procedural (most relevant for "how to" questions)
        2. episodic (context)
        3. atomic (facts)

        Otherwise:
        1. episodic
        2. atomic
        3. procedural
        """
        seen_keys: Set[str] = set()
        merged: List[Edge] = []

        def add_edges(edges: List[Edge]) -> None:
            for edge in edges:
                # Create unique key for deduplication
                key = self._edge_key(edge)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                merged.append(edge)

        if result.procedural_intent_detected:
            # Procedural intent: prioritize procedural
            add_edges(result.procedural_edges)
            add_edges(result.episodic_edges)
            add_edges(result.atomic_edges)
        else:
            # Default: prioritize episodic
            add_edges(result.episodic_edges)
            add_edges(result.atomic_edges)
            add_edges(result.procedural_edges)

        return merged

    def _edge_key(self, edge: Edge) -> str:
        """Generate unique key for edge deduplication."""
        src_id = str(edge.node1.id) if edge.node1 else ""
        tgt_id = str(edge.node2.id) if edge.node2 else ""
        rel = edge.attributes.get("relationship_name", "")
        return f"{src_id}_{tgt_id}_{rel}"


# -----------------------------
# Associative Suggestion Mode
# -----------------------------


def generate_procedural_suggestion(
    result: OrchestratorResult,
    suggestion_mode: str = "implicit",
) -> Optional[str]:
    """
    Generate associative suggestion.

    Args:
        result: OrchestratorResult
        suggestion_mode: "implicit" | "explicit"

    Returns:
        Suggestion text (if explicit suggestion needed), otherwise None
    """
    if not result.procedure_cards:
        return None

    # Implicit mode: don't generate user-visible suggestion text
    if suggestion_mode == "implicit":
        return None

    # Suggest when top hit has good score
    should_suggest = False

    # Check score-based suggestion
    if result.procedure_hits and result.procedure_hits[0].score >= 0.2:
        should_suggest = True

    if not should_suggest:
        return None

    # Generate suggestion text
    top_card = result.procedure_cards[0]

    suggestion_lines = [
        f'[TIP] **Suggestion**: I can follow the "{top_card.title}" procedure:',
    ]

    # Extract step summary
    if top_card.steps:
        steps_preview = top_card.steps[:150]
        if len(top_card.steps) > 150:
            steps_preview += "..."
        suggestion_lines.append(f"   {steps_preview}")

    suggestion_lines.append("")
    suggestion_lines.append("If you'd like to adjust the order or content this time, let me know.")

    return "\n".join(suggestion_lines)


# -----------------------------
# Convenience Functions
# -----------------------------


async def orchestrated_search(
    query: str,
    config: Optional[OrchestratorConfig] = None,
    override_budgets: Optional[Dict[str, int]] = None,
    conversation_ctx: Optional[List[str]] = None,
    enable_p5: bool = True,
) -> OrchestratorResult:
    """
    Convenience function for orchestrated search.

    Args:
        query: Search query
        config: Optional orchestrator config
        override_budgets: Optional budget overrides
        conversation_ctx: Optional conversation context for P5 trigger
        enable_p5: Whether to enable P5 pipeline (default True)

    Returns:
        OrchestratorResult with edges from all memory types
    """
    orchestrator = MemoryOrchestrator(config=config, enable_p5_pipeline=enable_p5)
    return await orchestrator.retrieve(
        query,
        override_budgets=override_budgets,
        conversation_ctx=conversation_ctx,
    )


async def get_orchestrated_context(
    query: str,
    config: Optional[OrchestratorConfig] = None,
) -> List[Edge]:
    """
    Get merged context from all memory types.

    Simplified interface returning just the edges.

    Args:
        query: Search query
        config: Optional orchestrator config

    Returns:
        List of merged edges
    """
    result = await orchestrated_search(query, config=config)
    return result.get_all_edges()


async def get_partitioned_context(
    query: str,
    config: Optional[OrchestratorConfig] = None,
    conversation_ctx: Optional[List[str]] = None,
) -> str:
    """
    Get partitioned prompt context.

    Args:
        query: Search query
        config: Optional orchestrator config
        conversation_ctx: Optional conversation context

    Returns:
        Partitioned prompt context text
    """
    result = await orchestrated_search(
        query,
        config=config,
        conversation_ctx=conversation_ctx,
        enable_p5=True,
    )
    return result.get_partitioned_context()


async def search_with_suggestion(
    query: str,
    config: Optional[OrchestratorConfig] = None,
    conversation_ctx: Optional[List[str]] = None,
    suggestion_mode: str = "explicit",
) -> Tuple[OrchestratorResult, Optional[str]]:
    """
    Execute retrieval and generate associative suggestion.

    Args:
        query: Search query
        config: Optional orchestrator config
        conversation_ctx: Optional conversation context
        suggestion_mode: "implicit" | "explicit"

    Returns:
        (OrchestratorResult, suggestion text or None)
    """
    orchestrator = MemoryOrchestrator(
        config=config,
        enable_p5_pipeline=True,
        suggestion_mode=suggestion_mode,
    )
    result = await orchestrator.retrieve(
        query,
        conversation_ctx=conversation_ctx,
    )

    suggestion = generate_procedural_suggestion(result, suggestion_mode)

    return result, suggestion
