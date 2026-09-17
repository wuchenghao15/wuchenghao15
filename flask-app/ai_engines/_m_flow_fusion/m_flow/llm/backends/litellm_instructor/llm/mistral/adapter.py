"""
Mistral LLM adapter for structured output generation.

Uses LiteLLM + Instructor for structured response extraction.
"""

from __future__ import annotations

import logging
from typing import Type

import instructor
import litellm
from litellm import JSONSchemaValidationError
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

_log = get_logger()


class MistralAdapter(LLMBackend):
    """
    Mistral AI structured output adapter.

    Wraps LiteLLM completion with Instructor for Pydantic validation.
    """

    name = "Mistral"
    default_instructor_mode = "mistral_tools"

    def __init__(
        self,
        api_key: str,
        model: str,
        max_completion_tokens: int,
        endpoint: str = None,
        instructor_mode: str = None,
    ):
        self.model = model
        self.max_completion_tokens = max_completion_tokens
        self.instructor_mode = instructor_mode or self.default_instructor_mode

        # Initialize instructor-patched client
        self.aclient = instructor.from_litellm(
            litellm.acompletion,
            mode=instructor.Mode(self.instructor_mode),
            api_key=get_llm_config().llm_api_key,
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
        Generate structured output from Mistral.

        Args:
            text_input: User input text.
            system_prompt: System context prompt.
            response_model: Pydantic model for response validation.

        Returns:
            Validated Pydantic model instance.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract from: {text_input}"},
        ]

        try:
            async with llm_rate_limiter_context_manager():
                resp = await self.aclient.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_completion_tokens,
                    max_retries=2,
                    messages=messages,
                    response_model=response_model,
                )

            if resp.choices and resp.choices[0].message.content:
                return response_model.model_validate_json(resp.choices[0].message.content)

            raise ValueError("No valid response received")

        except litellm.exceptions.BadRequestError as e:
            _log.error(f"Bad request: {e}")
            raise ValueError(f"Invalid request: {e}")

        except JSONSchemaValidationError as e:
            _log.error(f"Schema validation failed: {e}")
            raise ValueError(f"Response validation failed: {e}")
