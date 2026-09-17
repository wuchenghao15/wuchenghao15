"""
Directory dataset discovery utility.

Recursively scans a directory tree and groups files by
their containing folder as dataset names.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional


def discover_directory_datasets(
    root_path: str,
    parent_name: Optional[str] = None,
) -> Dict[Optional[str], List[str]]:
    """
    Walk a directory tree and collect files grouped by dataset name.

    Dataset names are formed by joining nested folder names with dots.
    Files directly under the root (no parent_name) are keyed by None.

    Args:
        root_path: Absolute or relative path to scan.
        parent_name: Accumulated dataset name for nested calls.

    Returns:
        Mapping from dataset name to list of absolute file paths.
    """
    result: Dict[Optional[str], List[str]] = {}

    for entry in os.listdir(root_path):
        full_path = os.path.join(root_path, entry)

        if os.path.isdir(full_path):
            # Build nested dataset name
            dataset_key = entry if parent_name is None else f"{parent_name}.{entry}"
            nested = discover_directory_datasets(full_path, dataset_key)
            result.update(nested)
        else:
            # Add file to current dataset
            if parent_name not in result:
                result[parent_name] = []
            result[parent_name].append(full_path)

    return result
