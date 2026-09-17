# m_flow/api/v1/maintenance/episode_size.py
"""
Episode Size Check API.

Provides a public API for checking and splitting oversized Episodes.
"""

from typing import Any, Dict, Optional

from m_flow.memory.episodic.episode_size_check import (
    run_episode_size_check,
    EpisodeSizeCheckConfig,
    get_size_check_config,
)


async def check_episode_sizes(
    *,
    enabled: Optional[bool] = None,
    base_threshold: Optional[int] = None,
    absolute_threshold: Optional[int] = None,
    max_threshold: Optional[int] = None,
    min_facets_to_check: Optional[int] = None,
    user_id: Optional[str] = None,
    space_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check and optionally split oversized Episodes.

    This is a maintenance operation that:
    1. Detects Episodes with abnormally high facet counts
    2. Uses LLM to audit whether they have coherent semantic focus
    3. Splits Episodes with multiple foci into separate Episodes
    4. Adapts thresholds for Episodes judged as reasonably large

    Args:
        enabled: Enable/disable the check (default: True)
        base_threshold: Default trigger threshold for IQR calculation (default: 12)
        absolute_threshold: Absolute threshold - must check if exceeded (default: 30)
        max_threshold: Threshold ceiling for adaptive adjustment (default: 50)
        min_facets_to_check: Minimum facet count to be considered for check (default: 9)
        user_id: Optional filter by user
        space_id: Optional filter by space

    Returns:
        {
            "checked": int,      # Number of Episodes checked
            "split": int,        # Number of Episodes split
            "adapted": int,      # Number of Episodes with raised thresholds
            "errors": List[str]  # Error messages
        }

    Example:
        >>> import m_flow
        >>> stats = await m_flow.maintenance.check_episode_sizes()
        >>> print(f"Split {stats['split']} Episodes")

        # With custom thresholds
        >>> stats = await m_flow.maintenance.check_episode_sizes(
        ...     absolute_threshold=25,
        ...     min_facets_to_check=10,
        ... )
    """
    # Build config with overrides
    base_config = get_size_check_config()

    config = EpisodeSizeCheckConfig(
        enabled=enabled if enabled is not None else base_config.enabled,
        base_threshold=base_threshold if base_threshold is not None else base_config.base_threshold,
        absolute_threshold=absolute_threshold if absolute_threshold is not None else base_config.absolute_threshold,
        max_threshold=max_threshold if max_threshold is not None else base_config.max_threshold,
        min_facets_to_check=min_facets_to_check if min_facets_to_check is not None else base_config.min_facets_to_check,
        min_episodes_for_distribution=base_config.min_episodes_for_distribution,
        iqr_multiplier=base_config.iqr_multiplier,
        adaptive_increment=base_config.adaptive_increment,
        prompt_file=base_config.prompt_file,
        reference_sample_count=base_config.reference_sample_count,
        history_log_path=base_config.history_log_path,
    )

    return await run_episode_size_check(config, user_id, space_id)
