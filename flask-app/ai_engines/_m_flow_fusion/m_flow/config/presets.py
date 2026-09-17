"""
M-flow configuration preset system.

Supports scenario-based configuration, allowing users to quickly switch between different configuration combinations.

Example:
    >>> import m_flow
    >>> m_flow.config.preset("quick_start")  # Apply preset
    >>> m_flow.config.list_presets()  # List all presets
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from m_flow.shared.logging_utils import get_logger

__all__ = [
    "ConfigPreset",
    "register_preset",
    "get_preset",
    "list_presets",
    "clear_config_caches",
]

logger = get_logger("presets")


# ============================================================================
# Config Cache Clearing
# ============================================================================

# All config functions using @lru_cache
_CACHED_CONFIG_FUNCTIONS: List[tuple[str, str]] = [
    ("m_flow.llm.config", "get_llm_config"),
    ("m_flow.base_config", "get_base_config"),
    ("m_flow.config.config", "get_memorize_config"),
    ("m_flow.adapters.vector.config", "get_vectordb_config"),
    ("m_flow.adapters.vector.embeddings.config", "get_embedding_config"),
    ("m_flow.adapters.graph.config", "get_graph_config"),
    ("m_flow.adapters.relational.config", "get_relational_config"),
    ("m_flow.adapters.relational.config", "get_migration_config"),
    ("m_flow.adapters.cache.config", "get_cache_config"),
    ("m_flow.shared.infra_data.chunking.config", "get_chunk_config"),
    ("m_flow.shared.files.storage.s3_config", "get_s3_config"),
    ("m_flow.preprocessing.coreference.config", "get_coref_config"),
]

# Non-lru_cache cleanup hooks (for global singletons, etc.)
_CLEANUP_HOOKS: List[tuple[str, str]] = [
    ("m_flow.preprocessing.coreference.preprocessor", "clear_session_manager"),
]


def clear_config_caches() -> int:
    """
    Clear all configuration caches.

    Config functions use @lru_cache decorator, caching results after first call.
    After changing environment variables, cache must be cleared for new values to take effect.

    Also calls cleanup hooks for non-lru_cache singletons.

    Returns:
        Number of caches cleared.

    Note:
        Uses importlib.import_module for delayed import to avoid circular imports.
    """
    cleared = 0

    # Clear lru_cache functions
    for module_path, func_name in _CACHED_CONFIG_FUNCTIONS:
        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name, None)
            if func and hasattr(func, "cache_clear"):
                func.cache_clear()
                cleared += 1
                logger.debug(f"Cleared cache: {module_path}.{func_name}")
        except (ImportError, AttributeError) as e:
            logger.debug(f"Skipping {module_path}.{func_name}: {e}")

    # Call cleanup hooks for singletons
    for module_path, func_name in _CLEANUP_HOOKS:
        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name, None)
            if func and callable(func):
                func()
                cleared += 1
                logger.debug(f"Called cleanup hook: {module_path}.{func_name}")
        except (ImportError, AttributeError) as e:
            logger.debug(f"Skipping hook {module_path}.{func_name}: {e}")

    total_items = len(_CACHED_CONFIG_FUNCTIONS) + len(_CLEANUP_HOOKS)
    logger.debug(f"Cleared {cleared}/{total_items} config caches and hooks")
    return cleared


# ============================================================================
# Config Presets
# ============================================================================


@dataclass
class ConfigPreset:
    """
    Configuration preset.

    Encapsulates a set of related environment variables and config overrides for one-click application.

    Attributes:
        name: Preset name (unique identifier).
        description: Preset description.
        env_vars: Environment variable settings {var_name: value}.
        config_overrides: Config overrides {category: {field: value}}.

    Example:
        >>> preset = ConfigPreset(
        ...     name="quick_start",
        ...     description="Quick start configuration",
        ...     env_vars={"MFLOW_CONTENT_ROUTING": "true"},
        ... )
        >>> preset.apply()
    """

    name: str
    description: str
    env_vars: Dict[str, str] = field(default_factory=dict)
    config_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def apply(self) -> None:
        """
        Apply preset.

        1. Set environment variables
        2. Clear config caches (for new env vars to take effect)
        3. Apply config overrides (optional)

        Warning:
            Preset only takes effect in current process. Must reapply after process restart.
        """
        # Step 1: Set environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value
            logger.debug(f"Set env: {key}={value}")

        # Step 2: Clear config caches (critical!)
        cleared = clear_config_caches()

        # Step 3: Apply config overrides
        for category, overrides in self.config_overrides.items():
            _apply_config_by_category(category, overrides)

        logger.info(f"Applied preset '{self.name}': {len(self.env_vars)} env vars, {cleared} caches cleared")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "env_vars": self.env_vars,
            "config_overrides": self.config_overrides,
        }


def _apply_config_by_category(category: str, overrides: Dict[str, Any]) -> None:
    """
    Apply config overrides by category.

    Args:
        category: Config category (llm, vector, graph, relational, etc.).
        overrides: Override value dictionary.
    """
    try:
        # Delayed import of config class to avoid circular imports
        from m_flow.api.v1.config.config import config

        setter_map = {
            "llm": config.set_llm_config,
            "vector": config.set_vector_db_config,
            "graph": config.set_graph_db_config,
            "relational": config.set_relational_db_config,
            "migration": config.set_migration_db_config,
        }

        setter = setter_map.get(category)
        if setter:
            setter(overrides)
            logger.debug(f"Applied config override: {category} = {overrides}")
        else:
            logger.warning(f"Unknown config category: {category}")
    except Exception as e:
        logger.warning(f"Failed to apply config override for {category}: {e}")


# ============================================================================
# Preset Registry
# ============================================================================

_PRESETS: Dict[str, ConfigPreset] = {}


def register_preset(preset: ConfigPreset) -> None:
    """
    Register preset.

    Args:
        preset: Preset object.

    Note:
        Same-named presets will be overwritten.
    """
    _PRESETS[preset.name] = preset
    logger.debug(f"Registered preset: {preset.name}")


def get_preset(name: str) -> Optional[ConfigPreset]:
    """
    Get preset.

    Args:
        name: Preset name.

    Returns:
        Preset object, or None if not found.
    """
    return _PRESETS.get(name)


def list_presets() -> Dict[str, str]:
    """
    List all presets.

    Returns:
        Dictionary {preset_name: description}.
    """
    return {name: p.description for name, p in _PRESETS.items()}


def get_all_presets() -> Dict[str, ConfigPreset]:
    """
    Get all preset objects.

    Returns:
        Dictionary {preset_name: preset_object}.
    """
    return _PRESETS.copy()


# ============================================================================
# Built-in Presets (placeholders, users define specific content later)
# ============================================================================

# Quick start preset
_QUICK_START = ConfigPreset(
    name="quick_start",
    description="Quick start, minimal configuration",
    env_vars={
        "MFLOW_CONTENT_ROUTING": "true",
        "MFLOW_EPISODE_SIZE_CHECK_AUTO": "false",
        "MFLOW_LLM_CONCURRENCY_LIMIT": "5",
    },
)

# Production preset
_PRODUCTION = ConfigPreset(
    name="production",
    description="Production environment, full features",
    env_vars={
        "MFLOW_CONTENT_ROUTING": "true",
        "MFLOW_EPISODE_SIZE_CHECK_AUTO": "true",
        "MFLOW_EPISODIC_ENABLE_FACET_POINTS": "true",
        "MFLOW_LLM_CONCURRENCY_LIMIT": "20",
    },
)

# Local LLM preset
_LOCAL_LLM = ConfigPreset(
    name="local_llm",
    description="Local LLM, no API Key required",
    env_vars={
        "LLM_BASE_URL": "http://localhost:11434/v1",
        "LLM_MODEL": "llama3",
        "LLM_API_KEY": "ollama",  # Ollama doesn't need a real key
        "MFLOW_CONTENT_ROUTING": "true",
    },
)

# Enterprise document preset
_ENTERPRISE_DOC = ConfigPreset(
    name="enterprise_doc",
    description="Enterprise documents, optimized for large document processing",
    env_vars={
        "MFLOW_CONTENT_ROUTING": "true",
        "MFLOW_EPISODE_SIZE_CHECK_AUTO": "true",
        "MFLOW_LLM_CONCURRENCY_LIMIT": "10",
        "MFLOW_EPISODIC_ENABLE_FACET_POINTS": "true",
    },
)


def _register_builtin_presets() -> None:
    """Register built-in presets."""
    for preset in [_QUICK_START, _PRODUCTION, _LOCAL_LLM, _ENTERPRISE_DOC]:
        register_preset(preset)


# Register built-in presets when module loads
_register_builtin_presets()
