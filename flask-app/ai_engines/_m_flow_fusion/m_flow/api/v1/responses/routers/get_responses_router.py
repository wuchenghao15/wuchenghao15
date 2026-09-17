"""
OpenAI-compatible responses API router.

Provides function-calling support via M-flow tools.
"""

from __future__ import annotations

import uuid
from typing import Any

import openai
from fastapi import APIRouter, Depends

from m_flow.api.v1.responses.default_tools import DEFAULT_TOOLS
from m_flow.api.v1.responses.dispatch_function import dispatch_function
from m_flow.api.v1.responses.models import (
    ChatUsage,
    FunctionCall,
    MflowModel,
    ResponseBody,
    ResponseRequest,
    ResponseToolCall,
    ToolCallOutput,
)
from m_flow.auth.methods import get_authenticated_user
from m_flow.auth.models import User
from m_flow.llm.config import get_llm_config
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)


def get_responses_router() -> APIRouter:
    """Build the responses API router."""
    router = APIRouter()

    def _build_client() -> openai.AsyncOpenAI:
        cfg = get_llm_config()
        return openai.AsyncOpenAI(api_key=cfg.llm_api_key)

    def _resolve_model(requested_model: str) -> str:
        """Resolve the synthetic M-flow alias to a concrete provider model."""
        cfg = get_llm_config()
        if not requested_model or requested_model == MflowModel.MFLOW_V1.value:
            return cfg.llm_model
        return requested_model

    async def _invoke_model(
        text: str,
        model: str,
        tools: list[dict[str, Any]] | None,
        tool_choice: Any,
        temperature: float,
    ) -> dict[str, Any]:
        """Send request to the configured OpenAI-compatible responses API."""
        resolved_model = _resolve_model(model)
        client = _build_client()

        _log.debug("Invoking model: %s", resolved_model)
        resp = await client.responses.create(
            model=resolved_model,
            input=text,
            temperature=temperature,
            tools=tools or DEFAULT_TOOLS,
            tool_choice=tool_choice,
        )
        _log.info("API response received")
        payload = resp.model_dump()
        payload.setdefault("model", resolved_model)
        return payload

    @router.post("/", response_model=ResponseBody)
    async def create_response(
        request: ResponseRequest,
        user: User = Depends(get_authenticated_user),
    ) -> ResponseBody:
        """
        Process input via OpenAI API with M-flow function calling.

        Returns an OpenAI-compatible response with executed tool results.
        """
        tools = request.tools or DEFAULT_TOOLS

        api_resp = await _invoke_model(
            text=request.input,
            model=request.model,
            tools=tools,
            tool_choice=request.tool_choice,
            temperature=request.temperature,
        )

        resp_id = api_resp.get("id") or f"resp_{uuid.uuid4().hex}"
        output_items = api_resp.get("output", [])

        processed_calls = []
        for item in output_items:
            if not isinstance(item, dict) or item.get("type") != "function_call":
                continue

            fn_name = item.get("name", "")
            args_json = item.get("arguments", "{}")
            call_id = item.get("call_id") or f"call_{uuid.uuid4().hex}"

            # Prepare dispatcher-compatible format
            call_spec = {
                "id": call_id,
                "type": "function",
                "function": {"name": fn_name, "arguments": args_json},
            }

            # Execute
            try:
                result = await dispatch_function(call_spec)
                status = "success"
            except Exception as exc:
                _log.exception("Tool %s failed: %s", fn_name, exc)
                result = f"Error: {exc}"
                status = "error"

            processed_calls.append(
                ResponseToolCall(
                    id=call_id,
                    type="function",
                    function=FunctionCall(name=fn_name, arguments=args_json),
                    output=ToolCallOutput(status=status, data={"result": result}),
                )
            )

        # Extract usage metrics
        usage_data = api_resp.get("usage", {})

        return ResponseBody(
            id=resp_id,
            model=api_resp.get("model", request.model),
            tool_calls=processed_calls,
            usage=ChatUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
        )

    return router
