# m_flow/tests/unit/tasks/episodic/test_context_isolation.py
"""
Step 1 validation test: Global variable thread safety.

Test contextvars coroutine isolation feature to ensure data doesn't interfere during concurrent Pipeline execution.
"""

import pytest
import asyncio
from typing import List


class TestContextIsolation:
    """Test coroutine isolation of context variables."""

    @pytest.mark.asyncio
    async def test_same_entity_edges_isolation(self):
        """Test same_entity_as edge isolation in different coroutines."""
        from m_flow.memory.episodic.context_vars import (
            add_pending_same_entity_edge,
            get_and_clear_pending_same_entity_edges,
        )

        results: List[List] = [[], []]

        async def coroutine_1():
            """Coroutine 1: Add edge_1."""
            add_pending_same_entity_edge({"source": "a1", "target": "b1"})
            add_pending_same_entity_edge({"source": "a2", "target": "b2"})
            await asyncio.sleep(0.01)  # Yield control
            edges = get_and_clear_pending_same_entity_edges()
            results[0] = edges

        async def coroutine_2():
            """Coroutine 2: Add edge_2."""
            add_pending_same_entity_edge({"source": "x1", "target": "y1"})
            await asyncio.sleep(0.01)  # Yield control
            edges = get_and_clear_pending_same_entity_edges()
            results[1] = edges

        # Execute concurrently
        await asyncio.gather(coroutine_1(), coroutine_2())

        # Verify isolation
        assert len(results[0]) == 2, "Coroutine 1 should have 2 edges"
        assert len(results[1]) == 1, "Coroutine 2 should have 1 edge"

        # Verify data correctness
        assert results[0][0]["source"] == "a1"
        assert results[0][1]["source"] == "a2"
        assert results[1][0]["source"] == "x1"

        print("✅ same_entity_as edge coroutine isolation test passed")

    @pytest.mark.asyncio
    async def test_clear_does_not_affect_other_coroutines(self):
        """Test that clear operation doesn't affect other coroutines."""
        from m_flow.memory.episodic.context_vars import (
            add_pending_same_entity_edge,
            get_and_clear_pending_same_entity_edges,
        )

        event_1_added = asyncio.Event()
        event_2_cleared = asyncio.Event()
        results: List[List] = [[], []]

        async def coroutine_1():
            """Coroutine 1: Add first, wait for coroutine 2 to clear, then read."""
            add_pending_same_entity_edge({"source": "keep_me", "target": "safe"})
            event_1_added.set()
            await event_2_cleared.wait()  # Wait for coroutine 2 to clear
            # Clear operation should not affect coroutine 1's data
            edges = get_and_clear_pending_same_entity_edges()
            results[0] = edges

        async def coroutine_2():
            """Coroutine 2: Add then clear."""
            await event_1_added.wait()  # Wait for coroutine 1 to add
            add_pending_same_entity_edge({"source": "will_be_cleared", "target": "gone"})
            edges = get_and_clear_pending_same_entity_edges()  # Clear
            results[1] = edges
            event_2_cleared.set()

        await asyncio.gather(coroutine_1(), coroutine_2())

        # Verify coroutine 1's data not affected by coroutine 2's clear
        assert len(results[0]) == 1, "Coroutine 1's data should be preserved"
        assert results[0][0]["source"] == "keep_me"

        # Verify coroutine 2 cleared normally
        assert len(results[1]) == 1
        assert results[1][0]["source"] == "will_be_cleared"

        print("✅ Clear operation isolation test passed")

    @pytest.mark.asyncio
    async def test_sequential_pipeline_simulation(self):
        """Simulate sequential Pipeline execution (single coroutine)."""
        from m_flow.memory.episodic.context_vars import (
            add_pending_same_entity_edge,
            get_and_clear_pending_same_entity_edges,
        )

        # Simulate write_episodic_memories adding data
        add_pending_same_entity_edge({"source": "e1", "target": "e2"})

        # Simulate write_same_entity_edges reading and clearing
        edges = get_and_clear_pending_same_entity_edges()
        assert len(edges) == 1
        assert edges[0]["source"] == "e1"

        # Verify empty after clear
        assert len(get_and_clear_pending_same_entity_edges()) == 0

        print("✅ Sequential Pipeline simulation test passed")


if __name__ == "__main__":
    # Run tests directly
    import sys

    async def run_tests():
        test = TestContextIsolation()

        print("=" * 70)
        print("Step 1 unit test: Context variable isolation verification")
        print("=" * 70)

        try:
            await test.test_same_entity_edges_isolation()
            await test.test_clear_does_not_affect_other_coroutines()
            await test.test_sequential_pipeline_simulation()

            print()
            print("=" * 70)
            print("All tests passed!")
            print("=" * 70)
            return 0
        except AssertionError as e:
            print(f"Test failed: {e}")
            return 1
        except Exception as e:
            print(f"Test error: {e}")
            return 1

    sys.exit(asyncio.run(run_tests()))
