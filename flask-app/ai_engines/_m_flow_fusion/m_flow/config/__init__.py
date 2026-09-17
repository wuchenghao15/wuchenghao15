"""
M-flow Configuration Package.

This package provides configuration management for the M-flow system,
including settings loading, validation, and environment configuration.

Submodules
----------

config
    Core configuration container and initialization.

settings
    Settings management and retrieval utilities.

env_registry
    Environment variable registry and discovery.

Example usage::

    from m_flow.config.config import configure_mflow
    from m_flow.config.settings import get_current_settings

    configure_mflow()
    settings = get_current_settings()

    # Configuration discovery (P1)
    import m_flow
    print(m_flow.config.show())  # Show current config
    print(m_flow.config.env_vars())  # List environment variables
"""

_LAZY_ATTRS = {
    "show",
    "env_vars",
    "env_categories",
    "preset",
    "list_presets",
    "register_preset",
    "clear_caches",
    "set_llm_config",
    "set_llm_provider",
    "set_llm_endpoint",
    "set_llm_model",
    "set_llm_api_key",
    "set_graph_db_config",
    "set_graph_database_provider",
    "set_graph_model",
    "set_vector_db_config",
    "set_vector_db_provider",
    "set_vector_db_key",
    "set_vector_db_url",
    "set_relational_db_config",
    "set_migration_db_config",
    "set_chunk_size",
    "set_chunk_overlap",
    "set_chunk_strategy",
    "set_chunk_engine",
    "set_classification_model",
    "set_summarization_model",
    "system_root_directory",
    "data_root_directory",
    "monitoring_tool",
}


def __getattr__(name: str):
    if name in _LAZY_ATTRS:
        from m_flow.api.v1.config.config import config as _config_class

        return getattr(_config_class, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_ATTRS)
