"""
Shared utilities and infrastructure for M-flow.

This package contains cross-cutting concerns used throughout
the M-flow codebase, including:

- Configuration management
- Logging utilities
- File handling infrastructure
- Data models and type definitions
- Common exceptions

Environment Bootstrap
---------------------
This module ensures that environment variables from .env files
are loaded before any configuration modules access them.
"""

from __future__ import annotations


def _load_environment_config() -> None:
    """
    Bootstrap environment variables from .env files.

    Uses python-dotenv to load variables. With override=False,
    existing environment variables take precedence over .env values,
    allowing users to explicitly configure settings before import.
    """
    try:
        from dotenv import load_dotenv

        # override=False: User environment variables take precedence over .env file
        load_dotenv(override=False)
    except ImportError:
        # dotenv not installed - skip environment loading
        pass


# Execute environment loading on module import
_load_environment_config()
