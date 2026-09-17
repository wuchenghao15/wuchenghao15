# m_flow/shared/tracing/sinks.py
"""
P6-1: Trace Sinks

JSONL file + in-memory ring buffer.
"""

from __future__ import annotations
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from .utils import dumps_json


@dataclass
class TraceEventRecord:
    """Single trace event record."""

    trace_id: str
    ts_ms: int
    name: str
    data: Dict[str, Any]


class TraceSink:
    """Trace sink base class."""

    def write(self, rec: TraceEventRecord) -> None:
        raise NotImplementedError


class JsonlTraceSink(TraceSink):
    """
    JSONL file sink.

    One file per trace to avoid concurrent write lock issues:
    base_dir/YYYYMMDD/<trace_id>.jsonl
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _path_for(self, trace_id: str) -> str:
        """Get trace file path."""
        day = time.strftime("%Y%m%d", time.localtime())
        d = os.path.join(self.base_dir, day)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"{trace_id}.jsonl")

    def write(self, rec: TraceEventRecord) -> None:
        """Write event to file."""
        path = self._path_for(rec.trace_id)
        line = dumps_json(
            {
                "trace_id": rec.trace_id,
                "ts_ms": rec.ts_ms,
                "name": rec.name,
                "data": rec.data,
            }
        )
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


class MemoryRingTraceSink(TraceSink):
    """
    In-memory ring buffer sink.

    For scenarios where "no disk writes but still debuggable".
    """

    def __init__(self, max_events: int = 2000):
        self.max_events = max_events
        self._events: List[TraceEventRecord] = []

    def write(self, rec: TraceEventRecord) -> None:
        """Write event to in-memory ring buffer."""
        self._events.append(rec)
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]

    def get_events(self, trace_id: str) -> List[TraceEventRecord]:
        """Get all events for specified trace."""
        return [e for e in self._events if e.trace_id == trace_id]

    def get_all_events(self) -> List[TraceEventRecord]:
        """Get all events."""
        return list(self._events)

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()


class MultiTraceSink(TraceSink):
    """Combine multiple sinks."""

    def __init__(self, sinks: List[TraceSink]):
        self.sinks = sinks

    def write(self, rec: TraceEventRecord) -> None:
        """Write to all sinks."""
        for sink in self.sinks:
            try:
                sink.write(rec)
            except Exception:
                pass  # Don't let single sink failure affect others
