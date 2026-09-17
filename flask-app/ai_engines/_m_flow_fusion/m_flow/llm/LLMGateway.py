"""
Unified LLM service for M-Flow.

All structured-output, transcription, and image-processing calls are
routed through this module.  The active backend (BAML vs LiteLLM/Instructor)
is resolved lazily at call time from the shared LLM configuration.
"""

from __future__ import annotations

import logging
from typing import Coroutine, Type

import litellm
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.llm import get_llm_config

_RETRY_CEILING = 120
_BACKOFF_MIN = 5
_BACKOFF_MAX = 120

# ---------------------------------------------------------------------------
# Backend resolution
# ---------------------------------------------------------------------------


def _is_baml_backend() -> bool:
    return get_llm_config().backends.upper() == "BAML"


def _get_instructor_client():
    from m_flow.llm.backends.litellm_instructor.llm.get_llm_client import (
        create_llm_backend,
    )

    return create_llm_backend()


def _get_baml_extractor():
    from m_flow.llm.backends.baml.baml_src.extraction import (
        extract_structured as _baml_extract,
    )

    return _baml_extract


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class LLMService:
    """
    Namespace class routing LLM calls to the configured backend.

    Not meant to be instantiated — every method is ``@staticmethod``.
    """

    @staticmethod
    def extract_structured(
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        **kwargs,
    ) -> Coroutine:
        """Return a coroutine that produces a *response_model* instance."""
        if _is_baml_backend():
            return _get_baml_extractor()(
                text_input=text_input,
                system_prompt=system_prompt,
                response_model=response_model,
            )

        return _get_instructor_client().extract_structured(
            text_input=text_input,
            system_prompt=system_prompt,
            response_model=response_model,
            **kwargs,
        )

    @staticmethod
    def extract_structured_sync(
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Synchronous structured extraction (Instructor-only)."""
        return _get_instructor_client().extract_structured_sync(
            text_input=text_input,
            system_prompt=system_prompt,
            response_model=response_model,
        )

    @staticmethod
    def transcribe_audio(input) -> Coroutine:
        """Transcribe audio via the Instructor client."""
        return _get_instructor_client().transcribe_audio(input=input)

    @staticmethod
    def describe_image(input) -> Coroutine:
        """Extract text from an image via the Instructor client."""
        return _get_instructor_client().describe_image(input=input)

    @staticmethod
    @retry(
        stop=stop_after_delay(_RETRY_CEILING),
        wait=wait_exponential_jitter(_BACKOFF_MIN, _BACKOFF_MAX),
        retry=retry_if_not_exception_type(
            (
                litellm.exceptions.NotFoundError,
                litellm.exceptions.BadRequestError,
                litellm.exceptions.AuthenticationError,
            )
        ),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.DEBUG),
        reraise=True,
    )
    async def complete_text(
        source_text: str,
        instructions: str,
        **kwargs,
    ) -> str:
        """
        Raw text completion via litellm (no structured extraction).

        Retries automatically on transient errors with exponential backoff.
        """
        from m_flow.llm import get_llm_config as _cfg
        from m_flow.shared.logging_utils import get_logger
        from m_flow.shared.rate_limiting import llm_rate_limiter_context_manager

        _log = get_logger(__name__)
        cfg = _cfg()

        async with llm_rate_limiter_context_manager():
            messages = [
                {"role": "system", "content": instructions},
                {"role": "user", "content": source_text},
            ]

            _log.debug(
                "text_completion request  model=%s  sys_len=%d  user_len=%d",
                cfg.llm_model,
                len(instructions),
                len(source_text),
            )

            call_kwargs = {
                "model": cfg.llm_model,
                "messages": messages,
                "api_key": cfg.llm_api_key,
                "api_base": cfg.llm_endpoint or None,
                "api_version": cfg.llm_api_version or None,
                **kwargs,
            }
            response = await litellm.acompletion(**call_kwargs)
            reply = response.choices[0].message.content or ""
            _log.debug("text_completion response  len=%d", len(reply))
            return reply
