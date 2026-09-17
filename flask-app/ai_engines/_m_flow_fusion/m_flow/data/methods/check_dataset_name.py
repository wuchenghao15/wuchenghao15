"""Dataset name validation."""

from __future__ import annotations


def check_dataset_name(dataset_name: str) -> None:
    """
    Validate dataset name does not contain invalid characters.

    Raises
    ------
    ValueError
        If dataset_name contains spaces or dots.
    """
    if "." in dataset_name or " " in dataset_name:
        raise ValueError("M-Flow dataset names must not include whitespace or period characters.")
