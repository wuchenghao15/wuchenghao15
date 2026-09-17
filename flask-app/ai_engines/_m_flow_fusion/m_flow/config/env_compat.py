"""
Environment variable compatibility layer.

Provides a mixin that enables MFLOW_-prefixed environment variables
while falling back to bare variable names for backward compatibility.

Usage:
    class MyConfig(MflowSettings):
        llm_api_key: str = ""

    # Reads MFLOW_LLM_API_KEY first, falls back to LLM_API_KEY
"""

from __future__ import annotations

import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MflowSettings(BaseSettings):
    """
    Base settings class for M-flow configuration.

    Reads environment variables with ``MFLOW_`` prefix by default,
    and falls back to bare variable names for backward compatibility
    with existing deployments.
    """

    model_config = SettingsConfigDict(
        env_prefix="MFLOW_",
        env_file=".env",
        extra="allow",
    )

    @model_validator(mode="before")
    @classmethod
    def _fallback_bare_env(cls, values):
        """For each field, if MFLOW_XXX is not set, fall back to bare XXX."""
        for field_name in cls.model_fields:
            prefixed = f"MFLOW_{field_name.upper()}"
            bare = field_name.upper()
            if prefixed not in os.environ and bare in os.environ:
                values[field_name] = os.environ[bare]
        return values
