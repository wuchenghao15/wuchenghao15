"""Benchmark graph extraction on a large model with circular references."""

from __future__ import annotations

import asyncio
import random
import time
from typing import List
from uuid import NAMESPACE_OID, uuid5

import pytest

from m_flow.core import MemoryNode
from m_flow.knowledge.graph_ops.utils import extract_graph

random.seed(1500)

NUM_MODULES = 1500
FRAGMENTS_PER_MODULE = 2


class Project(MemoryNode):
    location: str
    metadata: dict = {"index_fields": []}


class Module(MemoryNode):
    belongs_to: Project
    fragments: List["Fragment"] = []
    imports: List["Module"] = []
    content: str
    metadata: dict = {"index_fields": []}


class Fragment(MemoryNode):
    content: str
    metadata: dict = {"index_fields": []}


Module.model_rebuild()
Fragment.model_rebuild()


def _readable_duration(ns: float) -> str:
    thresholds = [
        (7 * 24 * 3600 * 1e9, "w"),
        (24 * 3600 * 1e9, "d"),
        (3600 * 1e9, "h"),
        (60 * 1e9, "min"),
        (1e9, "s"),
        (1e6, "ms"),
        (1e3, "us"),
    ]
    for divisor, label in thresholds:
        if ns >= divisor:
            return f"{ns / divisor:.2f}{label}"
    return f"{ns:.0f}ns"


def _pick_other(total: int, skip: int) -> int:
    candidate = skip
    while candidate == skip:
        candidate = random.randint(0, total - 1)
    return candidate


@pytest.mark.asyncio
async def test_circular_reference_extraction():
    project = Project(location="/src/project_alpha")

    modules = [
        Module(
            id=uuid5(NAMESPACE_OID, f"file{idx}"),
            content="source code",
            belongs_to=project,
            fragments=[],
            imports=[],
        )
        for idx in range(NUM_MODULES)
    ]

    for pos, mod in enumerate(modules):
        mod.imports.append(modules[_pick_other(NUM_MODULES, pos)])
        mod.imports.append(modules[_pick_other(NUM_MODULES, pos)])
        mod.fragments.extend(Fragment(part_of=mod, content=f"Part {k}") for k in range(FRAGMENTS_PER_MODULE))

    shared_nodes: dict = {}
    shared_edges: dict = {}
    seen_props: dict = {}

    t0 = time.perf_counter_ns()
    outcomes = await asyncio.gather(
        *(
            extract_graph(
                mod,
                added_nodes=shared_nodes,
                added_edges=shared_edges,
                visited_properties=seen_props,
            )
            for mod in modules
        )
    )
    duration = time.perf_counter_ns() - t0
    print(f"Graph extraction took {_readable_duration(duration)}")

    collected_nodes = [n for batch_nodes, _ in outcomes for n in batch_nodes]
    module_total = sum(1 for n in collected_nodes if n.type == "Module")
    fragment_total = sum(1 for n in collected_nodes if n.type == "Fragment")

    assert module_total == NUM_MODULES
    assert fragment_total == NUM_MODULES * FRAGMENTS_PER_MODULE


if __name__ == "__main__":
    asyncio.run(test_circular_reference_extraction())
