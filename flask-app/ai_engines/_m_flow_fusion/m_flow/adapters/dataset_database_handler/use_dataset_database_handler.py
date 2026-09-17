"""Register dataset database handlers."""

from __future__ import annotations

from typing import Any

from .supported_dataset_database_handlers import supported_dataset_database_handlers


def use_dataset_database_handler(
    handler_name: str,
    handler_instance: Any,
    provider: str,
) -> None:
    """
    Register a dataset database handler.

    Parameters
    ----------
    handler_name
        Unique handler identifier.
    handler_instance
        Handler implementation instance.
    provider
        Database provider name.
    """
    supported_dataset_database_handlers[handler_name] = {
        "handler_instance": handler_instance,
        "handler_provider": provider,
    }
