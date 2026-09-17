# m_flow/shared/tracing/manager.py
"""
TraceManager

Core trace manager:
- start/end: Start/end a trace
- event: Record events
- span: Auto-timing context manager
- Sampling, configuration, safe fallback
"""

from __future__ import annotations
import os
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .context import set_current_trace, get_current_trace, clear_current_trace
from .sinks import TraceSink, JsonlTraceSink, MemoryRingTraceSink, TraceEventRecord
from .utils import safe_payload


def _env_bool(name: str, default: bool = False) -> bool:
    """Read boolean from environment variable."""
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str, default: float) -> float:
    """Read float from environment variable."""
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


def _env_int(name: str, default: int) -> int:
    """Read integer from environment variable."""
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


@dataclass
class TraceConfig:
    """Trace configuration."""

    enabled: bool
    sample_rate: float
    base_dir: str
    max_str_len: int
    max_list_len: int


@dataclass
class TraceState:
    """Current trace state."""

    trace_id: str
    kind: str
    start_ts_ms: int
    cfg: TraceConfig
    sink: TraceSink


class TraceSpan:
    """
    Auto-timing span context manager.

    Usage:
        with TraceManager.span("my_operation", {"key": "value"}):
            do_something()
    """

    def __init__(self, name: str, data: Optional[Dict[str, Any]] = None):
        self.name = name
        self.data = data or {}
        self._t0: Optional[float] = None

    def __enter__(self) -> "TraceSpan":
        self._t0 = time.perf_counter()
        TraceManager.event(f"span.start:{self.name}", self.data)
        return self

    def __exit__(self, exc_type, exc, tb):
        dur_ms = int((time.perf_counter() - (self._t0 or time.perf_counter())) * 1000)
        d = dict(self.data)
        d["dur_ms"] = dur_ms
        if exc is not None:
            d["exc_type"] = str(getattr(exc_type, "__name__", "Exception"))
            d["exc"] = str(exc)[:300]
        TraceManager.event(f"span.end:{self.name}", d)
        return False  # Don't suppress exceptions


class TraceManager:
    """
    Global Trace manager.

    Core functions:
    - start(): Start new trace
    - end(): End current trace
    - event(): Record events
    - span(): Auto-timing context manager

    Configuration (environment variables):
    - MFLOW_TRACE_ENABLED: Whether enabled (default false)
    - MFLOW_TRACE_SAMPLE_RATE: Sample rate (default 1.0)
    - MFLOW_TRACE_DIR: Trace file directory (default .m_flow_traces)
    - MFLOW_TRACE_MAX_STR: Maximum string length (default 800)
    - MFLOW_TRACE_MAX_LIST: Maximum list length (default 50)
    """

    # Memory ring buffer (can debug even without disk writes)
    _mem_sink = MemoryRingTraceSink(max_events=5000)

    @staticmethod
    def _load_cfg() -> TraceConfig:
        """Load configuration from environment variables."""
        enabled = _env_bool("MFLOW_TRACE_ENABLED", False)
        sample_rate = _env_float("MFLOW_TRACE_SAMPLE_RATE", 1.0)
        base_dir = os.getenv("MFLOW_TRACE_DIR", ".m_flow_traces")
        max_str_len = _env_int("MFLOW_TRACE_MAX_STR", 800)
        max_list_len = _env_int("MFLOW_TRACE_MAX_LIST", 50)
        return TraceConfig(
            enabled=enabled,
            sample_rate=sample_rate,
            base_dir=base_dir,
            max_str_len=max_str_len,
            max_list_len=max_list_len,
        )

    @staticmethod
    def start(kind: str, meta: Optional[Dict[str, Any]] = None) -> Optional[TraceState]:
        """
        Start new trace.

        Args:
            kind: Trace type (e.g., "rag.retrieve", "procedural.write")
            meta: Metadata

        Returns:
            TraceState or None (if not enabled or not sampled)
        """
        cfg = TraceManager._load_cfg()

        if not cfg.enabled:
            return None

        if cfg.sample_rate < 1.0 and random.random() > cfg.sample_rate:
            return None

        trace_id = uuid.uuid4().hex[:16]
        start_ts_ms = int(time.time() * 1000)

        sink: TraceSink = JsonlTraceSink(cfg.base_dir)
        st = TraceState(
            trace_id=trace_id,
            kind=kind,
            start_ts_ms=start_ts_ms,
            cfg=cfg,
            sink=sink,
        )
        set_current_trace(st)

        TraceManager.event(
            "trace.start",
            {
                "kind": kind,
                "meta": meta or {},
                "cfg": {
                    "sample_rate": cfg.sample_rate,
                    "max_str_len": cfg.max_str_len,
                    "max_list_len": cfg.max_list_len,
                },
            },
        )
        return st

    @staticmethod
    def end(status: str = "ok", meta: Optional[Dict[str, Any]] = None) -> None:
        """
        End current trace.

        Args:
            status: Status ("ok" or "error")
            meta: Additional metadata
        """
        st = get_current_trace()
        if not st:
            return

        dur_ms = int(time.time() * 1000) - st.start_ts_ms
        TraceManager.event("trace.end", {"status": status, "dur_ms": dur_ms, "meta": meta or {}})
        clear_current_trace()

    @staticmethod
    def event(name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Record event.

        Args:
            name: Event name
            data: Event data
        """
        st = get_current_trace()
        if not st:
            return

        ts_ms = int(time.time() * 1000)
        payload = safe_payload(
            data or {},
            max_str_len=st.cfg.max_str_len,
            max_list_len=st.cfg.max_list_len,
            max_depth=5,
        )
        rec = TraceEventRecord(
            trace_id=st.trace_id,
            ts_ms=ts_ms,
            name=name,
            data=payload,
        )

        # Write to file sink
        try:
            st.sink.write(rec)
        except Exception:
            pass  # Don't let trace failure affect main logic

        # Also write to memory ring (for debugging)
        TraceManager._mem_sink.write(rec)

    @staticmethod
    def span(name: str, data: Optional[Dict[str, Any]] = None) -> TraceSpan:
        """
        Create auto-timing span.

        Usage:
            with TraceManager.span("my_operation"):
                do_something()
        """
        return TraceSpan(name, data or {})

    @staticmethod
    def current_trace_id() -> Optional[str]:
        """Get current trace ID (if any)."""
        st = get_current_trace()
        return st.trace_id if st else None

    @staticmethod
    def is_tracing() -> bool:
        """Whether currently tracing."""
        return get_current_trace() is not None

    @staticmethod
    def get_memory_events(trace_id: Optional[str] = None) -> list:
        """
        Get events in memory (for testing/debugging).

        Args:
            trace_id: Optional, specify trace ID

        Returns:
            List of events
        """
        if trace_id:
            return TraceManager._mem_sink.get_events(trace_id)
        return TraceManager._mem_sink.get_all_events()
