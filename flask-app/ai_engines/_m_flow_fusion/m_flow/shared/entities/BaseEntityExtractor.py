"""
Abstract base for entity extraction strategies.

Subclasses must implement :meth:`extract_entities` to convert a raw
text string into a structured list of :class:`Entity` instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from m_flow.core.domain.models import Entity


class BaseEntityExtractor(ABC):
    """Interface that every entity-extraction strategy must satisfy."""

    @abstractmethod
    async def extract_entities(
        self,
        text: str,
    ) -> Sequence[Entity]:
        """Identify and return entities found in *text*.

        Args:
            text: Unstructured input from which entities are mined.

        Returns:
            An ordered collection of extracted :class:`Entity` objects.
        """
        ...


# Backward compatibility alias
BaseConceptExtractor = BaseEntityExtractor
