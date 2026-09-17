"""
Closed time-range model for temporal annotations.

An :class:`Interval` pairs two :class:`Timestamp` values to represent a
contiguous duration.  It is typically attached to an :class:`Event` via
its ``during`` field to indicate that the event spans a period rather
than occurring at a single instant.
"""

from __future__ import annotations

from pydantic import Field

from m_flow.core import MemoryNode
from m_flow.core.domain.models.Timestamp import Timestamp


class Interval(MemoryNode):
    """
    Represents a closed time range defined by a start and end timestamp.

    Both boundaries are required; open-ended intervals are not supported.
    For point-in-time references, use a :class:`Timestamp` directly instead.

    Example::

        span = Interval(
            time_from=Timestamp(year=2025, month=1, day=1),
            time_to=Timestamp(year=2025, month=12, day=31),
        )
    """

    time_from: Timestamp = Field(
        ...,
        description="Inclusive lower bound of the interval",
    )
    time_to: Timestamp = Field(
        ...,
        description="Inclusive upper bound of the interval",
    )
