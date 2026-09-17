"""
M-Flow Response API – data models for tool-augmented completions.

Provides Pydantic schemas that mirror the OpenAI Responses API surface
while remaining specific to the M-Flow runtime.  All identifier generation
is handled through dedicated factory helpers rather than inline lambdas so
that the creation logic can be patched or overridden in tests.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, Field

from m_flow.api.DTO import InDTO, OutDTO


# ---------------------------------------------------------------------------
# Identifier factories
# ---------------------------------------------------------------------------


def _generate_call_identifier() -> str:
    """Produce a globally unique call identifier prefixed with ``call_``."""
    return f"call_{uuid.uuid4().hex}"


def _generate_response_identifier() -> str:
    """Produce a globally unique response identifier prefixed with ``resp_``."""
    return f"resp_{uuid.uuid4().hex}"


def _current_epoch() -> int:
    """Return the current UNIX epoch as an integer."""
    return int(time.time())


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class MflowModel(str, Enum):
    """Supported M-Flow model revisions."""

    MFLOW_V1 = "m_flow-v1"


# ---------------------------------------------------------------------------
# Function / Tool primitives
# ---------------------------------------------------------------------------


class FunctionParameters(BaseModel):
    """
    JSON-Schema descriptor for the parameters accepted by a callable tool.

    The ``type`` field is always ``"object"``; ``properties`` maps each
    parameter name to its own JSON-Schema definition; ``required`` lists
    the names of mandatory parameters (may be absent when all are optional).
    """

    type: str = "object"
    properties: Mapping[str, Mapping[str, Any]]
    required: Sequence[str] | None = None


class Function(BaseModel):
    """
    Metadata envelope describing a single invocable function.

    Carries the function's symbolic ``name``, a human-readable
    ``description``, and a ``parameters`` schema that callers must respect.
    """

    name: str
    description: str
    parameters: FunctionParameters


class ToolFunction(BaseModel):
    """Wraps a :class:`Function` inside a typed tool container."""

    type: str = "function"
    function: Function


class FunctionCall(BaseModel):
    """
    Represents the invocation of a specific function.

    ``name`` identifies which function to call; ``arguments`` contains a
    JSON-encoded string of the actual parameter values.
    """

    name: str
    arguments: str


class ToolCall(BaseModel):
    """
    A tool invocation emitted by the assistant.

    Each instance is assigned a unique ``id`` at construction time so that
    responses can be correlated with their originating calls.
    """

    id: str = Field(default_factory=_generate_call_identifier)
    type: str = "function"
    function: FunctionCall


# ---------------------------------------------------------------------------
# Usage / output helpers
# ---------------------------------------------------------------------------


class ChatUsage(BaseModel):
    """
    Aggregated token-budget accounting for a single response cycle.

    All counters default to zero and are populated by the serving layer
    once the completion has been produced.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCallOutput(BaseModel):
    """Captures the outcome of executing a single tool call."""

    status: str = "success"
    data: Mapping[str, Any] | None = None


# ---------------------------------------------------------------------------
# Request / Response envelopes
# ---------------------------------------------------------------------------


class ResponseRequest(InDTO):
    """
    Inbound payload for the ``/responses`` endpoint.

    Mirrors the OpenAI Responses API shape with M-Flow-specific defaults.
    ``tool_choice`` may be the literal string ``"auto"`` or a mapping that
    constrains tool selection to a specific function.

    ``model`` accepts either the synthetic ``m_flow-v1`` alias or a concrete
    provider model name. The serving layer resolves ``m_flow-v1`` to the
    configured default model from :func:`m_flow.llm.config.get_llm_config`.
    """

    model: str = MflowModel.MFLOW_V1.value
    input: str
    tools: Sequence[ToolFunction] | None = None
    tool_choice: str | Mapping[str, Any] | None = "auto"
    user: str | None = None
    temperature: float | None = 1.0
    max_completion_tokens: int | None = None


class ResponseToolCall(BaseModel):
    """A tool call entry inside a completed response, optionally paired with its output."""

    id: str = Field(default_factory=_generate_call_identifier)
    type: str = "function"
    function: FunctionCall
    output: ToolCallOutput | None = None


class ResponseBody(OutDTO):
    """
    Outbound payload returned by the ``/responses`` endpoint.

    Contains the full set of tool calls selected by the model, optional
    token-usage statistics, and an open ``metadata`` bag for caller-defined
    annotations.
    """

    id: str = Field(default_factory=_generate_response_identifier)
    created: int = Field(default_factory=_current_epoch)
    model: str
    object: str = "response"
    status: str = "completed"
    tool_calls: Sequence[ResponseToolCall]
    usage: ChatUsage | None = None
    metadata: Mapping[str, Any] | None = None
