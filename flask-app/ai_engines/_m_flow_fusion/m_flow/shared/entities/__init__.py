# m_flow.shared.entities
# Base abstractions for entity extraction used across ingestion stages.
#
# Entity extractors identify domain entities from unstructured text and
# return normalised representations suitable for downstream graph assembly.

from .BaseEntityExtractor import BaseEntityExtractor, BaseConceptExtractor  # noqa: F401

__all__: list[str] = ["BaseEntityExtractor", "BaseConceptExtractor"]
