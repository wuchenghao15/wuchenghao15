# m_flow/shared/tracing/__init__.py
"""
P6: Mflow Tracing System

Observability and explainable Debug system.

Core components:
- TraceManager: Global trace manager
- TraceSpan: Auto-timed span
- get_current_trace: Get current trace

Usage:
    from m_flow.shared.tracing import TraceManager

    # Start trace
    TraceManager.start("rag.retrieve", meta={"query": "..."})

    # Record event
    TraceManager.event("my_event", {"key": "value"})

    # Auto-timed
    with TraceManager.span("my_operation"):
        do_something()

    # End trace
    TraceManager.end("ok")

Configuration (environment variables):
- MFLOW_TRACE_ENABLED=1: Enable tracing
- MFLOW_TRACE_SAMPLE_RATE=1.0: Sample rate
- MFLOW_TRACE_DIR=.m_flow_traces: Trace file directory
"""

from .manager import TraceManager, TraceSpan, TraceState, TraceConfig
from .context import get_current_trace, set_current_trace, clear_current_trace
from .sinks import TraceEventRecord, TraceSink, JsonlTraceSink, MemoryRingTraceSink

__all__ = [
    "TraceManager",
    "TraceSpan",
    "TraceState",
    "TraceConfig",
    "get_current_trace",
    "set_current_trace",
    "clear_current_trace",
    "TraceEventRecord",
    "TraceSink",
    "JsonlTraceSink",
    "MemoryRingTraceSink",
]
