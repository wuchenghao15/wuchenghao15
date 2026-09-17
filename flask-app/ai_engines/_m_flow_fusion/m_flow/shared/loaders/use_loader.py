"""
Dynamic loader registration API.

Allows runtime registration of custom document loaders
into the M-flow loader registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .LoaderInterface import LoaderInterface


def use_loader(loader_name: str, loader_class: Type["LoaderInterface"]) -> None:
    """
    Register a custom loader in the global registry.

    The registered loader becomes available to the LoaderEngine
    for document processing. Can be called at any time before
    or after engine initialization.

    Args:
        loader_name: Unique identifier for the loader.
        loader_class: Loader class implementing LoaderInterface.

    Example:
        >>> from my_loaders import CustomMarkdownLoader
        >>> use_loader("markdown", CustomMarkdownLoader)
    """
    from .supported_loaders import supported_loaders

    supported_loaders[loader_name] = loader_class
