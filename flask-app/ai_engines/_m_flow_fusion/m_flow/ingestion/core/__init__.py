"""
Ingestion Core Module
=====================

Data classification, identification, and dataset discovery utilities.
"""

from __future__ import annotations

from .classify import classify
from .discover_directory_datasets import discover_directory_datasets
from .get_matched_datasets import get_matched_datasets
from .identify import identify
from .save_data_to_file import save_data_to_file

__all__ = [
    "classify",
    "discover_directory_datasets",
    "get_matched_datasets",
    "identify",
    "save_data_to_file",
]
