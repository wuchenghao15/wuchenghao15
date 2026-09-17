"""
Neo4j Graph Metrics Validation
==============================
m_flow.tests.tasks.descriptive_metrics.neo4j_metrics_test

Validates descriptive graph metrics computation using Neo4j as the
graph database backend. Tests both core required metrics and
optional advanced metrics calculations.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Import metric validation utilities
from m_flow.tests.tasks.descriptive_metrics.metrics_test_utils import validate_metrics


class Neo4jMetricsValidator:
    """Encapsulates Neo4j metrics validation logic."""

    PROVIDER_NAME = "neo4j"

    async def run_core_metrics(self) -> None:
        """Validate core required graph metrics."""
        await validate_metrics(
            provider=self.PROVIDER_NAME,
            extended=False,
        )

    async def run_extended_metrics(self) -> None:
        """Validate extended metrics including optional calculations."""
        await validate_metrics(
            provider=self.PROVIDER_NAME,
            extended=True,
        )

    async def execute_all(self) -> None:
        """Run complete metrics validation suite."""
        await self.run_core_metrics()
        await self.run_extended_metrics()


async def _run_validation():
    """Execute the Neo4j metrics validation suite."""
    validator = Neo4jMetricsValidator()
    await validator.execute_all()


if __name__ == "__main__":
    asyncio.run(_run_validation())
