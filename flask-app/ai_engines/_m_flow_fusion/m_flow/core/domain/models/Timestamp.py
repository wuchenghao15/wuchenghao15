"""
Temporal representation for memory nodes.

This module provides the Timestamp model for capturing and decomposing
temporal information associated with memory nodes in the knowledge graph.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import Field

from m_flow.core import MemoryNode


# Bounds for validation
_YEAR_MIN = 1970
_YEAR_MAX = 2100
_MONTH_RANGE = (1, 12)
_DAY_RANGE = (1, 31)
_HOUR_RANGE = (0, 23)
_MINUTE_RANGE = (0, 59)
_SECOND_RANGE = (0, 59)


class Timestamp(MemoryNode):
    """
    A temporal marker with Unix timestamp and decomposed date/time components.

    Attributes:
        time_at: Unix timestamp in seconds since epoch (UTC).
        year: Four-digit year (1970-2100).
        month: Month of year (1-12).
        day: Day of month (1-31).
        hour: Hour of day in 24h format (0-23).
        minute: Minute of hour (0-59).
        second: Second of minute (0-59).
        timestamp_str: Human-readable ISO 8601 representation.
    """

    time_at: int = Field(
        ...,
        description="Unix timestamp in seconds",
        ge=0,
    )
    year: int = Field(
        ...,
        description="Four-digit year",
        ge=_YEAR_MIN,
        le=_YEAR_MAX,
    )
    month: int = Field(
        ...,
        description="Month (1-12)",
        ge=_MONTH_RANGE[0],
        le=_MONTH_RANGE[1],
    )
    day: int = Field(
        ...,
        description="Day of month (1-31)",
        ge=_DAY_RANGE[0],
        le=_DAY_RANGE[1],
    )
    hour: int = Field(
        ...,
        description="Hour (0-23)",
        ge=_HOUR_RANGE[0],
        le=_HOUR_RANGE[1],
    )
    minute: int = Field(
        ...,
        description="Minute (0-59)",
        ge=_MINUTE_RANGE[0],
        le=_MINUTE_RANGE[1],
    )
    second: int = Field(
        ...,
        description="Second (0-59)",
        ge=_SECOND_RANGE[0],
        le=_SECOND_RANGE[1],
    )
    timestamp_str: str = Field(
        ...,
        description="ISO 8601 formatted timestamp string",
    )

    @classmethod
    def from_unix(cls, unix_ts: int, node_id: Optional[str] = None) -> "Timestamp":
        """
        Create a Timestamp from a Unix timestamp.

        Args:
            unix_ts: Seconds since Unix epoch (UTC).
            node_id: Optional identifier for the memory node.

        Returns:
            A new Timestamp instance with decomposed components.
        """
        dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        iso_str = dt.isoformat()

        kwargs = {
            "time_at": unix_ts,
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute,
            "second": dt.second,
            "timestamp_str": iso_str,
        }
        if node_id is not None:
            kwargs["id"] = node_id

        return cls(**kwargs)

    @classmethod
    def from_datetime(cls, dt: datetime, node_id: Optional[str] = None) -> "Timestamp":
        """
        Create a Timestamp from a datetime object.

        Args:
            dt: A datetime instance (assumed UTC if naive).
            node_id: Optional identifier for the memory node.

        Returns:
            A new Timestamp instance.
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        unix_ts = int(dt.timestamp())
        return cls.from_unix(unix_ts, node_id=node_id)

    def to_datetime(self) -> datetime:
        """
        Convert this Timestamp back to a datetime object (UTC).

        Returns:
            A timezone-aware datetime in UTC.
        """
        return datetime.fromtimestamp(self.time_at, tz=timezone.utc)

    def __str__(self) -> str:
        """Return the ISO 8601 string representation."""
        return self.timestamp_str

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"Timestamp({self.timestamp_str})"
