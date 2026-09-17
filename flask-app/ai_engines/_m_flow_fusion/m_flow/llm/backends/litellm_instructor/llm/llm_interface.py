"""M-Flow LLM adapter contract.

Every LLM provider integration (OpenAI, Anthropic, local models, …) that
wants to participate in M-Flow's structured-output pipeline must satisfy
the :class:`LLMBackend` protocol defined here.

The protocol is deliberately minimal — a single async method — so that
adding a new backend requires very little boiler-plate.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, Type, TypeVar, runtime_checkable

from pydantic import BaseModel

_M = TypeVar("_M", bound=BaseModel)


@runtime_checkable
class LLMBackend(Protocol):
    """Structural protocol that every M-Flow LLM adapter must satisfy.

    The sole requirement is :meth:`extract_structured`, which
    accepts free-form text plus a Pydantic schema and returns a
    validated instance of that schema populated by the model.

    Being a :class:`typing.Protocol` means implementations do **not**
    need to explicitly inherit from this class; duck-typing is enough.
    """

    __slots__ = ()

    @abstractmethod
    async def extract_structured(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Request a schema-constrained completion from the LLM.

        Parameters
        ----------
        text_input:
            The user-facing message or document that the model should
            process.
        system_prompt:
            High-level instructions that steer the model's behaviour
            (persona, formatting rules, domain constraints, …).
        response_model:
            A :class:`pydantic.BaseModel` subclass describing the
            expected JSON shape.  The adapter is responsible for
            ensuring the raw model output is parsed into an instance
            of this type.

        Returns
        -------
        BaseModel
            A fully-validated instance of *response_model*.
        """
        ...
