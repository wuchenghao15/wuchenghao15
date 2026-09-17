# m_flow.shared.loaders
# Plugin-oriented file-loader framework.
#
# The architecture mirrors database adapters: a thin ``LoaderInterface``
# protocol plus a registry (``LoaderEngine``) that picks the right
# implementation based on extension / MIME type.
#
# Quick start:
#   engine = get_loader_engine()
#   result = await engine.load("report.pdf")

from .get_loader_engine import get_loader_engine  # noqa: F401
from .use_loader import use_loader  # noqa: F401
from .LoaderInterface import LoaderInterface  # noqa: F401

__all__: list[str] = [
    "get_loader_engine",
    "use_loader",
    "LoaderInterface",
]
