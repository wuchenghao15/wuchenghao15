"""
Security utilities for authentication configuration.

Provides environment-based secret management with production safety checks.
"""

from __future__ import annotations

import os

from m_flow.shared.logging_utils import get_logger

_log = get_logger("auth.security")

# Track warned secrets to avoid duplicate log messages
_warned_secrets: set[str] = set()


def get_secret_with_production_check(
    env_var: str,
    default_value: str,
    secret_name: str,
) -> str:
    """
    Get secret from environment with production safety check.

    In non-development environments (production, staging, test, etc.),
    raises RuntimeError if the secret is not configured.
    In development environments, returns the default value with a warning.

    Parameters
    ----------
    env_var : str
        Name of the environment variable to read.
    default_value : str
        Default value to use in development if env var is not set.
    secret_name : str
        Human-readable name for logging purposes.

    Returns
    -------
    str
        The secret value from environment or default.

    Raises
    ------
    RuntimeError
        If running in non-development environment and secret is not configured.

    Examples
    --------
    >>> secret = get_secret_with_production_check(
    ...     "JWT_SECRET", "dev_secret", "JWT authentication"
    ... )
    """
    secret = os.getenv(env_var)
    if secret:
        return secret

    # Security policy: only allow default secrets in explicit development environments
    # Any other value (production, staging, test, prod, etc.) requires configuration
    env = os.getenv("MFLOW_ENV", "").lower()
    is_dev = env in ("", "development", "dev", "local")

    if not is_dev:
        raise RuntimeError(
            f"CRITICAL: {env_var} must be set when MFLOW_ENV={env!r}. "
            f'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
        )

    # Development environment: use default secret with warning (warn only once)
    if env_var not in _warned_secrets:
        _warned_secrets.add(env_var)
        _log.warning(
            "Using default %s for development. Set %s for production.",
            secret_name,
            env_var,
        )
    return default_value
