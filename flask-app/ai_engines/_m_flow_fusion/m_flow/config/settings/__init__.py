# ---------------------------------------------------------------------------
# m_flow.config.settings — public surface for runtime configuration queries
# ---------------------------------------------------------------------------
"""
Fetch or persist adapter-level settings (LLM, vector, graph, relational).

Re-exported names
-----------------
* :func:`get_current_settings`  — snapshot of active config across all adapters
* :func:`get_settings`          — full settings including UI-facing option lists
* :class:`SettingsDict`         — typed dict describing the settings payload
* :func:`save_llm_config`       — persist an LLM configuration change
* :func:`save_vector_db_config` — persist a vector-DB configuration change
"""

from __future__ import annotations

from .get_current_settings import get_current_settings
from .get_settings import SettingsDict, get_settings
from .save_llm_config import save_llm_config
from .save_vector_db_config import save_vector_db_config

__all__ = [
    "get_current_settings",
    "get_settings",
    "save_llm_config",
    "save_vector_db_config",
    "SettingsDict",
]
