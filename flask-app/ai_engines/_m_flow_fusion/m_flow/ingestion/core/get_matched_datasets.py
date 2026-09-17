"""Dataset matching utility."""

from __future__ import annotations

from typing import List, Optional, Tuple

from .discover_directory_datasets import discover_directory_datasets


def get_matched_datasets(
    data_path: str,
    dataset_name_to_match: Optional[str] = None,
) -> List[Tuple[str, List[str]]]:
    """Return datasets matching the optional name prefix filter."""
    datasets = discover_directory_datasets(data_path)

    results = []
    for name, files in datasets.items():
        if dataset_name_to_match is None or name.startswith(dataset_name_to_match):
            results.append((name, files))

    return results
