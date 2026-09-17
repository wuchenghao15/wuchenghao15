# m_flow/tests/unit/pipelines/test_run_parallel.py
"""
Unit tests for execute_parallel function.

Tests cover:
- Basic parallel execution
- Result merging
- Deduplication based on MemoryNode.id
- Exception handling
- Edge cases (empty tasks, single task)
"""

import asyncio
import pytest
from dataclasses import dataclass
from uuid import uuid4

from m_flow.pipeline.operations.execute_parallel import execute_parallel
from m_flow.pipeline.tasks import Stage


@dataclass
class MockMemoryNode:
    """Mock MemoryNode for testing deduplication."""

    id: str
    value: str


class TestRunTasksParallel:
    """Tests for execute_parallel function."""

    @pytest.mark.asyncio
    async def test_basic_parallel_execution(self):
        """Test basic parallel execution of multiple tasks."""

        async def task_a(*args, **kwargs):
            await asyncio.sleep(0.01)
            return [{"id": "a1", "value": "from_a"}]

        async def task_b(*args, **kwargs):
            await asyncio.sleep(0.01)
            return [{"id": "b1", "value": "from_b"}]

        parallel_task = execute_parallel(
            [
                Stage(task_a),
                Stage(task_b),
            ]
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        assert len(result) == 2
        ids = [item["id"] for item in result]
        assert "a1" in ids
        assert "b1" in ids

    @pytest.mark.asyncio
    async def test_deduplication_with_datapoint(self):
        """Test deduplication based on MemoryNode.id attribute."""
        shared_id = str(uuid4())

        async def task_a(*args, **kwargs):
            return [MockMemoryNode(id=shared_id, value="from_a")]

        async def task_b(*args, **kwargs):
            return [MockMemoryNode(id=shared_id, value="from_b")]

        parallel_task = execute_parallel(
            [
                Stage(task_a),
                Stage(task_b),
            ],
            deduplicate=True,
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        # Should only have 1 item due to deduplication
        assert len(result) == 1
        assert result[0].id == shared_id

    @pytest.mark.asyncio
    async def test_deduplication_with_dict(self):
        """Test deduplication based on dict['id'] key."""
        shared_id = "shared-123"

        async def task_a(*args, **kwargs):
            return [{"id": shared_id, "source": "a"}]

        async def task_b(*args, **kwargs):
            return [{"id": shared_id, "source": "b"}]

        parallel_task = execute_parallel(
            [
                Stage(task_a),
                Stage(task_b),
            ],
            deduplicate=True,
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        # Should only have 1 item due to deduplication
        assert len(result) == 1
        assert result[0]["id"] == shared_id

    @pytest.mark.asyncio
    async def test_no_deduplication(self):
        """Test that deduplication can be disabled."""
        shared_id = "shared-123"

        async def task_a(*args, **kwargs):
            return [{"id": shared_id, "source": "a"}]

        async def task_b(*args, **kwargs):
            return [{"id": shared_id, "source": "b"}]

        parallel_task = execute_parallel(
            [
                Stage(task_a),
                Stage(task_b),
            ],
            deduplicate=False,
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        # Should have 2 items (no deduplication)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test that exceptions are collected and re-raised."""

        async def task_success(*args, **kwargs):
            return [{"id": "success"}]

        async def task_failure(*args, **kwargs):
            raise ValueError("Intentional failure")

        parallel_task = execute_parallel(
            [
                Stage(task_success),
                Stage(task_failure),
            ]
        )

        with pytest.raises(ValueError, match="Intentional failure"):
            await parallel_task.run(None)  # data parameter required by parallel_run

    @pytest.mark.asyncio
    async def test_all_tasks_fail(self):
        """Test behavior when all tasks fail."""

        async def task_failure_1(*args, **kwargs):
            raise ValueError("Failure 1")

        async def task_failure_2(*args, **kwargs):
            raise RuntimeError("Failure 2")

        parallel_task = execute_parallel(
            [
                Stage(task_failure_1),
                Stage(task_failure_2),
            ]
        )

        # Should raise the first exception
        with pytest.raises(ValueError, match="Failure 1"):
            await parallel_task.run(None)  # data parameter required by parallel_run

    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Test handling of empty results."""

        async def task_empty(*args, **kwargs):
            return []

        parallel_task = execute_parallel(
            [
                Stage(task_empty),
                Stage(task_empty),
            ]
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        assert result == []

    @pytest.mark.asyncio
    async def test_single_task(self):
        """Test with a single task."""

        async def single_task(*args, **kwargs):
            return [{"id": "single", "value": 42}]

        parallel_task = execute_parallel([Stage(single_task)])

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        assert len(result) == 1
        assert result[0]["id"] == "single"

    @pytest.mark.asyncio
    async def test_no_merge(self):
        """Test merge_results=False returns last result."""

        async def task_a(*args, **kwargs):
            return [{"id": "a"}]

        async def task_b(*args, **kwargs):
            return [{"id": "b"}]

        parallel_task = execute_parallel(
            [
                Stage(task_a),
                Stage(task_b),
            ],
            merge_results=False,
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        # Should return the last valid result
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_mixed_results(self):
        """Test handling of mixed result types (list and non-list)."""

        async def task_list(*args, **kwargs):
            return [{"id": "list_item"}]

        async def task_non_list(*args, **kwargs):
            return "non_list_result"

        parallel_task = execute_parallel(
            [
                Stage(task_list),
                Stage(task_non_list),
            ]
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        # Should contain both the list item and the non-list result
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_arguments_passed_through(self):
        """Test that arguments are passed to all tasks."""
        received_args = []

        async def task_with_args(*args, **kwargs):
            received_args.append((args, kwargs))
            return [{"id": "test"}]

        parallel_task = execute_parallel(
            [
                Stage(task_with_args),
                Stage(task_with_args),
            ]
        )

        # The first positional arg is 'data', additional args go through context
        await parallel_task.run("test_data", context={"key": "value"})

        # Both tasks should receive the same data and context
        assert len(received_args) == 2
        for args, kwargs in received_args:
            assert args == ("test_data",)
            assert kwargs == {"context": {"key": "value"}}


class TestRunTasksParallelIntegration:
    """Integration-style tests for execute_parallel."""

    @pytest.mark.asyncio
    async def test_realistic_datapoint_dedup(self):
        """Test with realistic MemoryNode-like objects."""
        from uuid import uuid4

        class FakeMemoryNode:
            def __init__(self, id, name):
                self.id = id
                self.name = name

        shared_id = uuid4()
        unique_id = uuid4()

        async def episodic_task(*args, **kwargs):
            return [
                FakeMemoryNode(shared_id, "Episode from episodic"),
                FakeMemoryNode(uuid4(), "Unique from episodic"),
            ]

        async def procedural_task(*args, **kwargs):
            return [
                FakeMemoryNode(shared_id, "Same ID from procedural"),  # Duplicate
                FakeMemoryNode(unique_id, "Unique from procedural"),
            ]

        parallel_task = execute_parallel(
            [
                Stage(episodic_task),
                Stage(procedural_task),
            ],
            deduplicate=True,
        )

        result = await parallel_task.run(None)  # data parameter required by parallel_run

        # Should have 3 unique items (one duplicate removed)
        assert len(result) == 3

        # Verify deduplication happened
        ids = [str(item.id) for item in result]
        assert len(set(ids)) == 3  # All IDs should be unique
