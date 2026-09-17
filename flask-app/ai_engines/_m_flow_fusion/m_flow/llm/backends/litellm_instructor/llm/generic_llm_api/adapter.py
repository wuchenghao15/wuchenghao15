"""
Generic LLM API adapter for M-flow.

Provides structured output generation via LiteLLM for any
OpenAI-compatible endpoint.
"""

from __future__ import annotations

import logging
from typing import Type

import instructor
import litellm
from instructor.core import InstructorRetryException
from litellm.exceptions import ContentPolicyViolationError
from openai import ContentFilterFinishReasonError
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.llm.exceptions import ContentPolicyFilterError
from m_flow.llm.backends.litellm_instructor.llm.llm_interface import (
    LLMBackend,
)
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import llm_rate_limiter_context_manager

_log = get_logger()

# Error types that may indicate content policy violations
_CONTENT_ERRORS = (
    ContentFilterFinishReasonError,
    ContentPolicyViolationError,
    InstructorRetryException,
)


class GenericAPIAdapter(LLMBackend):
    """
    Generic adapter for OpenAI-compatible LLM endpoints.

    Supports structured output with optional fallback model.
    """

    name: str
    model: str
    api_key: str
    default_instructor_mode = "json_mode"

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        name: str,
        max_completion_tokens: int,
        instructor_mode: str | None = None,
        fallback_model: str | None = None,
        fallback_api_key: str | None = None,
        fallback_endpoint: str | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint
        self.max_completion_tokens = max_completion_tokens

        self.fallback_model = fallback_model
        self.fallback_api_key = fallback_api_key
        self.fallback_endpoint = fallback_endpoint

        mode = instructor_mode or self.default_instructor_mode
        self.instructor_mode = mode

        self.aclient = instructor.from_litellm(litellm.acompletion, mode=instructor.Mode(mode))

    def _is_content_policy_error(self, err: Exception) -> bool:
        """Check if error is content policy related."""
        if isinstance(err, InstructorRetryException):
            return "content management policy" in str(err).lower()
        return isinstance(err, _CONTENT_ERRORS)

    async def _call_llm(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        *,
        use_fallback: bool = False,
    ) -> BaseModel:
        """Execute LLM call to primary or fallback endpoint."""
        if use_fallback:
            model = self.fallback_model
            key = self.fallback_api_key
            base = self.fallback_endpoint
        else:
            model = self.model
            key = self.api_key
            base = self.endpoint

        return await self.aclient.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": text_input},
                {"role": "system", "content": system_prompt},
            ],
            max_retries=2,
            api_key=key,
            api_base=base,
            response_model=response_model,
        )

    @retry(
        stop=stop_after_delay(120),
        wait=wait_exponential_jitter(5, 120),
        retry=retry_if_not_exception_type(
            (
                litellm.exceptions.NotFoundError,
                litellm.exceptions.BadRequestError,
                litellm.exceptions.AuthenticationError,
            )
        ),
        before_sleep=before_sleep_log(_log, logging.DEBUG),
        reraise=True,
    )
    async def extract_structured(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """
        Generate structured output from the LLM.

        Falls back to secondary model if content policy error occurs.
        """
        try:
            async with llm_rate_limiter_context_manager():
                return await self._call_llm(text_input, system_prompt, response_model)
        except _CONTENT_ERRORS as err:
            if not self._is_content_policy_error(err):
                raise

            if not all([self.fallback_model, self.fallback_api_key, self.fallback_endpoint]):
                raise ContentPolicyFilterError(f"Content blocked: {text_input[:80]}...") from err

            try:
                async with llm_rate_limiter_context_manager():
                    return await self._call_llm(text_input, system_prompt, response_model, use_fallback=True)
            except _CONTENT_ERRORS as fallback_err:
                if not self._is_content_policy_error(fallback_err):
                    raise
                raise ContentPolicyFilterError(f"Content blocked: {text_input[:80]}...") from fallback_err
