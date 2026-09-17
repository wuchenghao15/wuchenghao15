# m_flow/eval/runner.py
"""
P7-2: Evaluation Runner

Core evaluation logic: Run pipeline and collect comparable outputs.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from m_flow.shared.tracing import TraceManager
from m_flow.shared.logging_utils import get_logger

from .config import EvalConfig
from .loader import EvalCase

logger = get_logger("EvalRunner")


@dataclass
class ProceduralResult:
    """Procedural retrieval result"""

    triggered: bool = False
    injected: bool = False
    selected_keys: List[str] = field(default_factory=list)
    selected_titles: List[str] = field(default_factory=list)
    selected_is_active: List[bool] = field(default_factory=list)
    top_hits: List[Dict[str, Any]] = field(default_factory=list)
    cards_count: int = 0
    cards_chars: List[int] = field(default_factory=list)
    context_fields_present: List[str] = field(default_factory=list)
    has_steps: bool = False


@dataclass
class EpisodicResult:
    """Episodic retrieval result"""

    retrieved: bool = False
    edges_count: int = 0
    episode_ids: List[str] = field(default_factory=list)


@dataclass
class AtomicResult:
    """Atomic retrieval result"""

    retrieved: bool = False
    edges_count: int = 0


@dataclass
class CaseResult:
    """Evaluation result for a single case"""

    id: str
    ok: bool
    trace_id: str

    procedural: ProceduralResult = field(default_factory=ProceduralResult)
    episodic: EpisodicResult = field(default_factory=EpisodicResult)
    atomic: AtomicResult = field(default_factory=AtomicResult)

    error: Optional[str] = None
    debug: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "ok": self.ok,
            "trace_id": self.trace_id,
            "procedural": {
                "triggered": self.procedural.triggered,
                "injected": self.procedural.injected,
                "selected_keys": self.procedural.selected_keys,
                "selected_titles": self.procedural.selected_titles,
                "selected_is_active": self.procedural.selected_is_active,
                "top_hits": self.procedural.top_hits,
                "cards_count": self.procedural.cards_count,
                "cards_chars": self.procedural.cards_chars,
                "context_fields_present": self.procedural.context_fields_present,
                "has_steps": self.procedural.has_steps,
            },
            "episodic": {
                "retrieved": self.episodic.retrieved,
                "edges_count": self.episodic.edges_count,
                "episode_ids": self.episodic.episode_ids,
            },
            "atomic": {
                "retrieved": self.atomic.retrieved,
                "edges_count": self.atomic.edges_count,
            },
            "error": self.error,
            "debug": self.debug,
        }


class EvalRunner:
    """
    Evaluation runner.

    Responsibilities:
    - Run pipeline
    - Collect comparable outputs
    - Record traces
    """

    def __init__(self, config: EvalConfig):
        self.config = config
        self._orchestrator = None

    async def _get_orchestrator(self):
        """Get MemoryOrchestrator instance"""
        if self._orchestrator is None:
            from m_flow.retrieval.memory_orchestrator import (
                MemoryOrchestrator,
                OrchestratorConfig,
            )

            orch_config = OrchestratorConfig(
                atomic_top_k=5,
                episodic_top_k=3,
                procedural_top_k=3,
                enable_procedural=True,
                enable_soft_routing=True,
            )

            self._orchestrator = MemoryOrchestrator(
                config=orch_config,
                enable_p5_pipeline=True,
                suggestion_mode="explicit",
            )

        return self._orchestrator

    async def run_case(self, case: EvalCase) -> CaseResult:
        """Run a single evaluation case"""
        # Start trace
        TraceManager.start(
            "eval.case",
            meta={
                "case_id": case.id,
                "type": case.type,
                "query": case.query[:100],
            },
        )
        trace_id = TraceManager.current_trace_id() or ""

        try:
            with TraceManager.span("eval.pipeline"):
                result = await self._run_pipeline(case)

            TraceManager.event(
                "eval.pipeline.out",
                {
                    "procedural_triggered": result.procedural.triggered,
                    "procedural_injected": result.procedural.injected,
                    "procedural_hits": len(result.procedural.top_hits),
                    "episodic_edges": result.episodic.edges_count,
                    "atomic_edges": result.atomic.edges_count,
                },
            )

            result.trace_id = trace_id
            result.ok = True
            TraceManager.end("ok")
            return result

        except Exception as e:
            logger.error(f"[eval] Case {case.id} failed: {e}")
            TraceManager.event("eval.case.error", {"error": str(e)})
            TraceManager.end("error")

            return CaseResult(
                id=case.id,
                ok=False,
                trace_id=trace_id,
                error=str(e),
            )

    async def _run_pipeline(self, case: EvalCase) -> CaseResult:
        """Run complete pipeline"""
        orchestrator = await self._get_orchestrator()

        # Build conversation context
        conversation_ctx = None
        if case.conversation_ctx.messages:
            conversation_ctx = [m.get("content", "") for m in case.conversation_ctx.messages]

        # Call orchestrator
        orch_result = await orchestrator.retrieve(
            query=case.query,
            conversation_ctx=conversation_ctx,
        )

        # Parse procedural results
        procedural = ProceduralResult()

        if orch_result.trigger_result:
            procedural.triggered = orch_result.trigger_result.triggered

        if orch_result.injection_result:
            procedural.injected = orch_result.injection_result.should_inject
            procedural.cards_count = len(orch_result.injection_result.cards)
            procedural.cards_chars = [len(c.to_text()) for c in orch_result.injection_result.cards]
            procedural.selected_keys = orch_result.injection_result.selected_procedure_ids

        # Parse procedure_hits
        if orch_result.procedure_hits:
            for hit in orch_result.procedure_hits[:5]:
                hit_info = {
                    "key": hit.procedure_id,
                    "procedure_key": "",  # P7 document requires procedure_key
                    "title": "",
                    "score": hit.score,
                    "active": True,
                }
                # Try to get more info from bundle_metadata
                if hit.bundle_metadata:
                    hit_info["title"] = hit.bundle_metadata.get("procedure_name", "")
                    hit_info["active"] = hit.bundle_metadata.get("is_active", True)
                    # P7 document requires: use procedure_key instead of procedure_id
                    hit_info["procedure_key"] = hit.bundle_metadata.get("procedure_key") or hit.bundle_metadata.get(
                        "signature", ""
                    )

                procedural.top_hits.append(hit_info)
                procedural.selected_titles.append(hit_info["title"])
                procedural.selected_is_active.append(hit_info["active"])

        # Check context fields and steps
        if orch_result.injection_result and orch_result.injection_result.cards:
            for card in orch_result.injection_result.cards:
                card_text = card.to_text()
                if "When:" in card_text or "when:" in card_text.lower():
                    if "when" not in procedural.context_fields_present:
                        procedural.context_fields_present.append("when")
                if "Why:" in card_text or "why:" in card_text.lower():
                    if "why" not in procedural.context_fields_present:
                        procedural.context_fields_present.append("why")
                if "Boundary:" in card_text or "boundary:" in card_text.lower():
                    if "boundary" not in procedural.context_fields_present:
                        procedural.context_fields_present.append("boundary")

                # Check steps
                if "1)" in card_text or "1." in card_text or "Step " in card_text:
                    procedural.has_steps = True

        # Parse episodic results
        episodic = EpisodicResult()
        if orch_result.episodic_edges:
            episodic.retrieved = True
            episodic.edges_count = len(orch_result.episodic_edges)
            # Extract episode IDs
            seen_ids = set()
            for edge in orch_result.episodic_edges:
                if hasattr(edge, "node1"):
                    n1_type = edge.node1.attributes.get("type", "")
                    if n1_type == "Episode":
                        seen_ids.add(edge.node1.id)
                if hasattr(edge, "node2"):
                    n2_type = edge.node2.attributes.get("type", "")
                    if n2_type == "Episode":
                        seen_ids.add(edge.node2.id)
            episodic.episode_ids = list(seen_ids)[:10]

        # Parse atomic results
        atomic = AtomicResult()
        if orch_result.atomic_edges:
            atomic.retrieved = True
            atomic.edges_count = len(orch_result.atomic_edges)

        return CaseResult(
            id=case.id,
            ok=True,
            trace_id="",
            procedural=procedural,
            episodic=episodic,
            atomic=atomic,
            debug={
                "budgets_used": orch_result.budgets_used,
            },
        )

    async def run_all(
        self,
        cases: List[EvalCase],
        concurrency: int = 1,
        progress_callback=None,
    ) -> List[CaseResult]:
        """
        Run all evaluation cases.

        Args:
            cases: List of cases
            concurrency: Concurrency level (recommended 1 for stability)
            progress_callback: Progress callback (current, total, case_id)

        Returns:
            List of CaseResult
        """
        results: List[CaseResult] = []

        if concurrency <= 1:
            # Serial execution (recommended)
            for i, case in enumerate(cases):
                if progress_callback:
                    progress_callback(i + 1, len(cases), case.id)

                result = await self.run_case(case)
                results.append(result)
        else:
            # Concurrent execution (may be unstable)
            semaphore = asyncio.Semaphore(concurrency)

            async def run_with_sem(case: EvalCase, idx: int) -> CaseResult:
                async with semaphore:
                    if progress_callback:
                        progress_callback(idx + 1, len(cases), case.id)
                    return await self.run_case(case)

            tasks = [run_with_sem(c, i) for i, c in enumerate(cases)]
            results = await asyncio.gather(*tasks)

        return results
