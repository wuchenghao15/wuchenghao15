"""
Gemini LLM adapter for M-flow.

Provides structured output generation via Google Gemini API.
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

# Error types that indicate content policy violations
_POLICY_ERRORS = (
    ContentFilterFinishReasonError,
    ContentPolicyViolationError,
    InstructorRetryException,
)


class GeminiAdapter(LLMBackend):
    """
    Adapter for Google Gemini models.

    Supports structured output with optional fallback model
    for content policy violations.
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
        api_version: str,
        max_completion_tokens: int,
        instructor_mode: str | None = None,
        fallback_model: str | None = None,
        fallback_api_key: str | None = None,
        fallback_endpoint: str | None = None,
    ) -> None:
        """
        Initialize the Gemini adapter.

        Args:
            endpoint: Gemini API base URL.
            api_key: API authentication key.
            model: Model identifier.
            api_version: API version string.
            max_completion_tokens: Output token limit.
            instructor_mode: Instructor extraction mode.
            fallback_model: Model to use on policy errors.
            fallback_api_key: API key for fallback.
            fallback_endpoint: Endpoint for fallback.
        """
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint
        self.api_version = api_version
        self.max_completion_tokens = max_completion_tokens

        self.fallback_model = fallback_model
        self.fallback_api_key = fallback_api_key
        self.fallback_endpoint = fallback_endpoint

        mode = instructor_mode or self.default_instructor_mode
        self.instructor_mode = mode

        self.aclient = instructor.from_litellm(
            litellm.acompletion,
            mode=instructor.Mode(mode),
        )

    def _is_policy_error(self, err: Exception) -> bool:
        """Check if error is a content policy violation."""
        if isinstance(err, InstructorRetryException):
            return "content management policy" in str(err).lower()
        return isinstance(err, _POLICY_ERRORS)

    async def _call_model(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        *,
        use_fallback: bool = False,
    ) -> BaseModel:
        """Make API call to primary or fallback model."""
        if use_fallback:
            model = self.fallback_model
            key = self.fallback_api_key
            base = self.fallback_endpoint
            version = None
        else:
            model = self.model
            key = self.api_key
            base = self.endpoint
            version = self.api_version

        params = {
            "model": model,
            "messages": [
                {"role": "user", "content": text_input},
                {"role": "system", "content": system_prompt},
            ],
            "api_key": key,
            "max_retries": 2,
            "api_base": base,
            "response_model": response_model,
        }
        if version:
            params["api_version"] = version

        return await self.aclient.chat.completions.create(**params)

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
        Generate structured output from Gemini.

        Falls back to secondary model if content policy violation occurs.

        Args:
            text_input: User message content.
            system_prompt: System instructions.
            response_model: Pydantic model for response.

        Returns:
            Parsed response conforming to response_model.

        Raises:
            ContentPolicyFilterError: If both primary and fallback fail.
        """
        try:
            async with llm_rate_limiter_context_manager():
                return await self._call_model(text_input, system_prompt, response_model)
        except _POLICY_ERRORS as err:
            if not self._is_policy_error(err):
                raise

            # Try fallback if configured
            if not all([self.fallback_model, self.fallback_api_key, self.fallback_endpoint]):
                raise ContentPolicyFilterError(f"Content blocked by policy: {text_input[:100]}...") from err

            try:
                async with llm_rate_limiter_context_manager():
                    return await self._call_model(text_input, system_prompt, response_model, use_fallback=True)
            except _POLICY_ERRORS as fallback_err:
                if not self._is_policy_error(fallback_err):
                    raise
                raise ContentPolicyFilterError(f"Content blocked by policy: {text_input[:100]}...") from fallback_err
