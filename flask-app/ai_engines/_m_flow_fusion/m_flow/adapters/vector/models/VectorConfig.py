"""
Vector Storage Configuration Model
===================================

Pydantic model defining configuration options for vector
database connections and similarity calculations.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# Supported distance metrics for vector similarity
DistanceMetric = Literal["Cosine", "Dot"]


class VectorConfig(BaseModel):
    """
    Vector storage configuration settings.

    This model defines the parameters needed to configure
    a vector database connection, including the similarity
    metric and embedding dimensions.

    Attributes
    ----------
    distance : DistanceMetric
        Similarity calculation method.
        - "Cosine": Angle-based similarity (normalized).
        - "Dot": Raw dot product (unnormalized).
    size : int
        Number of dimensions in embedding vectors.
        Must match the embedding model's output size.
    """

    distance: DistanceMetric = Field(
        default="Cosine",
        description="Similarity metric for vector comparisons",
    )
    size: int = Field(
        ...,
        description="Embedding vector dimensionality",
        gt=0,
    )
