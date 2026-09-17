"""
Procedural Injector

Decide when to inject procedural into RAG.

Soft gating strategy:
- "Whether to inject" is lenient
- "How much to inject" is strictly controlled (usually 1-2 procedure cards sufficient)

Strategy:
1. If Trigger not triggered: Only inject when top1 score < strong_threshold
2. If Trigger triggered: Inject top1 (inject even if score is poor), top2 if necessary
3. If top1 and top2 gap is small (gap < gap_threshold): Inject both
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from m_flow.retrieval.gating.procedural_trigger import TriggerResult
from m_flow.retrieval.orchestrators.procedural_recaller import ProcedureHit
from m_flow.retrieval.formatters.procedural_card_formatter import (
    ProcedureCard,
    ProceduralCardFormatter,
    cards_to_prompt_block,
)
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.tracing import TraceManager

logger = get_logger("ProceduralInjector")


@dataclass
class ProceduralInjectionResult:
    """
    Injection result.

    Attributes:
        cards: List of injected ProcedureCards
        cards_text: Text form of cards (for prompt)
        selected_procedure_ids: List of selected procedure IDs
        debug: Debug information
    """

    cards: List[ProcedureCard] = field(default_factory=list)
    cards_text: str = ""
    selected_procedure_ids: List[str] = field(default_factory=list)
    debug: Dict = field(default_factory=dict)

    @property
    def should_inject(self) -> bool:
        """Whether should inject."""
        return len(self.cards) > 0


class ProceduralInjector:
    """
    Procedural Injector

    Decide which procedures should be injected into RAG context.
    """

    def __init__(
        self,
        strong_threshold: float = 0.25,
        gap_threshold: float = 0.1,
        max_procedures: int = 2,
        weak_score_threshold: float = 0.5,
        include_provenance: bool = False,
    ):
        """
        Initialize Injector.

        Args:
            strong_threshold: Injection threshold when no trigger (only inject if score below this)
            gap_threshold: Gap threshold between top1 and top2 (inject both if gap below this)
            max_procedures: Maximum number of procedures to inject
            weak_score_threshold: Weak injection threshold (mark low confidence if score above this when triggered)
            include_provenance: Whether to include source_refs in cards
        """
        self.strong_threshold = strong_threshold
        self.gap_threshold = gap_threshold
        self.max_procedures = max_procedures
        self.weak_score_threshold = weak_score_threshold
        self.include_provenance = include_provenance
        self.formatter = ProceduralCardFormatter()

    def decide(
        self,
        hits: List[ProcedureHit],
        trigger_result: Optional[TriggerResult] = None,
    ) -> ProceduralInjectionResult:
        """
        Decide injection strategy.

        Args:
            hits: List of ProcedureHit (sorted by score)
            trigger_result: Trigger result

        Returns:
            ProceduralInjectionResult
        """
        result = ProceduralInjectionResult()

        if not hits:
            result.debug = {"reason": "no_hits"}
            return result

        triggered = trigger_result.triggered if trigger_result else False
        top1 = hits[0]
        top2 = hits[1] if len(hits) > 1 else None

        selected: List[ProcedureHit] = []
        reason = ""

        # Strategy 1: Trigger not triggered
        if not triggered:
            if top1.score < self.strong_threshold:
                selected.append(top1)
                reason = f"no_trigger_but_strong_match(score={top1.score:.3f}<{self.strong_threshold})"

                # Check if top2 should also be injected
                if top2 and (top2.score - top1.score) < self.gap_threshold:
                    selected.append(top2)
                    reason += f"+top2_close(gap={top2.score - top1.score:.3f})"
            else:
                reason = f"no_trigger_and_weak_match(score={top1.score:.3f}>={self.strong_threshold})"

        # Strategy 2: Trigger triggered
        else:
            # When triggered, at least inject top1
            selected.append(top1)
            reason = f"triggered(reason={trigger_result.reason})"

            # Mark low confidence
            if top1.score > self.weak_score_threshold:
                reason += f"+low_confidence(score={top1.score:.3f})"

            # Check if top2 needed
            if top2 and (top2.score - top1.score) < self.gap_threshold:
                selected.append(top2)
                reason += f"+top2_close(gap={top2.score - top1.score:.3f})"

        # Limit count
        selected = selected[: self.max_procedures]

        # Build cards
        if selected:
            # Get edges from hits
            all_edges = []
            bundles_meta = []
            for hit in selected:
                all_edges.extend(hit.edges)
                if hit.bundle_metadata:
                    bm = hit.bundle_metadata.copy()
                    bm["from_query_kinds"] = hit.from_query_kinds
                    bundles_meta.append(bm)

            # Format cards
            cards = self.formatter.format_from_edges(all_edges, bundles_meta)

            # Only keep selected cards
            selected_ids = {h.procedure_id for h in selected}
            cards = [c for c in cards if c.procedure_id in selected_ids]
            cards = cards[: self.max_procedures]

            result.cards = cards
            result.selected_procedure_ids = [c.procedure_id for c in cards]
            result.cards_text = cards_to_prompt_block(
                cards,
                include_provenance=self.include_provenance,
            )

        result.debug = {
            "reason": reason,
            "triggered": triggered,
            "top1_score": top1.score if hits else None,
            "top2_score": top2.score if top2 else None,
            "strong_threshold": self.strong_threshold,
            "gap_threshold": self.gap_threshold,
            "num_hits": len(hits),
            "num_selected": len(selected),
        }

        # Record injection decision
        TraceManager.event(
            "procedural.inject.decide",
            {
                "triggered": triggered,
                "top_hits": [{"id": h.procedure_id, "score": h.score} for h in hits[:3]],
                "selected_ids": result.selected_procedure_ids,
                "reason": reason,
                "card_chars": [len(c.to_text()) for c in result.cards],
            },
        )

        logger.debug(f"[injector] {reason}, selected={len(selected)}")

        return result


def inject_procedures(
    hits: List[ProcedureHit],
    trigger_result: Optional[TriggerResult] = None,
    max_procedures: int = 2,
) -> ProceduralInjectionResult:
    """
    Convenience function: decide procedural injection strategy.

    Args:
        hits: List of ProcedureHit
        trigger_result: Trigger result
        max_procedures: Maximum injection count

    Returns:
        ProceduralInjectionResult
    """
    injector = ProceduralInjector(max_procedures=max_procedures)
    return injector.decide(hits, trigger_result)
