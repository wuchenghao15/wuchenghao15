"""
Configuration Management API

Provides a unified interface for runtime configuration of M-flow subsystems
including LLM, vector database, graph database, chunking, and storage settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Union

from m_flow.api.v1.exceptions.exceptions import InvalidConfigAttributeError

# Type alias for configuration objects
ConfigT = TypeVar("ConfigT")

# ---------------------------------------------------------------------------
# Configuration Accessors (lazy imports to avoid circular dependencies)
# ---------------------------------------------------------------------------


def _fetch_base_cfg():
    from m_flow.base_config import get_base_config

    return get_base_config()


def _fetch_memorize_cfg():
    from m_flow.config.config import get_memorize_config

    return get_memorize_config()


def _fetch_chunk_cfg():
    from m_flow.shared.infra_data.chunking.config import get_chunk_config

    return get_chunk_config()


def _fetch_vector_cfg():
    from m_flow.adapters.vector import get_vectordb_config

    return get_vectordb_config()


def _fetch_graph_cfg():
    from m_flow.adapters.graph.config import get_graph_config

    return get_graph_config()


def _fetch_llm_cfg():
    from m_flow.llm.config import get_llm_config

    return get_llm_config()


def _fetch_relational_cfg():
    from m_flow.adapters.relational import get_relational_config

    return get_relational_config()


def _fetch_migration_cfg():
    from m_flow.adapters.relational import get_migration_config

    return get_migration_config()


# ---------------------------------------------------------------------------
# Generic Configuration Update Utility
# ---------------------------------------------------------------------------


def _apply_config_updates(
    cfg_obj: ConfigT,
    updates: dict[str, Any],
    *,
    raise_on_invalid: bool = True,
) -> None:
    """
    Apply key-value pairs to a configuration object.

    Args:
        cfg_obj: Target configuration instance
        updates: Dictionary of attribute names to new values
        raise_on_invalid: If True, raise on unknown attributes

    Raises:
        InvalidConfigAttributeError: When an unknown attribute is encountered
    """
    for attr_name, attr_value in updates.items():
        if not hasattr(cfg_obj, attr_name):
            if raise_on_invalid:
                raise InvalidConfigAttributeError(attribute=attr_name)
            continue
        object.__setattr__(cfg_obj, attr_name, attr_value)


# ---------------------------------------------------------------------------
# Configuration Facade Class
# ---------------------------------------------------------------------------


class config:
    """
    Centralized configuration facade for M-flow runtime settings.

    All methods are static and modify singleton configuration instances.
    Changes take effect immediately for subsequent operations.
    """

    # -----------------------------------------------------------------------
    # Directory Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def system_root_directory(root_path: str) -> None:
        """
        Configure the system root directory and update dependent paths.

        This updates paths for relational DB, graph DB, and vector DB storage.
        """
        base = _fetch_base_cfg()
        base.system_root_directory = root_path

        db_dir = Path(root_path) / "databases"
        db_dir_str = str(db_dir)

        # Update relational storage path
        rel_cfg = _fetch_relational_cfg()
        rel_cfg.db_path = db_dir_str

        # Update graph storage path
        graph_cfg = _fetch_graph_cfg()
        graph_fname = graph_cfg.graph_filename
        graph_cfg.graph_file_path = str(db_dir / graph_fname)

        # Update LanceDB path if applicable
        vec_cfg = _fetch_vector_cfg()
        if vec_cfg.vector_db_provider == "lancedb":
            vec_cfg.vector_db_url = str(db_dir / "m_flow.lancedb")

    @staticmethod
    def data_root_directory(data_path: str) -> None:
        """Set the root directory for user data storage."""
        _fetch_base_cfg().data_root_directory = data_path

    # -----------------------------------------------------------------------
    # Monitoring Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def monitoring_tool(tool: object) -> None:
        """Assign a monitoring/telemetry tool instance."""
        _fetch_base_cfg().monitoring_tool = tool

    # -----------------------------------------------------------------------
    # Memorization Model Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def set_classification_model(model: object) -> None:
        """Configure the document classification model."""
        _fetch_memorize_cfg().classification_model = model

    @staticmethod
    def set_summarization_model(model: object) -> None:
        """Configure the text summarization model."""
        _fetch_memorize_cfg().summarization_model = model

    # -----------------------------------------------------------------------
    # Graph Database Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def set_graph_model(model: object) -> None:
        """Set the graph extraction model."""
        _fetch_graph_cfg().graph_model = model

    @staticmethod
    def set_graph_database_provider(provider_name: str) -> None:
        """Select the graph database backend provider."""
        _fetch_graph_cfg().graph_database_provider = provider_name

    @staticmethod
    def set_graph_db_config(settings: dict[str, Any]) -> None:
        """
        Batch update graph database configuration.

        Raises:
            AttributeError: If any key is not a valid attribute
        """
        cfg = _fetch_graph_cfg()
        for key, val in settings.items():
            if hasattr(cfg, key):
                object.__setattr__(cfg, key, val)
            else:
                raise AttributeError(f"'{key}' is not a valid attribute of the config.")

    # -----------------------------------------------------------------------
    # LLM Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def set_llm_provider(provider_id: str) -> None:
        """Set the LLM provider (openai, anthropic, etc.)."""
        _fetch_llm_cfg().llm_provider = provider_id

    @staticmethod
    def set_llm_endpoint(endpoint_url: str) -> None:
        """Set custom LLM API endpoint URL."""
        _fetch_llm_cfg().llm_endpoint = endpoint_url

    @staticmethod
    def set_llm_model(model_name: str) -> None:
        """Set the LLM model identifier."""
        _fetch_llm_cfg().llm_model = model_name

    @staticmethod
    def set_llm_api_key(api_key: str) -> None:
        """Set the LLM provider API key."""
        _fetch_llm_cfg().llm_api_key = api_key

    @staticmethod
    def set_llm_config(settings: dict[str, Any]) -> None:
        """
        Batch update LLM configuration attributes.

        Raises:
            InvalidConfigAttributeError: If any key is invalid
        """
        _apply_config_updates(_fetch_llm_cfg(), settings)

    # -----------------------------------------------------------------------
    # Chunking Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def set_chunk_strategy(strategy: object) -> None:
        """Set the document chunking strategy."""
        _fetch_chunk_cfg().chunk_strategy = strategy

    @staticmethod
    def set_chunk_engine(engine: object) -> None:
        """Set the chunking engine implementation."""
        _fetch_chunk_cfg().chunk_engine = engine

    @staticmethod
    def set_chunk_overlap(overlap_size: int) -> None:
        """Set the overlap between adjacent chunks."""
        _fetch_chunk_cfg().chunk_overlap = overlap_size

    @staticmethod
    def set_chunk_size(size: int) -> None:
        """Set the target chunk size in tokens/characters."""
        _fetch_chunk_cfg().chunk_size = size

    # -----------------------------------------------------------------------
    # Vector Database Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def set_vector_db_provider(provider_name: str) -> None:
        """Select the vector database backend."""
        _fetch_vector_cfg().vector_db_provider = provider_name

    @staticmethod
    def set_vector_db_key(api_key: str) -> None:
        """Set the vector database API key."""
        _fetch_vector_cfg().vector_db_key = api_key

    @staticmethod
    def set_vector_db_url(connection_url: str) -> None:
        """Set the vector database connection URL."""
        _fetch_vector_cfg().vector_db_url = connection_url

    @staticmethod
    def set_vector_db_config(settings: dict[str, Any]) -> None:
        """
        Batch update vector database configuration.

        Note: Invalid attributes are silently ignored (legacy behavior).
        """
        _apply_config_updates(_fetch_vector_cfg(), settings, raise_on_invalid=False)

    # -----------------------------------------------------------------------
    # Relational Database Configuration
    # -----------------------------------------------------------------------

    @staticmethod
    def set_relational_db_config(settings: dict[str, Any]) -> None:
        """
        Batch update relational database configuration.

        Raises:
            InvalidConfigAttributeError: If any key is invalid
        """
        _apply_config_updates(_fetch_relational_cfg(), settings)

    @staticmethod
    def set_migration_db_config(settings: dict[str, Any]) -> None:
        """
        Batch update migration database configuration.

        Raises:
            InvalidConfigAttributeError: If any key is invalid
        """
        _apply_config_updates(_fetch_migration_cfg(), settings)

    # -----------------------------------------------------------------------
    # Configuration Discovery (P1: Configuration Discoverability)
    # -----------------------------------------------------------------------

    @staticmethod
    def show(
        category: Optional[str] = None,
        as_dict: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """
        Display current configuration status.

        Args:
            category: Optional filter ("llm", "vector", "graph", "chunk", "base", "relational", "memorize")
            as_dict: Return dict instead of formatted string

        Returns:
            Formatted configuration string or dict

        Example:
            >>> import m_flow
            >>> print(m_flow.config.show())
            >>> print(m_flow.config.show("llm"))
            >>> cfg = m_flow.config.show(as_dict=True)
        """
        configs = {
            "llm": _fetch_llm_cfg,
            "vector": _fetch_vector_cfg,
            "graph": _fetch_graph_cfg,
            "chunk": _fetch_chunk_cfg,
            "base": _fetch_base_cfg,
            "relational": _fetch_relational_cfg,
            "memorize": _fetch_memorize_cfg,
        }

        # Validate category parameter
        if category:
            if category not in configs:
                valid = ", ".join(configs.keys())
                raise ValueError(f"Unknown category '{category}'. Valid: {valid}")
            configs = {category: configs[category]}

        # Sensitive fields list (need masking)
        SENSITIVE_FIELDS = {"api_key", "secret", "password", "token", "credential", "key"}

        def _mask_sensitive(data: dict) -> dict:
            """Mask sensitive fields."""
            masked = {}
            for k, v in data.items():
                if any(s in k.lower() for s in SENSITIVE_FIELDS):
                    if isinstance(v, str) and len(v) > 8:
                        masked[k] = v[:4] + "***" + v[-4:]
                    elif v is not None:
                        masked[k] = "***"
                    else:
                        masked[k] = None
                elif isinstance(v, dict):
                    masked[k] = _mask_sensitive(v)
                else:
                    masked[k] = v
            return masked

        result = {}
        for name, cfg_fn in configs.items():
            try:
                cfg = cfg_fn()

                # Pydantic BaseSettings uses model_dump()
                if hasattr(cfg, "model_dump"):
                    data = cfg.model_dump(exclude_none=True)
                elif hasattr(cfg, "to_dict"):
                    data = cfg.to_dict()
                elif hasattr(cfg, "as_dict"):
                    data = cfg.as_dict()
                else:
                    # Fallback for non-Pydantic objects
                    data = {k: v for k, v in vars(cfg).items() if not k.startswith("_")}

                # Mask sensitive data
                result[name] = _mask_sensitive(data)
            except Exception as e:
                result[name] = {"_error": str(e)}

        if as_dict:
            return result

        # Format output
        lines = []
        for name, attrs in result.items():
            lines.append(f"\n[{name.upper()}]")
            if isinstance(attrs, dict):
                for k, v in attrs.items():
                    # Truncate long values
                    display_v = str(v)
                    if len(display_v) > 100:
                        display_v = display_v[:100] + "..."
                    lines.append(f"  {k}: {display_v}")
            else:
                lines.append(f"  {attrs}")
        return "\n".join(lines)

    @staticmethod
    def env_vars(category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        List all supported environment variables with their current and default values.

        Args:
            category: Optional filter ("core", "episodic", "retrieval", "database", "performance", "auth", "logging", "chunking")

        Returns:
            dict: {var_name: {"value": current_value, "default": default_value, "description": desc, ...}}

        Example:
            >>> import m_flow
            >>> vars = m_flow.config.env_vars()
            >>> for name, info in vars.items():
            ...     print(f"{name}: {info['value']} (default: {info['default']})")
            >>>
            >>> # Filter by category
            >>> episodic_vars = m_flow.config.env_vars("episodic")
        """
        from m_flow.config.env_registry import _get_env_var_registry, get_categories

        # Validate category
        if category:
            valid_categories = get_categories()
            if category not in valid_categories:
                raise ValueError(f"Unknown category '{category}'. Valid: {sorted(valid_categories)}")

        return _get_env_var_registry(category=category, mask_sensitive=True)

    @staticmethod
    def env_categories() -> list[str]:
        """
        List all environment variable categories.

        Returns:
            List of category names.

        Example:
            >>> m_flow.config.env_categories()
            ['auth', 'chunking', 'core', 'database', 'episodic', 'logging', 'performance', 'retrieval']
        """
        from m_flow.config.env_registry import get_categories

        return get_categories()

    # -----------------------------------------------------------------------
    # Configuration Presets (P3: Configuration Preset System)
    # -----------------------------------------------------------------------

    @staticmethod
    def preset(name: str) -> None:
        """
        Apply a configuration preset.

        Presets are predefined configuration combinations for common scenarios.

        Args:
            name: Preset name.

        Available presets:
            - quick_start: Quick start with minimal configuration
            - production: Production environment with full features
            - local_llm: Local LLM, no API Key required
            - enterprise_doc: Enterprise documents, optimized for large doc processing

        Warning:
            Presets only take effect in the current process. Reapply after restart.

        Example:
            >>> import m_flow
            >>> m_flow.config.preset("quick_start")
            >>> m_flow.config.preset("production")

        Raises:
            ValueError: Unknown preset name.
        """
        from m_flow.config.presets import get_preset, list_presets

        preset_obj = get_preset(name)
        if preset_obj is None:
            available = ", ".join(list_presets().keys())
            raise ValueError(f"Unknown preset '{name}'. Available: {available}")

        preset_obj.apply()

    @staticmethod
    def list_presets() -> Dict[str, str]:
        """
        List all available presets.

        Returns:
            Dict of {preset_name: description}.

        Example:
            >>> import m_flow
            >>> presets = m_flow.config.list_presets()
            >>> for name, desc in presets.items():
            ...     print(f"{name}: {desc}")
        """
        from m_flow.config.presets import list_presets

        return list_presets()

    @staticmethod
    def register_preset(
        name: str,
        description: str,
        env_vars: Optional[Dict[str, str]] = None,
        config_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """
        Register a custom preset.

        Args:
            name: Preset name.
            description: Description.
            env_vars: Environment variable settings.
            config_overrides: Configuration overrides {category: {field: value}}.

        Note:
            Presets with the same name will be overwritten.

        Example:
            >>> import m_flow
            >>> m_flow.config.register_preset(
            ...     name="my_preset",
            ...     description="My custom configuration",
            ...     env_vars={"MFLOW_CONTENT_ROUTING": "true"},
            ...     config_overrides={"llm": {"llm_model": "gpt-4o"}}
            ... )
            >>> m_flow.config.preset("my_preset")
        """
        from m_flow.config.presets import register_preset, ConfigPreset

        preset = ConfigPreset(
            name=name,
            description=description,
            env_vars=env_vars or {},
            config_overrides=config_overrides or {},
        )
        register_preset(preset)

    @staticmethod
    def clear_caches() -> int:
        """
        Clear all configuration caches.

        Configuration functions use @lru_cache decorator, caching results after first call.
        Clear caches after changing environment variables to make new values take effect.

        Returns:
            Number of caches cleared.

        Example:
            >>> import os
            >>> os.environ["LLM_MODEL"] = "gpt-4o"
            >>> m_flow.config.clear_caches()  # Make new environment variable take effect
        """
        from m_flow.config.presets import clear_config_caches

        return clear_config_caches()
