"""Create nodes with multiple typed edges, some weighted, some not."""

import asyncio
from typing import Any
from pydantic import SkipValidation
from m_flow.api.v1.visualize.visualize import visualize_graph
from m_flow.core import MemoryNode
from m_flow.core.models.Edge import Edge
from m_flow.storage import persist_memory_nodes
import m_flow


class Student(MemoryNode):
    name: str
    major: str


class Course(MemoryNode):
    title: str
    credits: int
    enrolled: SkipValidation[Any]  # Mixed: students with/without grade weights


async def run():
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Students
    alice = Student(name="Alice Chen", major="Computer Science")
    bob = Student(name="Bob Martinez", major="Mathematics")
    carol = Student(name="Carol Kim", major="Physics")

    # Courses with mixed edge types
    algorithms = Course(
        title="Algorithms",
        credits=4,
        enrolled=[
            (Edge(relationship_name="enrolled_in", weight=92), alice),  # with grade
            (Edge(relationship_name="enrolled_in", weight=88), bob),
            carol,  # no weight
        ],
    )
    calculus = Course(
        title="Calculus III",
        credits=3,
        enrolled=[
            (Edge(relationship_name="enrolled_in", weight=95), alice),
            bob,
        ],
    )
    quantum = Course(
        title="Quantum Mechanics",
        credits=4,
        enrolled=[
            (Edge(relationship_name="enrolled_in", weight=91), carol),
        ],
    )

    all_nodes = [alice, bob, carol, algorithms, calculus, quantum]
    await persist_memory_nodes(all_nodes)

    print(f"Created {len(all_nodes)} nodes with mixed edge types.")
    await visualize_graph()


if __name__ == "__main__":
    asyncio.run(run())
