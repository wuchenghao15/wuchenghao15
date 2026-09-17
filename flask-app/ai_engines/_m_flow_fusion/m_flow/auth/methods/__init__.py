"""
Auth method implementations for M-flow.

Contains core authentication and authorization functions.
"""

from __future__ import annotations

# Explicit imports to ensure functions are accessible
from .create_default_user import create_default_user
from .create_user import create_user
from .delete_user import delete_user
from .get_authenticated_user import get_authenticated_user
from .get_seed_user import get_seed_user
from .get_user import get_user
from .get_user_by_email import get_user_by_email

__all__ = [
    "create_default_user",
    "create_user",
    "delete_user",
    "get_authenticated_user",
    "get_seed_user",
    "get_user",
    "get_user_by_email",
]
