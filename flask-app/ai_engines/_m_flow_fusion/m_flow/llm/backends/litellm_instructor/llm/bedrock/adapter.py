"""
M-Flow AWS Bedrock structured-output adapter.

Provides synchronous and asynchronous structured generation through
AWS Bedrock foundation models.  Authentication is resolved in priority
order: explicit API key → IAM credentials → named AWS profile.
"""

from __future__ import annotations

from typing import Type

import instructor
import litellm
from instructor.exceptions import InstructorRetryException
from litellm.exceptions import ContentPolicyViolationError
from pydantic import BaseModel

from m_flow.llm.exceptions import ContentPolicyFilterError, MissingSystemPromptPathError
from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.backends.litellm_instructor.llm.llm_interface import (
    LLMBackend,
)
from m_flow.llm.backends.litellm_instructor.llm.rate_limiter import (
    rate_limit_async,
    rate_limit_sync,
    sleep_and_retry_async,
    sleep_and_retry_sync,
)
from m_flow.shared.files.storage.s3_config import get_s3_config
from m_flow.shared.observability.get_observe import get_observe

_trace = get_observe()

_CONTENT_VIOLATION_TYPES = (ContentPolicyViolationError, InstructorRetryException)
_POLICY_KEYWORD = "content management policy"
_INPUT_PREVIEW_LEN = 80


class BedrockAdapter(LLMBackend):
    """AWS Bedrock foundation-model adapter for M-Flow.

    Supports three credential strategies (checked in order):
    1. Bearer API key passed at construction time.
    2. Explicit AWS access-key / secret-key (with optional session token).
    3. Named AWS CLI profile resolved through the boto3 credential chain.
    """

    name = "Bedrock"
    model: str
    api_key: str | None
    default_instructor_mode = "json_schema_mode"
    MAX_RETRIES = 5

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        max_completion_tokens: int = 16384,
        streaming: bool = False,
        instructor_mode: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.max_completion_tokens = max_completion_tokens
        self.streaming = streaming

        active_mode = instructor_mode or self.default_instructor_mode
        self.instructor_mode = active_mode

        self.aclient = instructor.from_litellm(litellm.acompletion, mode=instructor.Mode(active_mode))
        self.client = instructor.from_litellm(litellm.completion)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_request(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
    ) -> dict:
        """Assemble completion parameters including AWS credential resolution."""
        request_payload: dict = {
            "model": self.model,
            "custom_llm_provider": "bedrock",
            "drop_params": True,
            "messages": [
                {"role": "user", "content": text_input},
                {"role": "system", "content": system_prompt},
            ],
            "response_model": response_model,
            "max_retries": self.MAX_RETRIES,
            "max_completion_tokens": self.max_completion_tokens,
            "stream": self.streaming,
        }

        aws_cfg = get_s3_config()

        if self.api_key:
            request_payload["api_key"] = self.api_key
        elif aws_cfg.aws_access_key_id and aws_cfg.aws_secret_access_key:
            request_payload["aws_access_key_id"] = aws_cfg.aws_access_key_id
            request_payload["aws_secret_access_key"] = aws_cfg.aws_secret_access_key
            if aws_cfg.aws_session_token:
                request_payload["aws_session_token"] = aws_cfg.aws_session_token
        elif aws_cfg.aws_profile_name:
            request_payload["aws_profile_name"] = aws_cfg.aws_profile_name

        if aws_cfg.aws_region:
            request_payload["aws_region_name"] = aws_cfg.aws_region

        if aws_cfg.aws_bedrock_runtime_endpoint:
            request_payload["aws_bedrock_runtime_endpoint"] = aws_cfg.aws_bedrock_runtime_endpoint

        return request_payload

    @staticmethod
    def _is_content_policy_error(exc: Exception) -> bool:
        """Determine whether *exc* stems from a content-policy violation."""
        if isinstance(exc, ContentPolicyViolationError):
            return True
        if isinstance(exc, InstructorRetryException):
            return _POLICY_KEYWORD in str(exc).lower()
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @_trace(as_type="generation")
    @sleep_and_retry_async()
    @rate_limit_async
    async def extract_structured(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Asynchronously produce a schema-validated response from Bedrock."""
        try:
            req = self._build_request(text_input, system_prompt, response_model)
            return await self.aclient.chat.completions.create(**req)
        except _CONTENT_VIOLATION_TYPES as exc:
            if not self._is_content_policy_error(exc):
                raise
            snippet = text_input[:_INPUT_PREVIEW_LEN]
            raise ContentPolicyFilterError(f"Content blocked: {snippet}...") from exc

    @_trace
    @sleep_and_retry_sync()
    @rate_limit_sync
    def extract_structured_sync(
        self,
        text_input: str,
        system_prompt: str,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Synchronously produce a schema-validated response from Bedrock."""
        req = self._build_request(text_input, system_prompt, response_model)
        return self.client.chat.completions.create(**req)

    def show_prompt(self, text_input: str, system_prompt: str) -> str:
        """Render the full prompt pair for diagnostic inspection."""
        display_input = text_input if text_input else "No user input provided."
        if not system_prompt:
            raise MissingSystemPromptPathError()

        from m_flow.llm.prompts import read_query_prompt

        rendered_system = read_query_prompt(system_prompt) or system_prompt
        return f"System Prompt:\n{rendered_system}\n\nUser Input:\n{display_input}\n"
