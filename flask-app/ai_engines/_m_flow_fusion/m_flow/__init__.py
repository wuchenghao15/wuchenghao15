# ruff: noqa: E402
"""
M-flow — cognitive memory engine for AI agents.

Core operations: add · memorize · learn · search · ingest · query
Manual control: manual_ingest · manual_add_episode · patch_node
"""

from m_flow.version import get_version as _ver

__version__: str = _ver()

import dotenv as _dotenv

_dotenv.load_dotenv(override=False)

from m_flow.shared.logging_utils import setup_logging as _setup

logger = _setup()

# ── Core memory operations ────────────────────────────────────────
from .api.v1.add import add  # noqa: E402
from .api.v1.memorize import memorize  # noqa: E402
from .api.v1.learn import learn  # noqa: E402
from .api.v1.search import search, query, RecallMode, QueryResult, SearchConfig  # noqa: E402
from .api.v1.ingest import ingest, IngestResult, IngestStatus  # noqa: E402

# ── Data management ───────────────────────────────────────────────
from .api.v1.datasets.datasets import datasets  # noqa: E402
from .api.v1.delete import delete  # noqa: E402
from .api.v1.update import update  # noqa: E402
from .api.v1.prune import prune  # noqa: E402
from .shared.enums import ContentType  # noqa: E402

# ── Manual ingestion (bypass LLM extraction) ──────────────────────
from .api.v1.manual import (  # noqa: E402
    manual_ingest,
    manual_add_episode,
    patch_node,
    ManualIngestRequest,
    ManualEpisodeInput,
    ManualFacetInput,
    ManualFacetPointInput,
    ManualConceptInput,
    PatchNodeRequest,
)

# ── Configuration & UI ────────────────────────────────────────────
from .api.v1.config.config import config  # noqa: E402
from .api.v1.ui import start_ui  # noqa: E402
from .api.v1 import maintenance  # noqa: E402

# ── Advanced / pipeline ───────────────────────────────────────────
from .pipeline.custom import run_custom_pipeline  # noqa: E402
from . import pipeline as pipelines  # noqa: E402

__all__ = [
    # Core operations
    "add",
    "memorize",
    "learn",
    "search",
    "query",
    "ingest",
    # Search types
    "RecallMode",
    "QueryResult",
    "SearchConfig",
    "IngestResult",
    "IngestStatus",
    "ContentType",
    # Data management
    "datasets",
    "delete",
    "update",
    "prune",
    # Manual ingestion
    "manual_ingest",
    "manual_add_episode",
    "patch_node",
    "ManualIngestRequest",
    "ManualEpisodeInput",
    "ManualFacetInput",
    "ManualFacetPointInput",
    "ManualConceptInput",
    "PatchNodeRequest",
    # Configuration & UI
    "config",
    "start_ui",
    "maintenance",
    # Advanced
    "pipelines",
    "run_custom_pipeline",
]
