"""
M-Flow Anthropic Claude structured-output adapter.

Wraps the Anthropic Messages API behind the common ``LLMBackend``
contract, using Instructor for schema-validated responses and Tenacity
for automatic retry with exponential back-off.
"""

from __future__ import annotations

import logging
from typing import Type

import instructor
import litellm
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.llm.config import get_llm_config
from m_flow.llm.backends.litellm_instructor.llm.llm_interface import (
    LLMBackend,
)
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import llm_rate_limiter_context_manager

_logger = get_logger()

_RESPONSE_TOKEN_CAP = 4096
_RETRY_CEILING_SECS = 120
_RETRY_BASE_WAIT = 5
_INSTRUCTOR_MAX_RETRIES = 2


class AnthropicAdapter(LLMBackend):
    """Structured-output adapter targeting Anthropic Claude models.

    Uses the native ``anthropic_tools`` instructor mode by default so that
    tool-use based extraction can leverage Claude's function-calling
    capabilities for reliable schema adherence.
    """

    name = "Anthropic"
    _default_mode = "anthropic_tools"

    def __init__(
        self,
        max_completion_tokens: int,
        model: str = None,
        instructor_mode: str = None,
    ):
        import anthropic

        llm_settings = get_llm_config()
        selected_mode = instructor_mode or self._default_mode

        self.model = model
        self.max_completion_tokens = max_completion_tokens

        raw_client = anthropic.AsyncAnthropic(api_key=llm_settings.llm_api_key)
        self.aclient = instructor.patch(
            create=raw_client.messages.create,
            mode=instructor.Mode(selected_mode),
        )

    @retry(
        stop=stop_after_delay(_RETRY_CEILING_SECS),
        wait=wait_exponential_jitter(_RETRY_BASE_WAIT, _RETRY_CEILING_SECS),
        retry=retry_if_not_exception_type(
            (
                litellm.exceptions.NotFoundError,
                litellm.exceptions.BadRequestError,
                litellm.exceptions.AuthenticationError,
            )
        ),
        before_sleep=before_sleep_log(_logger, logging.DEBUG),
        reraise=True,
    )
    async def extract_structured(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """Request a schema-validated response from Claude.

        Merges the caller-supplied ``text_input`` and ``system_prompt`` into a
        single user-role message and delegates to Instructor for automatic
        Pydantic validation of the model's reply.
        """
        merged_content = f"Extract from: {text_input}. {system_prompt}"

        async with llm_rate_limiter_context_manager():
            result = await self.aclient(
                model=self.model,
                max_tokens=_RESPONSE_TOKEN_CAP,
                max_retries=_INSTRUCTOR_MAX_RETRIES,
                messages=[{"role": "user", "content": merged_content}],
                response_model=response_model,
            )
        return result
