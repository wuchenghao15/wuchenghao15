# m_flow/memory/episodic/ingestion_logger.py
"""
Episodic Memory ingestion logging module.

Provides unified logging to ensure every stage of the ingestion process is traceable:
1. Input/output for each step
2. Trigger conditions for each logical branch
3. Performance metrics (duration, LLM calls, etc.)

Log levels:
- INFO: Main process stages and key metrics
- DEBUG: Detailed data and intermediate results
- WARNING: Exceptions and fallbacks

Usage:
    from .ingestion_logger import IngestionLogger

    ilog = IngestionLogger(doc_id="doc_123", doc_title="Example Document")
    ilog.log_phase_start("routing")
    # ... execute routing logic ...
    ilog.log_phase_end("routing", decision="existing", episode_id="ep_456")
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum

from m_flow.shared.logging_utils import get_logger, INFO, DEBUG


class IngestionPhase(str, Enum):
    """Ingestion phase enumeration."""

    INIT = "init"
    ROUTING = "routing"
    ENTITY_EXTRACTION = "entity_extraction"
    FACET_GENERATION = "facet_generation"
    SEMANTIC_MERGE = "semantic_merge"
    FACET_POINTS = "facet_points"
    ENTITY_SELECTION = "entity_selection"
    ENTITY_DESCRIPTION = "entity_description"
    GRAPH_BUILD = "graph_build"
    SAME_ENTITY_EDGES = "same_entity_edges"
    COMPLETE = "complete"


@dataclass
class PhaseMetrics:
    """Single phase metrics."""

    phase: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    triggered: bool = False
    llm_calls: int = 0
    items_in: int = 0
    items_out: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def calculate_duration(self):
        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class IngestionMetrics:
    """Complete ingestion metrics."""

    doc_id: str = ""
    doc_title: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    total_duration_ms: float = 0.0

    # Metrics per phase
    phases: Dict[str, PhaseMetrics] = field(default_factory=dict)

    # Key metrics
    chunks_count: int = 0
    episodes_created: int = 0
    episodes_updated: int = 0
    facets_created: int = 0
    facet_points_created: int = 0
    entities_created: int = 0
    edges_created: int = 0

    # LLM call statistics
    total_llm_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0

    # Logical branches
    routing_decision: str = ""  # "new" | "existing" | "disabled"
    semantic_merge_used: bool = False
    facet_points_enabled: bool = False

    def calculate_total(self):
        if self.start_time and self.end_time:
            self.total_duration_ms = (self.end_time - self.start_time) * 1000


class IngestionLogger:
    """
    Ingestion process logger.

    Provides structured logging supporting:
    - Phase start/end markers
    - Detailed metrics recording
    - LLM call tracking
    - Final summary report
    """

    def __init__(self, doc_id: str, doc_title: str = "", batch_id: Optional[str] = None):
        self.doc_id = (doc_id or "unknown")[:20]
        self.doc_title = (doc_title or "")[:30]
        self.batch_id = batch_id or f"B{int(time.time() * 1000) % 100000}"

        self.metrics = IngestionMetrics(
            doc_id=self.doc_id,
            doc_title=self.doc_title,
            start_time=time.time(),
        )

        # Loggers
        self._info_logger = get_logger(name="m_flow.ingestion.info", level=INFO)
        self._debug_logger = get_logger(name="m_flow.ingestion.debug", level=DEBUG)

        self._log_info(
            f"[{self.batch_id}] [Ingestion] Ingestion started",
            {
                "doc_id": self.doc_id,
                "doc_title": self.doc_title[:20] + ("..." if len(self.doc_title) > 20 else ""),
            },
        )

    def _log_info(self, message: str, data: Optional[Dict] = None):
        """INFO level logging."""
        if data:
            self._info_logger.info(f"{message} | {self._format_data(data)}")
        else:
            self._info_logger.info(message)

    def _log_debug(self, message: str, data: Optional[Dict] = None):
        """DEBUG level logging."""
        if data:
            self._debug_logger.debug(f"{message} | {self._format_data(data)}")
        else:
            self._debug_logger.debug(message)

    def _log_warning(self, message: str, data: Optional[Dict] = None):
        """WARNING level logging."""
        if data:
            self._info_logger.warning(f"{message} | {self._format_data(data)}")
        else:
            self._info_logger.warning(message)

    def _format_data(self, data: Dict) -> str:
        """Format data as log string."""
        parts = []
        for k, v in (data or {}).items():
            if v is None:
                parts.append(f"{k}=None")
            elif isinstance(v, float):
                parts.append(f"{k}={v:.2f}")
            elif isinstance(v, list):
                parts.append(f"{k}=[{len(v)} items]")
            elif isinstance(v, dict):
                parts.append(f"{k}={{{len(v)} keys}}")
            elif isinstance(v, str) and len(v) > 30:
                parts.append(f"{k}={v[:30]}...")
            else:
                parts.append(f"{k}={v}")
        return ", ".join(parts)

    # ============================================================
    # Phase logging methods
    # ============================================================

    def log_phase_start(self, phase: str):
        """Log phase start."""
        self.metrics.phases[phase] = PhaseMetrics(
            phase=phase,
            start_time=time.time(),
        )
        self._log_debug(f"[{self.batch_id}] [Phase] {phase} started")

    def log_phase_end(self, phase: str, triggered: bool = True, **kwargs):
        """Log phase end."""
        if phase in self.metrics.phases:
            m = self.metrics.phases[phase]
            m.end_time = time.time()
            m.calculate_duration()
            m.triggered = triggered
            m.details.update(kwargs)

            if "items_in" in kwargs:
                m.items_in = kwargs["items_in"]
            if "items_out" in kwargs:
                m.items_out = kwargs["items_out"]
            if "llm_calls" in kwargs:
                m.llm_calls = kwargs["llm_calls"]
                self.metrics.total_llm_calls += kwargs["llm_calls"]

            status = "[OK]" if triggered else "[SKIP]"
            self._log_info(
                f"[{self.batch_id}] {status} {phase} completed",
                {
                    "duration_ms": m.duration_ms,
                    **{k: v for k, v in kwargs.items() if k not in ["items_in", "items_out"]},
                },
            )

    # ============================================================
    # Specific phase logging
    # ============================================================

    def log_routing(
        self,
        decision: str,  # "new" | "existing" | "disabled"
        episode_id: str,
        matched_score: Optional[float] = None,
        candidates_count: int = 0,
    ):
        """Log Episode routing decision."""
        self.log_phase_start(IngestionPhase.ROUTING)

        self.metrics.routing_decision = decision

        details = {
            "decision": decision,
            "episode_id": episode_id[:20] if episode_id else "",
        }

        if decision == "existing":
            self.metrics.episodes_updated += 1
            if matched_score is not None:
                details["score"] = matched_score
            details["candidates"] = candidates_count
            self._log_info(f"[{self.batch_id}] [Routing] Routed to existing Episode", details)
        elif decision == "new":
            self.metrics.episodes_created += 1
            self._log_info(f"[{self.batch_id}] [Routing] Created new Episode", details)
        else:
            self._log_debug(f"[{self.batch_id}] [Routing] Routing disabled, using default Episode")

        self.log_phase_end(IngestionPhase.ROUTING, triggered=True, **details)

    def log_entity_extraction(
        self,
        method: str,  # "llm" | "chunk_contains"
        segments_count: int,
        entities_found: int,
        llm_calls: int = 0,
    ):
        """Log entity extraction."""
        self.log_phase_start(IngestionPhase.ENTITY_EXTRACTION)

        details = {
            "method": method,
            "segments": segments_count,
            "entities": entities_found,
        }

        if llm_calls > 0:
            details["llm_calls"] = llm_calls

        self._log_info(f"[{self.batch_id}] [Entity] Entity extraction", details)

        self.log_phase_end(
            IngestionPhase.ENTITY_EXTRACTION,
            triggered=True,
            items_in=segments_count,
            items_out=entities_found,
            llm_calls=llm_calls,
            **details,
        )

    def log_facet_generation(
        self,
        method: str,  # "section_based" | "llm_based"
        facets_created: int,
        llm_calls: int = 0,
    ):
        """Log Facet generation."""
        self.log_phase_start(IngestionPhase.FACET_GENERATION)

        self.metrics.facets_created += facets_created

        details = {
            "method": method,
            "facets": facets_created,
        }

        if llm_calls > 0:
            details["llm_calls"] = llm_calls

        self._log_info(f"[{self.batch_id}] [Facet] Facet generation", details)

        self.log_phase_end(
            IngestionPhase.FACET_GENERATION,
            triggered=True,
            items_out=facets_created,
            llm_calls=llm_calls,
            **details,
        )

    def log_semantic_merge(
        self,
        enabled: bool,
        facets_before: int = 0,
        facets_after: int = 0,
        merged_count: int = 0,
    ):
        """Log semantic merge."""
        self.log_phase_start(IngestionPhase.SEMANTIC_MERGE)

        self.metrics.semantic_merge_used = enabled

        if not enabled:
            self._log_debug(f"[{self.batch_id}] [SemanticMerge] Semantic merge: disabled")
            self.log_phase_end(IngestionPhase.SEMANTIC_MERGE, triggered=False, enabled=False)
            return

        details = {
            "before": facets_before,
            "after": facets_after,
            "merged": merged_count,
        }

        if merged_count > 0:
            self._log_info(f"[{self.batch_id}] [SemanticMerge] Semantic merge", details)

        self.log_phase_end(
            IngestionPhase.SEMANTIC_MERGE,
            triggered=merged_count > 0,
            items_in=facets_before,
            items_out=facets_after,
            **details,
        )

    def log_facet_points(
        self,
        enabled: bool,
        facets_processed: int = 0,
        points_created: int = 0,
        llm_calls: int = 0,
    ):
        """Log FacetPoint extraction."""
        self.log_phase_start(IngestionPhase.FACET_POINTS)

        self.metrics.facet_points_enabled = enabled

        if not enabled:
            self._log_debug(f"[{self.batch_id}] [FacetPoint] FacetPoint extraction: disabled")
            self.log_phase_end(IngestionPhase.FACET_POINTS, triggered=False, enabled=False)
            return

        self.metrics.facet_points_created += points_created

        details = {
            "facets": facets_processed,
            "points": points_created,
        }

        if llm_calls > 0:
            details["llm_calls"] = llm_calls

        self._log_info(f"[{self.batch_id}] [FacetPoint] FacetPoint extraction", details)

        self.log_phase_end(
            IngestionPhase.FACET_POINTS,
            triggered=True,
            items_in=facets_processed,
            items_out=points_created,
            llm_calls=llm_calls,
            **details,
        )

    def log_entity_selection(
        self,
        candidates: int,
        selected: int,
        llm_calls: int = 0,
    ):
        """Log entity selection."""
        self.log_phase_start(IngestionPhase.ENTITY_SELECTION)

        details = {
            "candidates": candidates,
            "selected": selected,
        }

        if llm_calls > 0:
            details["llm_calls"] = llm_calls

        self._log_info(f"[{self.batch_id}] [Entity] Entity selection", details)

        self.log_phase_end(
            IngestionPhase.ENTITY_SELECTION,
            triggered=True,
            items_in=candidates,
            items_out=selected,
            llm_calls=llm_calls,
            **details,
        )

    def log_entity_description(
        self,
        entities_count: int,
        llm_calls: int = 0,
    ):
        """Log entity description generation."""
        self.log_phase_start(IngestionPhase.ENTITY_DESCRIPTION)

        self.metrics.entities_created += entities_count

        details = {
            "entities": entities_count,
        }

        if llm_calls > 0:
            details["llm_calls"] = llm_calls

        self._log_info(f"[{self.batch_id}] [Entity] Entity description", details)

        self.log_phase_end(
            IngestionPhase.ENTITY_DESCRIPTION,
            triggered=True,
            items_out=entities_count,
            llm_calls=llm_calls,
            **details,
        )

    def log_graph_build(
        self,
        episodes: int,
        facets: int,
        facet_points: int,
        entities: int,
        edges: int,
    ):
        """Log graph structure construction."""
        self.log_phase_start(IngestionPhase.GRAPH_BUILD)

        self.metrics.edges_created += edges

        details = {
            "episodes": episodes,
            "facets": facets,
            "points": facet_points,
            "entities": entities,
            "edges": edges,
        }

        self._log_info(f"[{self.batch_id}] [Graph] Graph structure construction", details)

        self.log_phase_end(IngestionPhase.GRAPH_BUILD, triggered=True, items_out=edges, **details)

    def log_same_entity_edges(
        self,
        edges_created: int,
    ):
        """Log same_entity_as edge writing."""
        self.log_phase_start(IngestionPhase.SAME_ENTITY_EDGES)

        if edges_created == 0:
            self._log_debug(f"[{self.batch_id}] [SameConcept] same_entity_as edges: none")
            self.log_phase_end(IngestionPhase.SAME_ENTITY_EDGES, triggered=False, edges=0)
            return

        self._log_info(f"[{self.batch_id}] [SameConcept] same_entity_as edges", {"edges": edges_created})

        self.log_phase_end(
            IngestionPhase.SAME_ENTITY_EDGES,
            triggered=True,
            items_out=edges_created,
            edges=edges_created,
        )

    def log_llm_call(
        self,
        phase: str,
        call_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float = 0.0,
    ):
        """Log single LLM call."""
        self.metrics.llm_input_tokens += input_tokens
        self.metrics.llm_output_tokens += output_tokens

        self._log_debug(
            f"[{self.batch_id}] [LLM] LLM: {call_type}",
            {
                "phase": phase,
                "in_tokens": input_tokens,
                "out_tokens": output_tokens,
                "duration_ms": duration_ms,
            },
        )

    # ============================================================
    # Completion and summary
    # ============================================================

    def log_complete(self):
        """Log ingestion completion and output summary."""
        self.metrics.end_time = time.time()
        self.metrics.calculate_total()

        # Build summary
        summary = self._build_summary()

        self._log_info(
            f"[{self.batch_id}] [Complete] Ingestion completed",
            {
                "total_ms": round(self.metrics.total_duration_ms, 1),
                "episodes": self.metrics.episodes_created + self.metrics.episodes_updated,
                "facets": self.metrics.facets_created,
                "entities": self.metrics.entities_created,
                "llm_calls": self.metrics.total_llm_calls,
            },
        )

        # Output detailed summary
        self._log_info(f"[{self.batch_id}] [Summary] Ingestion summary:\n{summary}")

        return self.metrics

    def _build_summary(self) -> str:
        """Build ingestion summary report."""
        m = self.metrics
        lines = [
            "=" * 60,
            f"  Document: {m.doc_title or m.doc_id}",
            f"  Total duration: {m.total_duration_ms:.1f}ms",
            "-" * 60,
            "  Phase duration:",
        ]

        for phase_name, phase in m.phases.items():
            status = "[OK]" if phase.triggered else "[SKIP]"
            llm_info = f" (LLM×{phase.llm_calls})" if phase.llm_calls > 0 else ""
            lines.append(f"    {status} {phase_name}: {phase.duration_ms:.1f}ms{llm_info}")

        lines.extend(
            [
                "-" * 60,
                "  Key metrics:",
                f"    Episode: {m.episodes_created} created + {m.episodes_updated} updated",
                f"    Facet: {m.facets_created}",
                f"    FacetPoint: {m.facet_points_created}",
                f"    Entity: {m.entities_created}",
                f"    Edge: {m.edges_created}",
                "-" * 60,
                "  LLM calls:",
                f"    Total: {m.total_llm_calls}",
                f"    Input tokens: {m.llm_input_tokens}",
                f"    Output tokens: {m.llm_output_tokens}",
                "-" * 60,
                "  Logical branches:",
                f"    Routing decision: {m.routing_decision or 'N/A'}",
                f"    Semantic merge: {'[ON]' if m.semantic_merge_used else '[OFF]'}",
                f"    FacetPoint: {'[ON]' if m.facet_points_enabled else '[OFF]'}",
                "=" * 60,
            ]
        )

        return "\n".join(lines)

    def log_error(self, phase: str, error: Exception):
        """Log error."""
        self._log_warning(f"[{self.batch_id}] [Error] {phase} error", {"error": str(error)[:100]})


# ============================================================
# Convenience functions
# ============================================================


def create_ingestion_logger(doc_id: str, doc_title: str = "") -> IngestionLogger:
    """Create ingestion logger."""
    return IngestionLogger(doc_id, doc_title)
