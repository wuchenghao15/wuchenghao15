"""
Episode Quality Statistics.

Provides functions to analyze Episode quality and detect issues.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, List, Optional

from m_flow.memory.episodic.episode_size_check import (
    EpisodeStats,
    _get_all_episodes_with_facet_count,
    _get_episode_facets_ordered,
    adapt_threshold,
    audit_episode,
    execute_split,
    get_size_check_config,
)
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    pass

_logger = get_logger(__name__)


@dataclass
class EpisodeQualityItem:
    """Episode quality information."""

    id: str
    name: str
    facet_count: int
    issue_type: Optional[str]  # "empty" | "oversized" | None
    severity: Optional[str]  # "high" | "medium" | "low" | None
    can_size_check: bool  # False for empty episodes


async def get_episode_quality_stats(dataset_id: Optional[str] = None) -> dict:
    """
    Get Episode quality statistics.

    Args:
        dataset_id: Optional dataset ID to filter by

    Returns:
        Dictionary containing stats, problematic_episodes, and all_episodes
    """
    # 1. Get all Episodes with facet counts
    all_episodes: List[EpisodeStats] = await _get_all_episodes_with_facet_count()

    if not all_episodes:
        return {
            "stats": {
                "total_episodes": 0,
                "empty_count": 0,
                "oversized_count": 0,
                "threshold": 0,
                "threshold_mode": "fixed",
                "q1": 0,
                "q3": 0,
                "max_facet_count": 0,
            },
            "problematic_episodes": [],
            "all_episodes": [],
        }

    # 2. Get configuration (reuse existing config for consistency)
    config = get_size_check_config()

    # 3. Calculate threshold (align with existing implementation)
    facet_counts = [ep.facet_count for ep in all_episodes if ep.facet_count > 0]

    if config.detection_mode == "fixed":
        threshold = config.fixed_threshold
        q1, q3 = 0.0, 0.0
        if len(facet_counts) >= 4:
            import numpy as np

            q1, q3 = np.percentile(facet_counts, [25, 75])
    else:
        # IQR mode
        import numpy as np

        if len(facet_counts) >= config.min_episodes_for_distribution:
            q1, q3 = np.percentile(facet_counts, [25, 75])
            iqr = q3 - q1
            threshold = max(config.base_threshold, q3 + config.iqr_multiplier * iqr)
        else:
            q1, q3 = 0.0, 0.0
            threshold = config.base_threshold

    # 4. Classify problematic Episodes
    problematic: List[EpisodeQualityItem] = []
    all_items: List[EpisodeQualityItem] = []

    for ep in all_episodes:
        issue_type: Optional[str] = None
        severity: Optional[str] = None
        can_size_check = ep.facet_count > 0  # Empty Episodes cannot run Size Check

        if ep.facet_count == 0:
            issue_type = "empty"
            severity = "high"
        elif ep.facet_count > threshold:
            issue_type = "oversized"
            excess = ep.facet_count / threshold if threshold > 0 else 1
            severity = "high" if excess > 2 else "medium" if excess > 1.5 else "low"

        item = EpisodeQualityItem(
            id=ep.episode_id,
            name=ep.episode_name,
            facet_count=ep.facet_count,
            issue_type=issue_type,
            severity=severity,
            can_size_check=can_size_check,
        )

        all_items.append(item)
        if issue_type:
            problematic.append(item)

    # 5. Sort: problematic Episodes by facet_count descending
    problematic.sort(key=lambda x: (-x.facet_count, x.name))

    return {
        "stats": {
            "total_episodes": len(all_episodes),
            "empty_count": sum(1 for p in problematic if p.issue_type == "empty"),
            "oversized_count": sum(1 for p in problematic if p.issue_type == "oversized"),
            "threshold": round(threshold, 1),
            "threshold_mode": config.detection_mode,
            "q1": round(q1, 1),
            "q3": round(q3, 1),
            "max_facet_count": max(facet_counts) if facet_counts else 0,
        },
        "problematic_episodes": [asdict(p) for p in problematic],
        "all_episodes": [asdict(a) for a in sorted(all_items, key=lambda x: (-x.facet_count, x.name))],
    }


async def run_size_check_for_episodes(episode_ids: List[str]) -> dict:
    """
    Run Size Check on specified Episodes.

    Args:
        episode_ids: List of Episode IDs to check

    Returns:
        Dictionary containing results and summary
    """
    config = get_size_check_config()
    results: List[dict[str, Any]] = []

    # Batch fetch all Episode info (avoid repeated queries)
    all_episodes = await _get_all_episodes_with_facet_count()
    episode_map = {ep.episode_id: ep for ep in all_episodes}

    for ep_id in episode_ids:
        ep = episode_map.get(ep_id)

        if not ep:
            results.append(
                {
                    "episode_id": ep_id,
                    "decision": "ERROR",
                    "reasoning": "Episode not found",
                }
            )
            continue

        # Skip empty Episodes
        if ep.facet_count == 0:
            results.append(
                {
                    "episode_id": ep_id,
                    "episode_name": ep.episode_name,
                    "decision": "SKIPPED",
                    "reasoning": "Episode has no facets (cannot run Size Check)",
                }
            )
            continue

        # Get facets
        facets = await _get_episode_facets_ordered(ep_id)

        if not facets:
            results.append(
                {
                    "episode_id": ep_id,
                    "episode_name": ep.episode_name,
                    "decision": "SKIPPED",
                    "reasoning": "No facets found",
                }
            )
            continue

        try:
            # LLM audit
            audit_result = await audit_episode(ep, facets, config)

            if audit_result.decision == "SPLIT" and audit_result.splits:
                # Execute split
                new_ep_ids = await execute_split(ep_id, audit_result.splits, audit_result.reasoning)

                results.append(
                    {
                        "episode_id": ep_id,
                        "episode_name": ep.episode_name,
                        "decision": "SPLIT",
                        "reasoning": audit_result.reasoning,
                        "new_episodes": [
                            {
                                "id": nid,
                                "name": s.new_episode_name,
                                "facet_count": len(s.facet_indices),
                            }
                            for nid, s in zip(new_ep_ids, audit_result.splits)
                        ],
                    }
                )
            else:
                # KEEP - adapt threshold
                new_threshold = await adapt_threshold(ep_id, ep.facet_count, config)

                results.append(
                    {
                        "episode_id": ep_id,
                        "episode_name": ep.episode_name,
                        "decision": "KEEP",
                        "reasoning": audit_result.reasoning,
                        "adapted_threshold": new_threshold,
                    }
                )
        except Exception as e:
            _logger.error(f"[maintenance] Size Check failed for {ep_id}: {e}")
            results.append(
                {
                    "episode_id": ep_id,
                    "episode_name": ep.episode_name,
                    "decision": "ERROR",
                    "reasoning": str(e),
                }
            )

    return {
        "results": results,
        "summary": {
            "checked": len([r for r in results if r["decision"] in ("SPLIT", "KEEP")]),
            "split": sum(1 for r in results if r["decision"] == "SPLIT"),
            "kept": sum(1 for r in results if r["decision"] == "KEEP"),
            "skipped": sum(1 for r in results if r["decision"] == "SKIPPED"),
            "errors": sum(1 for r in results if r["decision"] == "ERROR"),
        },
    }
