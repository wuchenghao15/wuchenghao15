"""M-Flow vector embedding protocol.

Declares the structural sub-typing contract that every concrete
embedding back-end (LiteLLM, FastEmbed, Ollama …) must satisfy.
Runtime duck-typing is intentional – no registration required.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingEngine(Protocol):
    """Structural protocol every M-Flow embedding adapter must implement.

    Concrete classes need **not** inherit from this protocol explicitly;
    any object exposing the three methods below with compatible signatures
    is accepted wherever ``EmbeddingEngine`` is expected.
    """

    __slots__ = ()

    async def embed_text(self, text: list[str]) -> list[list[float]]:
        """Transform *text* into dense floating-point vectors.

        Parameters
        ----------
        text:
            Sequence of raw strings to be embedded.

        Returns
        -------
        list[list[float]]
            One vector per input string, length equal to the model's
            native dimensionality.

        Raises
        ------
        NotImplementedError
            Always – protocol methods are not callable directly.
        """
        raise NotImplementedError("embed_text must be provided by an adapter")

    def get_vector_size(self) -> int:
        """Report the fixed dimensionality of vectors this engine produces.

        Raises
        ------
        NotImplementedError
            Always – protocol methods are not callable directly.
        """
        raise NotImplementedError("get_vector_size must be provided by an adapter")

    def get_batch_size(self) -> int:
        """Suggest the optimal number of texts per single embedding call.

        Raises
        ------
        NotImplementedError
            Always – protocol methods are not callable directly.
        """
        raise NotImplementedError("get_batch_size must be provided by an adapter")
