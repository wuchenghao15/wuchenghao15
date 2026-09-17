"""Exponential back-off with jitter for retry loops.

The jitter prevents the *thundering-herd* effect when many callers
retry simultaneously after a transient outage.
"""

from __future__ import annotations

import random

# ── tunables ──────────────────────────────────────────────────────

MAX_RETRIES: int = 5
INITIAL_DELAY: float = 1.0  # seconds
GROWTH_FACTOR: float = 2.0  # exponential multiplier
JITTER_FRACTION: float = 0.1  # ±10 %


def calculate_backoff(
    attempt: int,
    *,
    base_delay: float = INITIAL_DELAY,
    multiplier: float = GROWTH_FACTOR,
    jitter: float = JITTER_FRACTION,
) -> float:
    """Return the number of seconds to wait before retry *attempt*.

    >>> 0.8 < calculate_backoff(0) < 1.2
    True
    """
    raw = base_delay * (multiplier**attempt)
    delta = raw * jitter
    return raw + random.uniform(-delta, delta)
