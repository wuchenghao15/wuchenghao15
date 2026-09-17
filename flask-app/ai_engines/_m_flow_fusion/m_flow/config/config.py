"""
Configuration containers for the memorization pipeline.

This module provides Pydantic-based configuration classes that control
document classification, summarization, and embedding behavior during
the memorize phase.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.shared.data_models import ContentPrediction, CompressedText


class MemorizeConfig(MflowSettings):
    """
    Pipeline configuration for document processing.

    Controls which models are used for classification and summarization,
    and whether triplet embeddings are enabled.

    Attributes:
        classification_model: Pydantic model class for content classification.
        summarization_model: Pydantic model class for generating summaries.
        triplet_embedding: Enable embedding of knowledge graph triplets.
    """

    _default_classification: ClassVar[type] = ContentPrediction
    _default_summarization: ClassVar[type] = CompressedText

    classification_model: type[Any] = Field(
        default_factory=lambda: ContentPrediction,
        description="Model class for content classification",
    )
    summarization_model: type[Any] = Field(
        default_factory=lambda: CompressedText,
        description="Model class for text summarization",
    )
    triplet_embedding: bool = Field(
        default=False,
        description="Whether to embed knowledge graph triplets",
    )

    model_config = SettingsConfigDict(
        env_prefix="MFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    def as_dict(self) -> dict[str, Any]:
        """
        Export configuration as a dictionary.

        Returns:
            Dictionary containing all configuration values.
        """
        return {
            "classification_model": self.classification_model,
            "summarization_model": self.summarization_model,
            "triplet_embedding": self.triplet_embedding,
        }


@lru_cache(maxsize=1)
def get_memorize_config() -> MemorizeConfig:
    """
    Retrieve the singleton memorize configuration instance.

    Uses LRU cache to ensure a single configuration instance
    is shared across the application.

    Returns:
        The cached MemorizeConfig instance.
    """
    return MemorizeConfig()
