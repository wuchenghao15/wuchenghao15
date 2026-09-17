"""
LoaderEngine factory with automatic loader registration.

Assembles a fully-configured LoaderEngine by discovering and
registering all available document loaders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from .LoaderEngine import LoaderEngine

_logger = get_logger(__name__)


def _register_all_loaders(engine: "LoaderEngine") -> None:
    """
    Register all available loaders with the engine.

    Iterates through supported loaders and attempts to register each.
    Loaders that fail to instantiate are logged and skipped.
    """
    from .supported_loaders import supported_loaders

    for loader_name, loader_class in supported_loaders.items():
        try:
            instance = loader_class()
            engine.register_loader(instance)
        except Exception as err:
            _logger.warning(
                "Skipping loader '%s' due to initialization error: %s",
                loader_name,
                err,
            )


def create_loader_engine() -> "LoaderEngine":
    """
    Construct a LoaderEngine with all available loaders registered.

    This factory creates a new LoaderEngine instance and populates it
    with every loader defined in the supported_loaders registry. Loaders
    with missing dependencies are gracefully skipped.

    Returns:
        A fully-configured LoaderEngine ready for use.

    Example:
        >>> engine = create_loader_engine()
        >>> path = await engine.load_file("/docs/report.pdf")
    """
    from .LoaderEngine import LoaderEngine

    engine = LoaderEngine()
    _register_all_loaders(engine)
    return engine
