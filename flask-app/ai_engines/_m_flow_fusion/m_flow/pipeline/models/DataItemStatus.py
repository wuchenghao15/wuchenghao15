"""
Data Item Processing Status
===========================

Enumeration for tracking the lifecycle state of data items
as they progress through the processing pipeline.
"""

from __future__ import annotations

import enum


class DataItemStatus(str, enum.Enum):
    """
    Lifecycle states for data item processing.

    Used to track whether a data item has been fully processed
    through the ingestion and memorization pipeline.

    Values
    ------
    COMPLETED : str
        Data item has been fully processed.
    DATA_ITEM_PROCESSING_COMPLETED : str
        Legacy alias for COMPLETED (backwards compatibility).
    """

    COMPLETED = "DATA_ITEM_PROCESSING_COMPLETED"
    DATA_ITEM_PROCESSING_COMPLETED = "DATA_ITEM_PROCESSING_COMPLETED"


# Module-level alias
DATA_ITEM_PROCESSING_COMPLETED = DataItemStatus.COMPLETED
