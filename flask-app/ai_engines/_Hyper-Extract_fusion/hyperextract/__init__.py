"""HyperExtract - AI-powered data structure extraction from unstructured text.

This library provides Auto-prefixed intelligent data structures that automatically
extract structured information from text using Large Language Models (LLMs).

Architecture:
- types: Core data structure primitives (AutoModel, AutoList, AutoSet, AutoGraph, etc.)
- methods: Algorithms and strategies (rag, typical graph construction methods)
- templates: Domain-specific extraction templates

Usage:
    from hyperextract import Template

    # List available templates
    Template.list()

    # 1. Create knowledge template (auto reads config from ~/.he/config.toml)
    template = Template.create("general/graph", language="zh")

    # 2. Create method template (language always "en")
    template = Template.create("method/light_rag")
"""

# Core AutoType primitives
from importlib.metadata import version

from .types import (
    AutoDocument,
    AutoGraph,
    AutoHypergraph,
    AutoList,
    AutoModel,
    AutoSet,
    AutoSpatialGraph,
    AutoSpatioTemporalGraph,
    AutoTemporalGraph,
    BaseAutoType,
)

# Client factory
from .utils.client import create_client, create_embedder, create_llm, get_client

# Logging utilities
from .utils.logging import configure_logging, get_logger, set_log_level

# Template engine API
from .utils.template_engine import Template

__version__ = version("hyperextract")
__author__ = "Yifan Feng"
__email__ = "evanfeng97@gmail.com"

__all__ = [
    # Corpus type
    "AutoDocument",
    # Graph types
    "AutoGraph",
    "AutoHypergraph",
    "AutoList",
    # Scalar types
    "AutoModel",
    "AutoSet",
    "AutoSpatialGraph",
    "AutoSpatioTemporalGraph",
    "AutoTemporalGraph",
    # Base class
    "BaseAutoType",
    # Template engine
    "Template",
    # Logging utilities
    "configure_logging",
    # Client factory
    "create_client",
    "create_embedder",
    "create_llm",
    "get_client",
    "get_logger",
    "set_log_level",
]
