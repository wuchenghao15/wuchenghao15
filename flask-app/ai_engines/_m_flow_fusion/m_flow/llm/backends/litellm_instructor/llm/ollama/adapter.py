"""
Ollama adapter — structured outputs via local Ollama server.

This module wraps an Ollama-compatible OpenAI endpoint with
instructor for schema-constrained generation.
"""

from __future__ import annotations

import base64
import logging
from typing import Type

import instructor
import litellm
from openai import OpenAI
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from m_flow.llm.backends.litellm_instructor.llm.llm_interface import (
    LLMBackend,
)
from m_flow.shared.files.utils.open_data_file import open_data_file
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.rate_limiting import llm_rate_limiter_context_manager

_logger = get_logger()

# Retry configuration: 120s total with jitter
_RETRY_CFG = {
    "stop": stop_after_delay(120),
    "wait": wait_exponential_jitter(5, 120),
    "retry": retry_if_not_exception_type(
        (litellm.exceptions.NotFoundError, litellm.exceptions.BadRequestError, litellm.exceptions.AuthenticationError)
    ),
    "before_sleep": before_sleep_log(_logger, logging.DEBUG),
    "reraise": True,
}


class OllamaAPIAdapter(LLMBackend):
    """
    LLM adapter for Ollama servers via OpenAI-compatible API.

    Capabilities:
      - Structured output (JSON mode)
      - Audio transcription (Whisper)
      - Vision/image description
    """

    default_instructor_mode = "json_mode"

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        name: str,
        max_completion_tokens: int,
        instructor_mode: str | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint
        self.max_completion_tokens = max_completion_tokens

        self.instructor_mode = instructor_mode or self.default_instructor_mode

        raw_client = OpenAI(base_url=endpoint, api_key=api_key)
        self.aclient = instructor.from_openai(raw_client, mode=instructor.Mode(self.instructor_mode))

    @retry(**_RETRY_CFG)
    async def extract_structured(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """Request structured JSON output from Ollama."""
        async with llm_rate_limiter_context_manager():
            return self.aclient.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": text_input},
                    {"role": "system", "content": system_prompt},
                ],
                max_retries=2,
                response_model=response_model,
            )

    @retry(**_RETRY_CFG)
    async def transcribe_audio(self, input_file: str, **kwargs) -> str:
        """Transcribe audio via Whisper model."""
        async with open_data_file(input_file, mode="rb") as fp:
            resp = self.aclient.audio.transcriptions.create(model="whisper-1", file=fp, language="en")

        if not getattr(resp, "text", None):
            raise ValueError("Audio transcription yielded no text")
        return resp.text

    @retry(
        stop=stop_after_delay(120),
        wait=wait_exponential_jitter(2, 120),
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
    async def describe_image(self, input_file: str, **kwargs) -> str:
        """Describe image content using vision model."""
        async with open_data_file(input_file, mode="rb") as fp:
            encoded = base64.b64encode(fp.read()).decode("ascii")

        vision_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                },
            ],
        }

        completion = self.aclient.chat.completions.create(
            model=self.model, messages=[vision_msg], max_completion_tokens=300
        )

        if not getattr(completion, "choices", None):
            raise ValueError("Vision model returned empty response")

        return completion.choices[0].message.content
