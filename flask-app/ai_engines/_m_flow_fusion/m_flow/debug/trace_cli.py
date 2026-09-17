#!/usr/bin/env python3
# m_flow/debug/trace_cli.py
"""
P6-4: Trace CLI

Reads trace files and displays aggregated information.

Usage:
    python -m m_flow.debug.trace_cli --trace_id <id>
    python -m m_flow.debug.trace_cli --trace_id <id> --tail 50
    python -m m_flow.debug.trace_cli --list  # List recent traces
"""

import argparse
import glob
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any


def find_trace_file(base_dir: str, trace_id: str) -> str:
    """Find trace file."""
    pattern = os.path.join(base_dir, "*", f"{trace_id}.jsonl")
    hits = glob.glob(pattern)
    if not hits:
        raise FileNotFoundError(f"trace file not found for trace_id={trace_id}, pattern={pattern}")
    return hits[0]


def list_recent_traces(base_dir: str, limit: int = 20) -> List[Dict[str, Any]]:
    """List recent trace files."""
    pattern = os.path.join(base_dir, "*", "*.jsonl")
    files = glob.glob(pattern)

    traces = []
    for f in files:
        try:
            stat = os.stat(f)
            trace_id = os.path.basename(f).replace(".jsonl", "")
            traces.append(
                {
                    "trace_id": trace_id,
                    "path": f,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
            )
        except Exception:
            continue

    # Sort by modification time
    traces.sort(key=lambda x: -x["mtime"])
    return traces[:limit]


def load_events(path: str) -> List[Dict[str, Any]]:
    """Load trace events."""
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def print_trace_summary(events: List[Dict[str, Any]]) -> None:
    """Print trace summary."""
    if not events:
        print("No events found.")
        return

    # Time range
    ts_list = [e.get("ts_ms", 0) for e in events]
    start_ts = min(ts_list)
    end_ts = max(ts_list)
    duration_ms = end_ts - start_ts

    print("\n[STATS] Trace Summary")
    print(f"   Events: {len(events)}")
    print(f"   Duration: {duration_ms}ms")
    print(f"   Start: {datetime.fromtimestamp(start_ts / 1000).strftime('%H:%M:%S.%f')[:-3]}")
    print(f"   End: {datetime.fromtimestamp(end_ts / 1000).strftime('%H:%M:%S.%f')[:-3]}")

    # Count by name
    cnt = defaultdict(int)
    for e in events:
        cnt[e.get("name")] += 1

    print("\n[CHART] Event Counts (top 20):")
    top_names = sorted(cnt.items(), key=lambda x: -x[1])[:20]
    for name, c in top_names:
        print(f"   {c:>4}  {name}")


def print_events(events: List[Dict[str, Any]], tail: int = 100) -> None:
    """Print event details."""
    print(f"\n[NOTE] Events (last {min(tail, len(events))}):")
    print("-" * 80)

    for e in events[-tail:]:
        name = e.get("name", "")
        ts = e.get("ts_ms", 0)
        data = e.get("data", {})

        ts_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M:%S.%f")[:-3]
        print(f"[{ts_str}] {name}")

        if isinstance(data, dict):
            # Priority fields displayed first
            priority_keys = [
                "query",
                "top",
                "selected",
                "reason",
                "dur_ms",
                "collections",
                "triggered",
                "score",
                "count",
                "atomic_count",
                "episodic_count",
                "procedural_count",
            ]
            for k in priority_keys:
                if k in data:
                    val = data[k]
                    if isinstance(val, str) and len(val) > 100:
                        val = val[:100] + "..."
                    print(f"   {k}: {val}")

            # Other fields
            for k, v in data.items():
                if k not in priority_keys:
                    if isinstance(v, str) and len(v) > 60:
                        v = v[:60] + "..."
                    print(f"   {k}: {v}")
        else:
            print(f"   data: {data}")
        print()


def main():
    ap = argparse.ArgumentParser(description="Mflow Trace CLI")
    ap.add_argument("--trace_id", help="Trace ID to view")
    ap.add_argument("--dir", default=os.getenv("MFLOW_TRACE_DIR", ".m_flow_traces"), help="Trace directory")
    ap.add_argument("--tail", type=int, default=100, help="Number of events to show")
    ap.add_argument("--list", action="store_true", help="List recent traces")
    ap.add_argument("--summary", action="store_true", help="Show summary only")
    args = ap.parse_args()

    if args.list:
        traces = list_recent_traces(args.dir)
        if not traces:
            print("No traces found.")
            return

        print(f"\n[LIST] Recent Traces ({len(traces)}):")
        print("-" * 80)
        for t in traces:
            mtime_str = datetime.fromtimestamp(t["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   {t['trace_id']}  {mtime_str}  {t['size']:>8} bytes")
        return

    if not args.trace_id:
        ap.print_help()
        return

    try:
        path = find_trace_file(args.dir, args.trace_id)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    print(f"\n[SEARCH] Trace: {args.trace_id}")
    print(f"   File: {path}")

    events = load_events(path)
    print_trace_summary(events)

    if not args.summary:
        print_events(events, args.tail)


if __name__ == "__main__":
    main()
