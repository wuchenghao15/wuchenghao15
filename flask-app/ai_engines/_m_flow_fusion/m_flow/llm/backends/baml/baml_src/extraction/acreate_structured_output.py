"""
Async structured output generation via BAML.

Provides functionality to generate type-safe structured responses from LLM
calls using the BAML framework with automatic retry and rate limiting.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Type, TypeVar

from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import llm_rate_limiter_context_manager

if TYPE_CHECKING:
    pass

_logger = get_logger()

# Retry configuration constants
_MAX_RETRY_SECONDS = 128
_INITIAL_WAIT_SECONDS = 8
_MAX_WAIT_SECONDS = 128

ModelT = TypeVar("ModelT", bound=BaseModel)


def _configure_retry_policy():
    """Build retry decorator with exponential backoff and jitter."""
    return retry(
        stop=stop_after_delay(_MAX_RETRY_SECONDS),
        wait=wait_exponential_jitter(_INITIAL_WAIT_SECONDS, _MAX_WAIT_SECONDS),
        before_sleep=before_sleep_log(_logger, logging.DEBUG),
        reraise=True,
    )


def _get_baml_client():
    """Lazy import of BAML client to avoid circular dependencies."""
    from m_flow.llm.backends.baml.baml_client import b

    return b


def _get_type_builder_class():
    """Lazy import of TypeBuilder."""
    from m_flow.llm.backends.baml.baml_client.type_builder import (
        TypeBuilder,
    )

    return TypeBuilder


def _build_dynamic_schema(response_schema: Type[BaseModel]):
    """
    Construct BAML type definitions from a Pydantic model.

    Returns the configured TypeBuilder instance.
    """
    from m_flow.llm.backends.baml.baml_src.extraction.create_dynamic_baml_type import (
        create_dynamic_baml_type,
    )

    TypeBuilder = _get_type_builder_class()
    builder = TypeBuilder()
    configured_builder = create_dynamic_baml_type(builder, builder.ResponseModel, response_schema)
    return configured_builder


def _extract_response_value(raw_result, target_model: Type[BaseModel]):
    """
    Transform BAML response into the target Pydantic model.

    For string models, extracts the text attribute directly.
    For complex models, validates through Pydantic.
    """
    if target_model is str:
        # String responses use a wrapper with 'text' attribute
        return str(raw_result.text)

    # Convert to dict and validate through Pydantic
    raw_dict = raw_result.dict()
    return target_model.model_validate(raw_dict)


@_configure_retry_policy()
async def acreate_structured_output(
    text_input: str,
    system_prompt: str,
    response_model: Type[ModelT],
) -> ModelT:
    """
    Generate structured LLM output matching a Pydantic schema.

    Uses BAML framework for type-safe structured generation with automatic
    rate limiting and retry logic for transient failures.

    Args:
        text_input: User-provided input text for generation
        system_prompt: Instruction prompt guiding model behavior
        response_model: Pydantic model class defining output structure

    Returns:
        Instance of response_model populated with generated content

    Raises:
        tenacity.RetryError: When all retry attempts exhausted
        pydantic.ValidationError: When response doesn't match schema
    """
    from m_flow.llm.config import get_llm_config

    llm_cfg = get_llm_config()
    baml_client = _get_baml_client()

    schema_builder = _build_dynamic_schema(response_model)

    baml_opts = {
        "client_registry": llm_cfg.baml_registry,
        "tb": schema_builder,
    }

    async with llm_rate_limiter_context_manager():
        raw_output = await baml_client.AcreateStructuredOutput(
            text_input=text_input,
            system_prompt=system_prompt,
            baml_options=baml_opts,
        )

    return _extract_response_value(raw_output, response_model)


def _run_demo():
    """Execute a simple demonstration of structured output generation."""
    from typing import Dict, List, Optional

    class DemoEntity(BaseModel):
        type: str
        source: Optional[str] = None
        target: Optional[str] = None
        properties: Optional[Dict[str, List[str]]] = None

    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    try:
        demo_input = "DEMO INPUT"
        demo_prompt = "DEMO SYSTEM PROMPT"
        event_loop.run_until_complete(acreate_structured_output(demo_input, demo_prompt, DemoEntity))
    finally:
        event_loop.run_until_complete(event_loop.shutdown_asyncgens())


if __name__ == "__main__":
    _run_demo()
