"""Resolve the effective storage configuration for the current context.

Priority order:
1. A context-variable override set via :data:`file_storage_config`
   (useful when different async tasks target different roots).
2. The application-wide base configuration from ``m_flow.base_config``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from m_flow.base_config import get_base_config as _base_cfg
from .config import file_storage_config as _ctx_var


def _defaults_from_base() -> Dict[str, Any]:
    """Derive storage settings from the global base configuration."""
    cfg = _base_cfg()
    return {"data_root_directory": cfg.data_root_directory}


def get_storage_config() -> Optional[Any]:
    """Return context-local config when set, otherwise global defaults."""
    override = _ctx_var.get()
    return override if override is not None else _defaults_from_base()
