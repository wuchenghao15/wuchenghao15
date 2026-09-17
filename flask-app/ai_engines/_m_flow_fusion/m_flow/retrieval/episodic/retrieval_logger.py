"""
Episodic Retrieval logging module.

Provides unified logging to ensure every stage of the retrieval process is traceable:
1. Input/output for each step
2. Trigger conditions for each logical branch
3. Performance metrics (duration, hit rate, etc.)

Log levels:
- INFO: Main process stages and key metrics
- DEBUG: Detailed data and intermediate results
- WARNING: Exceptions and fallback triggers

Usage:
    from .retrieval_logger import RetrievalLogger

    rlog = RetrievalLogger(query="What is NPS")
    rlog.log_step_start("vector_search")
    # ... execute vector search ...
    rlog.log_step_end("vector_search", hits=150, collections=5)
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from m_flow.shared.logging_utils import get_logger, INFO, DEBUG


class RetrievalStep(str, Enum):
    """Retrieval step enumeration."""

    INIT = "init"
    PREPROCESS = "preprocess"
    TIME_PARSE = "time_parse"  # Time parsing
    VECTOR_SEARCH = "vector_search"
    BONUS_APPLY = "bonus_apply"
    TIME_BONUS = "time_bonus"  # Time bonus application
    GRAPH_PROJECT = "graph_project"
    INDEX_BUILD = "index_build"
    BUNDLE_SCORE = "bundle_score"
    OUTPUT_ASSEMBLE = "output_assemble"
    COMPLETE = "complete"


@dataclass
class StepMetrics:
    """Single step metrics."""

    step: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    input_count: int = 0
    output_count: int = 0
    triggered: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def calculate_duration(self):
        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class RetrievalMetrics:
    """Complete retrieval metrics."""

    query: str = ""
    query_length: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    total_duration_ms: float = 0.0

    # Metrics per step
    steps: Dict[str, StepMetrics] = field(default_factory=dict)

    # Key metrics
    total_vector_hits: int = 0
    unique_node_ids: int = 0
    episodes_found: int = 0
    bundles_computed: int = 0
    top_bundles: int = 0
    output_edges: int = 0

    # Logical branches
    hybrid_search_used: bool = False
    hybrid_reason: Optional[str] = None
    fallback_triggered: bool = False

    # Time enhancement metrics
    time_parse_used: bool = False
    time_confidence: float = 0.0
    time_matched_spans: List[str] = field(default_factory=list)
    time_bonus_matched: int = 0

    def calculate_total(self):
        if self.start_time and self.end_time:
            self.total_duration_ms = (self.end_time - self.start_time) * 1000


class RetrievalLogger:
    """
    Retrieval logging.

    Provides structured logging supporting:
    - Step start/end markers
    - Detailed metrics recording
    - Final summary report
    """

    def __init__(self, query: str, session_id: Optional[str] = None):
        self.query = query
        self.session_id = session_id or f"S{int(time.time() * 1000) % 100000}"
        self.metrics = RetrievalMetrics(
            query=query[:100],  # Truncate
            query_length=len(query),
            start_time=time.time(),
        )

        # Loggers - use INFO level to ensure output
        self._info_logger = get_logger(name="m_flow.retrieval.info", level=INFO)
        self._debug_logger = get_logger(name="m_flow.retrieval.debug", level=DEBUG)

        self._log_info(
            f"[{self.session_id}] [Retrieval] Retrieval started",
            {
                "query": query[:50] + ("..." if len(query) > 50 else ""),
                "query_length": len(query),
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
        for k, v in data.items():
            if isinstance(v, float):
                parts.append(f"{k}={v:.2f}")
            elif isinstance(v, list):
                parts.append(f"{k}=[{len(v)} items]")
            elif isinstance(v, dict):
                parts.append(f"{k}={{{len(v)} keys}}")
            else:
                parts.append(f"{k}={v}")
        return ", ".join(parts)

    # ============================================================
    # Step logging methods
    # ============================================================

    def log_step_start(self, step: str):
        """Log step start."""
        self.metrics.steps[step] = StepMetrics(
            step=step,
            start_time=time.time(),
        )
        self._log_debug(f"[{self.session_id}] [Step] {step} started")

    def log_step_end(self, step: str, triggered: bool = True, **kwargs):
        """Log step end."""
        if step in self.metrics.steps:
            m = self.metrics.steps[step]
            m.end_time = time.time()
            m.calculate_duration()
            m.triggered = triggered
            m.details.update(kwargs)

            if "input_count" in kwargs:
                m.input_count = kwargs["input_count"]
            if "output_count" in kwargs:
                m.output_count = kwargs["output_count"]

            self._log_info(
                f"[{self.session_id}] [OK] {step} completed",
                {"duration_ms": m.duration_ms, **kwargs},
            )

    # ============================================================
    # Specific step logging
    # ============================================================

    def log_preprocess(
        self,
        original: str,
        vector_query: str,
        use_hybrid: bool,
        hybrid_reason: Optional[str],
        keyword: str,
    ):
        """Log query preprocessing."""
        self.log_step_start(RetrievalStep.PREPROCESS)

        self.metrics.hybrid_search_used = use_hybrid
        self.metrics.hybrid_reason = hybrid_reason

        details = {
            "original_len": len(original),
            "vector_query_len": len(vector_query),
            "stripped": original != vector_query,
            "use_hybrid": use_hybrid,
            "hybrid_reason": hybrid_reason or "none",
            "keyword": keyword[:20] if keyword else "",
        }

        if use_hybrid:
            self._log_info(
                f"[{self.session_id}] [Hybrid] Hybrid search enabled",
                {"reason": hybrid_reason, "keyword": keyword[:20]},
            )

        self.log_step_end(RetrievalStep.PREPROCESS, triggered=True, **details)

    def log_time_parse(
        self,
        found: bool,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        confidence: float = 0.0,
        matched_spans: Optional[List[str]] = None,
    ):
        """Log time parsing results."""
        self.log_step_start(RetrievalStep.TIME_PARSE)

        self.metrics.time_parse_used = found
        self.metrics.time_confidence = confidence
        self.metrics.time_matched_spans = matched_spans or []

        details = {
            "found": found,
            "confidence": confidence,
            "matched_spans": matched_spans[:3] if matched_spans else [],
        }

        if found:
            # Convert to readable time if needed
            from datetime import datetime, timezone

            try:
                if start_ms:
                    start_str = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                    end_str = (
                        datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if end_ms else "?"
                    )
                    details["range"] = f"{start_str} ~ {end_str}"
            except Exception:
                pass

            self._log_info(
                f"[{self.session_id}] [Time] Time parsing",
                {"conf": round(confidence, 2), "spans": matched_spans[:2] if matched_spans else []},
            )

        self.log_step_end(RetrievalStep.TIME_PARSE, triggered=found, **details)

    def log_time_bonus(
        self,
        bundles: int = 0,
        matched: int = 0,
        mentioned_time_matched: int = 0,
        created_at_matched: int = 0,
        avg_bonus: float = 0.0,
        max_bonus: float = 0.0,
    ):
        """Log time bonus application."""
        self.log_step_start(RetrievalStep.TIME_BONUS)

        self.metrics.time_bonus_matched = matched
        triggered = matched > 0

        details = {
            "bundles": bundles,
            "matched": matched,
            "mentioned_time_matched": mentioned_time_matched,
            "created_at_matched": created_at_matched,
            "avg_bonus": avg_bonus,
            "max_bonus": max_bonus,
        }

        if triggered:
            self._log_info(
                f"[{self.session_id}] [Time] Time bonus",
                {"matched": matched, "avg": round(avg_bonus, 3), "max": round(max_bonus, 3)},
            )

        self.log_step_end(RetrievalStep.TIME_BONUS, triggered=triggered, **details)

    def log_vector_search(
        self,
        collections: List[str],
        results_by_collection: Dict[str, int],
        total_hits: int,
        unique_ids: int,
    ):
        """Log vector search."""
        self.log_step_start(RetrievalStep.VECTOR_SEARCH)

        self.metrics.total_vector_hits = total_hits
        self.metrics.unique_node_ids = unique_ids

        # Record by collection
        collection_details = []
        for c in collections:
            hits = results_by_collection.get(c, 0)
            if hits > 0:
                collection_details.append(f"{c.split('_')[0]}:{hits}")

        details = {
            "collections": len(collections),
            "total_hits": total_hits,
            "unique_ids": unique_ids,
            "per_collection": ", ".join(collection_details[:5]),
        }

        self._log_debug(
            f"[{self.session_id}] [VectorSearch] Vector search details",
            {"hits_by_col": results_by_collection},
        )

        self.log_step_end(
            RetrievalStep.VECTOR_SEARCH,
            triggered=total_hits > 0,
            input_count=len(collections),
            output_count=unique_ids,
            **details,
        )

    def log_bonus_apply(
        self,
        keyword_matches: int = 0,
        exact_matches: int = 0,
        number_matches: int = 0,
        english_matches: int = 0,
    ):
        """Log bonus application."""
        self.log_step_start(RetrievalStep.BONUS_APPLY)

        total_bonuses = keyword_matches + exact_matches + number_matches + english_matches
        triggered = total_bonuses > 0

        details = {
            "keyword_matches": keyword_matches,
            "exact_matches": exact_matches,
            "number_matches": number_matches,
            "english_matches": english_matches,
            "total_bonuses": total_bonuses,
        }

        if triggered:
            self._log_info(
                f"[{self.session_id}] [Bonus] Exact match bonus",
                {"keyword": keyword_matches, "exact": exact_matches, "number": number_matches},
            )

        self.log_step_end(RetrievalStep.BONUS_APPLY, triggered=triggered, **details)

    def log_graph_projection(
        self,
        phase: int,
        input_ids: int,
        projected_nodes: int,
        projected_edges: int,
        expanded_ids: int = 0,
    ):
        """Log graph projection."""
        step_name = f"{RetrievalStep.GRAPH_PROJECT}_p{phase}"
        self.log_step_start(step_name)

        details = {
            "phase": phase,
            "input_ids": input_ids,
            "nodes": projected_nodes,
            "edges": projected_edges,
        }

        if phase == 2 and expanded_ids > 0:
            details["expanded_ids"] = expanded_ids
            self._log_debug(
                f"[{self.session_id}] [Graph] Graph projection expansion",
                {"from": input_ids, "to": expanded_ids},
            )

        self.log_step_end(
            step_name,
            triggered=projected_edges > 0,
            input_count=input_ids,
            output_count=projected_edges,
            **details,
        )

    def log_index_build(
        self,
        episodes: int,
        facets: int,
        points: int,
        entities: int,
    ):
        """Log relationship index construction."""
        self.log_step_start(RetrievalStep.INDEX_BUILD)

        self.metrics.episodes_found = episodes

        details = {
            "episodes": episodes,
            "facets": facets,
            "points": points,
            "entities": entities,
        }

        self._log_info(
            f"[{self.session_id}] [Index] Relationship index",
            {"ep": episodes, "fa": facets, "pt": points, "en": entities},
        )

        self.log_step_end(RetrievalStep.INDEX_BUILD, triggered=episodes > 0, output_count=episodes, **details)

    def log_bundle_scoring(
        self,
        total_bundles: int,
        top_k: int,
        top_bundles: List[Dict[str, Any]],  # [{episode_id, score, path}, ...]
    ):
        """Log Bundle scoring."""
        self.log_step_start(RetrievalStep.BUNDLE_SCORE)

        self.metrics.bundles_computed = total_bundles
        self.metrics.top_bundles = min(top_k, total_bundles)

        # Analyze best path distribution
        path_counts = {}
        for b in top_bundles:
            path = b.get("path", "unknown")
            path_counts[path] = path_counts.get(path, 0) + 1

        details = {
            "total": total_bundles,
            "top_k": top_k,
            "returned": len(top_bundles),
            "paths": path_counts,
        }

        if top_bundles:
            best = top_bundles[0]
            self._log_info(
                f"[{self.session_id}] [Bundle] Best Bundle",
                {
                    "episode": best.get("episode_id", "")[:20],
                    "score": round(best.get("score", 0), 4),
                    "path": best.get("path", ""),
                },
            )

        self.log_step_end(
            RetrievalStep.BUNDLE_SCORE,
            triggered=total_bundles > 0,
            input_count=self.metrics.episodes_found,
            output_count=len(top_bundles),
            **details,
        )

    def log_output_assemble(
        self,
        input_bundles: int,
        output_edges: int,
        max_facets_per_ep: int,
        max_points_per_facet: int,
    ):
        """Log output assembly."""
        self.log_step_start(RetrievalStep.OUTPUT_ASSEMBLE)

        self.metrics.output_edges = output_edges

        details = {
            "bundles": input_bundles,
            "edges": output_edges,
            "max_facets": max_facets_per_ep,
            "max_points": max_points_per_facet,
        }

        self.log_step_end(
            RetrievalStep.OUTPUT_ASSEMBLE,
            triggered=output_edges > 0,
            input_count=input_bundles,
            output_count=output_edges,
            **details,
        )

    # ============================================================
    # Completion and summary
    # ============================================================

    def log_complete(self, output_count: int):
        """Log retrieval completion and output summary."""
        self.metrics.end_time = time.time()
        self.metrics.calculate_total()
        self.metrics.output_edges = output_count

        # Build summary
        summary = self._build_summary()

        self._log_info(
            f"[{self.session_id}] [Complete] Retrieval completed",
            {
                "total_ms": round(self.metrics.total_duration_ms, 1),
                "output_edges": output_count,
                "episodes": self.metrics.top_bundles,
            },
        )

        # Output detailed summary
        self._log_info(f"[{self.session_id}] [Summary] Retrieval summary:\n{summary}")

        return self.metrics

    def _build_summary(self) -> str:
        """Build retrieval summary report."""
        m = self.metrics
        lines = [
            "=" * 60,
            f"  Query: {m.query}",
            f"  Total duration: {m.total_duration_ms:.1f}ms",
            "-" * 60,
            "  Step duration:",
        ]

        for step_name, step in m.steps.items():
            status = "[OK]" if step.triggered else "[SKIP]"
            lines.append(
                f"    {status} {step_name}: {step.duration_ms:.1f}ms (in={step.input_count}, out={step.output_count})"
            )

        lines.extend(
            [
                "-" * 60,
                "  Key metrics:",
                f"    Vector hits: {m.total_vector_hits} (unique IDs: {m.unique_node_ids})",
                f"    Episodes found: {m.episodes_found}",
                f"    Bundles computed: {m.bundles_computed} -> Top {m.top_bundles}",
                f"    Output edges: {m.output_edges}",
                "-" * 60,
                "  Logical branches:",
                f"    Hybrid search: {'[ON] ' + (m.hybrid_reason or '') if m.hybrid_search_used else '[OFF]'}",
                f"    Fallback: {'[TRIGGERED]' if m.fallback_triggered else '[NOT TRIGGERED]'}",
                f"    Time enhancement: {'conf=' + str(round(m.time_confidence, 2)) + ', matched=' + str(m.time_bonus_matched) if m.time_parse_used else '[OFF]'}",
                "=" * 60,
            ]
        )

        return "\n".join(lines)

    def log_error(self, step: str, error: Exception):
        """Log error."""
        self._log_warning(f"[{self.session_id}] [Error] {step} error", {"error": str(error)[:100]})


# ============================================================
# Convenience functions
# ============================================================


def create_retrieval_logger(query: str) -> RetrievalLogger:
    """Create retrieval logger."""
    return RetrievalLogger(query)
