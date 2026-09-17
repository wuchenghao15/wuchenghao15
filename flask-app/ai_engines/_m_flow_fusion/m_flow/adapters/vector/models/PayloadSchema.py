"""
Vector Storage Payload Schema
=============================

Generic type variable for defining custom payload structures
in vector database operations.
"""

from __future__ import annotations

from typing import TypeVar

# Type variable for vector payload schemas
# Used to type-hint custom payload structures across adapters
PayloadSchema = TypeVar("PayloadSchema")
