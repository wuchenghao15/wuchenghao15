"""
Foundation configuration for M-Flow runtime.

Defines the directory layout (data, system, cache, logs) and optional
integrations (Langfuse observability).  All paths are normalized to
absolute form on load.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import pydantic
from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.root_dir import ensure_absolute_path, get_absolute_path
from m_flow.shared.observability.observers import Observer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_logs_dir() -> str:
    env = os.getenv("MFLOW_LOGS_DIR")
    if env:
        return env
    return str(Path(__file__).resolve().parent.parent / "logs")


def _infer_s3_cache(bucket: Optional[str]) -> Optional[str]:
    """Construct S3 cache path when running against remote storage."""
    if bucket:
        return f"s3://{bucket}/m_flow/cache"
    return None


# ---------------------------------------------------------------------------
# Settings model
# ---------------------------------------------------------------------------


class BaseConfig(MflowSettings):
    """
    Root-level environment configuration.

    Attributes
    ----------
    data_root_directory
        Primary storage for user data artifacts.
    system_root_directory
        Internal system state (e.g., lock files).
    cache_root_directory
        Transient cache objects.
    logs_root_directory
        Log file destination.
    monitoring_tool
        Observability backend (auto-detected from env vars).
    """

    data_root_directory: str = get_absolute_path(".data_storage")
    system_root_directory: str = get_absolute_path(".mflow/system")
    cache_root_directory: str = get_absolute_path(".mflow/cache")
    logs_root_directory: str = pydantic.Field(default_factory=_default_logs_dir)

    monitoring_tool: object = Observer.NONE

    # Optional Langfuse integration
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: Optional[str] = None

    # Bootstrap user (primarily for dev/test)
    default_user_email: Optional[str] = None
    default_user_password: Optional[str] = None
    auto_create_default_user: bool = True  # Auto-recover default user on login

    model_config = SettingsConfigDict(env_prefix="MFLOW_", env_file=".env", extra="allow")

    # ------------------------------------------------------------------
    @pydantic.model_validator(mode="after")
    def _finalize(self) -> "BaseConfig":
        # S3 auto-config for cache when storage is remote
        backend = os.getenv("STORAGE_BACKEND", "").lower()
        cache_explicit = os.getenv("CACHE_ROOT_DIRECTORY")
        if backend == "s3" and not cache_explicit:
            inferred = _infer_s3_cache(os.getenv("STORAGE_BUCKET_NAME"))
            if inferred:
                object.__setattr__(self, "cache_root_directory", inferred)

        # Normalize all paths to absolute
        for attr in ("data_root_directory", "system_root_directory", "logs_root_directory"):
            object.__setattr__(self, attr, ensure_absolute_path(getattr(self, attr)))

        # Auto-enable Langfuse when credentials present
        if self.langfuse_public_key and self.langfuse_secret_key:
            object.__setattr__(self, "monitoring_tool", Observer.LANGFUSE)

        return self

    # ------------------------------------------------------------------
    def as_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a plain dictionary."""
        return {
            "data_root": self.data_root_directory,
            "system_root": self.system_root_directory,
            "cache_root": self.cache_root_directory,
            "logs_root": self.logs_root_directory,
            "monitoring": str(self.monitoring_tool),
        }


@lru_cache(maxsize=1)
def get_base_config() -> BaseConfig:
    """Singleton accessor for the runtime configuration."""
    return BaseConfig()
