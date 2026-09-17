"""
Temporal event model for knowledge graph construction.

Captures occurrences that happen at a specific point in time or span
an interval, optionally anchored to a geographic location.  Events are
indexed by ``name`` for efficient retrieval during graph queries.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field, SkipValidation

from m_flow.core import MemoryNode
from m_flow.core.domain.models.Interval import Interval
from m_flow.core.domain.models.Timestamp import Timestamp

# Configuration for downstream vector / search indexing pipelines
_EVENT_INDEX_CONFIG: Dict[str, Any] = {"index_fields": ["name"]}


class Event(MemoryNode):
    """
    Represents a discrete occurrence with optional temporal and spatial context.

    An event may be pinpointed to a single moment via ``at`` (a :class:`Timestamp`),
    or stretched across a duration via ``during`` (an :class:`Interval`).
    Arbitrary extra data can be attached through the ``attributes`` mapping,
    which deliberately skips Pydantic validation to accept heterogeneous payloads.

    Example::

        evt = Event(
            name="product_launch",
            description="Global launch of version 3.0",
            location="San Francisco, CA",
        )
    """

    name: str = Field(
        ...,
        description="Short identifier or title for the event",
    )
    description: Optional[str] = Field(
        default=None,
        description="Longer human-readable narrative of what occurred",
    )
    at: Optional[Timestamp] = Field(
        default=None,
        description="Exact point-in-time when the event took place",
    )
    during: Optional[Interval] = Field(
        default=None,
        description="Time span over which the event occurred",
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic or logical location associated with the event",
    )
    attributes: SkipValidation[Any] = Field(
        default=None,
        description="Opaque bag of extra attributes (validation skipped)",
    )

    # Determines which fields are sent to the indexing pipeline
    metadata: dict = Field(default_factory=lambda: dict(_EVENT_INDEX_CONFIG))
