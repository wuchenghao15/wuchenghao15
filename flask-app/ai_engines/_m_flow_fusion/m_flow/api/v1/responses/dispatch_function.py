"""
Function dispatcher module.

Provides functionality to dispatch tool calls to corresponding Mflow functions.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

from m_flow.api.v1.responses.models import ToolCall
from m_flow.search.types import RecallMode
from m_flow.api.v1.add import add
from m_flow.api.v1.search import search
from m_flow.api.v1.memorize import memorize
from m_flow.api.v1.prune import prune
from m_flow.auth.methods import get_seed_user
from m_flow.api.v1.responses.default_tools import DEFAULT_TOOLS
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

# Function handler type definition
DispatchHandler = Callable[[dict, Any], Awaitable[Any]]


def _locate_tool_config(tool_name: str) -> dict | None:
    """Locate tool configuration."""
    for tool_def in DEFAULT_TOOLS:
        if tool_def.get("name") == tool_name:
            return tool_def
    return None


def _extract_call_info(raw_call: ToolCall | dict) -> tuple[str, dict]:
    """Extract function name and arguments from tool call."""
    if isinstance(raw_call, dict):
        func_info = raw_call.get("function", {})
        fn_name = func_info.get("name", "")
        arg_json = func_info.get("arguments", "{}")
    else:
        fn_name = raw_call.function.name
        arg_json = raw_call.function.arguments

    parsed_args = json.loads(arg_json)
    return fn_name, parsed_args


def _resolve_recall_mode(mode_str: str, tool_cfg: dict | None) -> RecallMode:
    """Resolve recall mode."""
    fallback_modes = ["TRIPLET_COMPLETION", "EPISODIC", "PROCEDURAL"]

    if tool_cfg is not None:
        props = tool_cfg.get("parameters", {}).get("properties", {})
        mode_prop = props.get("recall_mode", {})
        allowed = mode_prop.get("enum", fallback_modes)
    else:
        allowed = fallback_modes

    if mode_str not in allowed:
        _log.warning("Invalid recall mode %s, falling back to TRIPLET_COMPLETION", mode_str)
        mode_str = "TRIPLET_COMPLETION"

    return RecallMode[mode_str]


async def _process_search(params: dict, current_user) -> list:
    """Process search request."""
    cfg = _locate_tool_config("search")

    # Validate required parameters
    if cfg is not None:
        mandatory = cfg.get("parameters", {}).get("required", [])
    else:
        mandatory = ["search_query"]

    query_text = params.get("search_query")
    if query_text is None and "search_query" in mandatory:
        return "Error: Missing required 'search_query' parameter"

    # Parse recall mode
    mode_input = params.get("recall_mode", "TRIPLET_COMPLETION")
    recall = _resolve_recall_mode(mode_input, cfg)

    # Get other optional parameters
    limit = params.get("top_k")
    if not isinstance(limit, int):
        limit = 10

    dataset_ids = params.get("datasets")
    prompt_file = params.get("system_prompt_path", "direct_answer.txt")

    # Execute search
    output = await search(
        query_text=query_text,
        query_type=recall,
        datasets=dataset_ids,
        user=current_user,
        system_prompt_path=prompt_file,
        top_k=limit,
    )
    return output


async def _process_memorize(params: dict, current_user) -> str:
    """Process memorize request."""
    input_text = params.get("text")

    # If there is input text, add data first
    if input_text:
        await add(data=input_text, user=current_user)

    await memorize(
        user=current_user,
        enable_content_routing=False,
    )

    # Return result message
    msg = (
        "Text successfully converted into knowledge graph."
        if input_text
        else "Knowledge graph successfully updated with new information."
    )
    return msg


async def _process_prune(params: dict, current_user) -> str:
    """Process prune request.

    Uses prune.all() to perform complete cleanup, ensuring data consistency.
    """
    del params, current_user  # 未使用
    await prune.all()
    return "Memory has been pruned successfully."


# Function handler registry
_HANDLER_REGISTRY: dict[str, DispatchHandler] = {
    "search": _process_search,
    "memorize": _process_memorize,
    "prune": _process_prune,
}


async def dispatch_function(tool_call: ToolCall | dict) -> Any:
    """
    Dispatch tool call to corresponding Mflow function.

    Args:
        tool_call: Tool call object or dictionary.

    Returns:
        Function execution result.
    """
    fn_name, arguments = _extract_call_info(tool_call)
    _log.info("Dispatching function call: %s, arguments: %s", fn_name, arguments)

    user = await get_seed_user()

    handler = _HANDLER_REGISTRY.get(fn_name)
    if handler is None:
        return f"Error: Unknown function {fn_name}"

    result = await handler(arguments, user)
    return result
