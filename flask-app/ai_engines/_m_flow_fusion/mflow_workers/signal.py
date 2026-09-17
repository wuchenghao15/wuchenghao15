"""
Sentinel tokens for multiprocess / async queue fan-out.

These values are not graph payloads; workers compare against them to cascade
shutdown without scattering bare string literals across worker code.
"""

from __future__ import annotations

from enum import Enum


class WorkerQueueSentinel(str, Enum):
    """
    Control token carried on the same queues as normal work items.

    The payload remains the literal ``"STOP"`` for compatibility with any
    code paths that still compare against that string value.
    """

    STOP = "STOP"


# Historical import path; prefer ``WorkerQueueSentinel`` in new code.
QueueSignal = WorkerQueueSentinel
