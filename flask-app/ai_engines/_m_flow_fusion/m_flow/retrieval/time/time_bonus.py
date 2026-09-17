"""
Time bonus calculation module.

Features:
- Calculate match degree between candidate and query time range
- Convert match degree to bonus value (used to reduce score, since lower score is better)
- Support mismatch penalty (time mismatch penalty, disabled by default)

Design principles:
- Only positive bonuses, no negative penalties (stability)
- Upper bound protection (avoid excessive bonuses disrupting original ranking)
- Prioritize mentioned_time, then created_at
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .query_time_parser import QueryTimeInfo


@dataclass
class TimeBonus:
    """Time bonus result."""

    bonus: float  # Actual bonus value (used to reduce score, positive = favorable)
    match_score: float  # Match degree [0, 1]
    match_type: str  # "mentioned_time" | "created_at" | "none"
    candidate_start_ms: Optional[int] = None
    candidate_end_ms: Optional[int] = None
    # Mismatch penalty
    penalty: float = 0.0  # Penalty value (used to increase score, positive = unfavorable)
    penalty_reason: str = "none"  # "mismatch" | "missing" | "none"


@dataclass
class TimeBonusConfig:
    """Time bonus configuration."""

    # Master switch
    enabled: bool = True

    # Bonus strength
    bonus_max: float = 0.06  # Maximum bonus
    score_floor: float = 0.08  # Score floor (avoid excessive suppression)

    # Confidence threshold
    query_conf_min: float = 0.4  # No bonus if query time confidence below this value

    # Match weights
    mentioned_time_weight: float = 1.0  # Weight for mentioned_time
    created_at_weight: float = 0.5  # Weight for created_at (typically lower)

    # Wide time range decay
    wide_range_penalty_days: float = 365.0  # Start decay after this many days
    wide_range_min_weight: float = 0.3  # Minimum weight for wide range

    # Recall expansion
    wide_search_multiplier: float = 2.0  # Multiplier to expand candidate pool when time is present
    wide_search_cap: int = 300  # Candidate pool cap

    # ====== Mismatch Penalty ======
    # When query explicitly contains time but candidate time doesn't match, apply penalty
    enable_mismatch_penalty: bool = False  # Whether to enable mismatch penalty
    mismatch_penalty_max: float = 0.03  # Maximum penalty value (added to score)
    mismatch_conf_threshold: float = 0.7  # Only penalize if query time confidence above this value
    mismatch_require_candidate_time: bool = True  # Whether to require candidate to have time for penalty
    # If mismatch_require_candidate_time=True, only penalize when candidate has time but doesn't match
    # If mismatch_require_candidate_time=False, candidates without time fields will also be penalized


def compute_time_match(
    candidate: Dict[str, Any],
    query_time: QueryTimeInfo,
    config: Optional[TimeBonusConfig] = None,
) -> TimeBonus:
    """
    Calculate match degree between a single candidate and query time.

    Args:
        candidate: Candidate object, needs to contain payload or direct time fields
        query_time: Query time parsing result
        config: Configuration object

    Returns:
        TimeBonus: Bonus result
    """
    if config is None:
        config = TimeBonusConfig()

    # Check if enabled
    if not config.enabled:
        return TimeBonus(bonus=0.0, match_score=0.0, match_type="none")

    # Check if query has valid time
    if not query_time.has_time or query_time.confidence < config.query_conf_min:
        return TimeBonus(bonus=0.0, match_score=0.0, match_type="none")

    q_start = query_time.start_ms
    q_end = query_time.end_ms

    # Get candidate time fields (supports multiple data structures)
    payload = candidate.get("payload", candidate) if isinstance(candidate, dict) else {}
    if hasattr(candidate, "payload") and candidate.payload is not None:
        payload = candidate.payload

    # Ensure payload is a dict type
    if not isinstance(payload, dict):
        payload = {}

    # Try to get mentioned_time
    mentioned_start = payload.get("mentioned_time_start_ms")
    mentioned_end = payload.get("mentioned_time_end_ms")
    mentioned_conf = payload.get("mentioned_time_confidence", 0.7)

    # Try to get created_at
    created_at = payload.get("created_at")

    match_score = 0.0
    match_type = "none"
    cand_start = None
    cand_end = None

    # Prioritize mentioned_time
    if mentioned_start is not None and mentioned_end is not None:
        match_score = (
            _compute_overlap_score(mentioned_start, mentioned_end, q_start, q_end)
            * mentioned_conf
            * config.mentioned_time_weight
        )
        if match_score > 0:
            match_type = "mentioned_time"
            cand_start = mentioned_start
            cand_end = mentioned_end

    # If mentioned_time didn't match, try created_at
    if match_score == 0 and created_at is not None:
        # created_at is a single point, check if it's within query range
        if q_start <= created_at <= q_end:
            match_score = 1.0 * config.created_at_weight
            match_type = "created_at"
            cand_start = created_at
            cand_end = created_at

    # Calculate actual bonus
    bonus = 0.0
    if match_score > 0:
        # Apply wide range decay
        query_days = query_time.duration_days
        if query_days > config.wide_range_penalty_days:
            range_factor = max(config.wide_range_min_weight, config.wide_range_penalty_days / query_days)
            match_score *= range_factor

        # Multiply by query time confidence
        match_score *= query_time.confidence

        # Convert to bonus
        bonus = min(config.bonus_max, match_score * config.bonus_max)

    # Calculate mismatch penalty
    penalty = 0.0
    penalty_reason = "none"

    if config.enable_mismatch_penalty and bonus == 0:
        # Only consider penalty when there's no match (bonus=0)
        # and query time confidence is high enough
        if query_time.confidence >= config.mismatch_conf_threshold:
            has_candidate_time = (mentioned_start is not None and mentioned_end is not None) or created_at is not None

            if has_candidate_time:
                # Candidate has time but doesn't match -> mismatch penalty
                penalty = config.mismatch_penalty_max * query_time.confidence
                penalty_reason = "mismatch"
            elif not config.mismatch_require_candidate_time:
                # Candidate has no time -> missing penalty (if config allows)
                penalty = config.mismatch_penalty_max * query_time.confidence * 0.5
                penalty_reason = "missing"

    return TimeBonus(
        bonus=bonus,
        match_score=match_score,
        match_type=match_type,
        candidate_start_ms=cand_start,
        candidate_end_ms=cand_end,
        penalty=penalty,
        penalty_reason=penalty_reason,
    )


def _compute_overlap_score(
    cand_start: int,
    cand_end: int,
    query_start: int,
    query_end: int,
) -> float:
    """
    Calculate overlap degree between two time ranges.

    Returns [0, 1]:
    - 0: No overlap
    - 1: Complete overlap (containment also counts as 1)
    """
    # Calculate overlap interval
    overlap_start = max(cand_start, query_start)
    overlap_end = min(cand_end, query_end)

    if overlap_start >= overlap_end:
        return 0.0

    overlap = overlap_end - overlap_start

    # Use shorter interval as denominator (containment also counts as full score)
    cand_dur = max(1, cand_end - cand_start)
    query_dur = max(1, query_end - query_start)
    min_dur = min(cand_dur, query_dur)

    return min(1.0, overlap / min_dur)


def apply_time_bonus_to_results(
    results: List[Any],
    query_time: QueryTimeInfo,
    config: Optional[TimeBonusConfig] = None,
) -> Dict[str, Any]:
    """
    Batch apply time bonus to search results.

    Directly modifies the score attribute of each object in results.

    Args:
        results: List of VectorSearchHit
        query_time: Query time parsing result
        config: Configuration object

    Returns:
        dict: Statistics
    """
    if config is None:
        config = TimeBonusConfig()

    stats = {
        "total": len(results),
        "time_matched": 0,
        "mentioned_time_matched": 0,
        "created_at_matched": 0,
        "avg_bonus": 0.0,
        "max_bonus": 0.0,
        # Penalty statistics
        "time_penalized": 0,
        "mismatch_penalized": 0,
        "missing_penalized": 0,
        "avg_penalty": 0.0,
        "max_penalty": 0.0,
    }

    if not config.enabled or not query_time.has_time:
        return stats

    total_bonus = 0.0
    total_penalty = 0.0

    for r in results:
        # Calculate bonus/penalty
        time_bonus = compute_time_match(r, query_time, config)

        # Get current score
        current_score = getattr(r, "score", None)
        if current_score is None:
            continue

        new_score = current_score

        # Apply bonus (reduce score, since lower score is better)
        if time_bonus.bonus > 0:
            new_score = max(config.score_floor, new_score - time_bonus.bonus)

            # Update statistics
            stats["time_matched"] += 1
            if time_bonus.match_type == "mentioned_time":
                stats["mentioned_time_matched"] += 1
            elif time_bonus.match_type == "created_at":
                stats["created_at_matched"] += 1

            total_bonus += time_bonus.bonus
            stats["max_bonus"] = max(stats["max_bonus"], time_bonus.bonus)

        # Apply penalty (increase score)
        if time_bonus.penalty > 0:
            new_score = new_score + time_bonus.penalty  # Increase score = lower ranking

            stats["time_penalized"] += 1
            if time_bonus.penalty_reason == "mismatch":
                stats["mismatch_penalized"] += 1
            elif time_bonus.penalty_reason == "missing":
                stats["missing_penalized"] += 1

            total_penalty += time_bonus.penalty
            stats["max_penalty"] = max(stats["max_penalty"], time_bonus.penalty)

        r.score = new_score

    if stats["time_matched"] > 0:
        stats["avg_bonus"] = total_bonus / stats["time_matched"]
    if stats["time_penalized"] > 0:
        stats["avg_penalty"] = total_penalty / stats["time_penalized"]

    return stats


def compute_edge_time_bonus(
    node1_payload: Dict[str, Any],
    node2_payload: Dict[str, Any],
    query_time: QueryTimeInfo,
    config: Optional[TimeBonusConfig] = None,
) -> float:
    """
    Calculate time bonus for an edge (used for adaptive sort).

    Takes the higher match degree from the two endpoints.

    Args:
        node1_payload: Payload of node 1
        node2_payload: Payload of node 2
        query_time: Query time parsing result
        config: Configuration object

    Returns:
        float: Bonus value
    """
    if config is None:
        config = TimeBonusConfig()

    bonus1 = compute_time_match({"payload": node1_payload}, query_time, config)
    bonus2 = compute_time_match({"payload": node2_payload}, query_time, config)

    # Take the higher bonus
    return max(bonus1.bonus, bonus2.bonus)
