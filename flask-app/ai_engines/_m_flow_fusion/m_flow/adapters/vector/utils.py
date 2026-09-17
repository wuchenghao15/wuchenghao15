"""
Vector database utility functions.

Provides helper functions for working with vector search results,
including distance normalization for consistent scoring.
"""

from __future__ import annotations

from typing import Sequence


def normalize_distances(results: Sequence[dict]) -> list[float]:
    """
    Scale distance values to the [0, 1] range.

    Performs min-max normalization on distance values from vector
    search results. When all distances are identical, returns zeros
    to avoid division by zero.

    Args:
        results: Search results with '_distance' keys.

    Returns:
        Normalized distance values in [0, 1] range.

    Example:
        >>> results = [{"_distance": 0.2}, {"_distance": 0.8}]
        >>> normalize_distances(results)
        [0.0, 1.0]
    """
    if not results:
        return []

    distances = [r["_distance"] for r in results]
    min_dist = min(distances)
    max_dist = max(distances)

    # Handle identical distances
    if max_dist == min_dist:
        return [0.0] * len(results)

    # Apply min-max normalization
    range_dist = max_dist - min_dist
    return [(d - min_dist) / range_dist for d in distances]
