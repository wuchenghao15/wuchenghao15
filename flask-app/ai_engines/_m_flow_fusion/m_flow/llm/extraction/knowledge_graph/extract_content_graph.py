"""
Knowledge graph content extraction module.

Uses LLM to extract structured graph data from text content.
"""

from __future__ import annotations

import os
from typing import Any, Type

from pydantic import BaseModel

from m_flow.llm.config import get_llm_config
from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.prompts import render_prompt
from m_flow.shared.logging_utils import get_logger

_log = get_logger()

# Internal parameters, not passed to LLM API
_INTERNAL_PARAMS = frozenset({"dataset_name", "datasets", "batch_size", "task_config"})


class SchemaResponseError(Exception):
    """Raised when LLM returns JSON Schema definition instead of actual data."""

    pass


def _detect_schema_in_response(model_output: BaseModel) -> bool:
    """
    Detect if LLM output is a schema definition rather than actual data.

    Some models (e.g., gpt-5-nano) may return schema definitions when using json_schema format.
    """
    data = model_output.model_dump() if hasattr(model_output, "model_dump") else model_output.dict()

    # Top-level contains schema markers
    if "$defs" in data or "properties" in data:
        return True

    # Check if nodes contain schema content
    node_list = data.get("nodes", [])
    if node_list and isinstance(node_list, list):
        sample = node_list[0] if isinstance(node_list[0], dict) else {}

        # Schema type identifiers
        if sample.get("type") in ("object", "string", "array"):
            return True
        if "$ref" in str(sample):
            return True

        # ID contains schema keywords
        node_id = str(sample.get("id", "")).lower()
        if any(kw in node_id for kw in ("properties", "$defs", "json_schema")):
            return True

    # Check if edges reference schema content
    edge_list = data.get("edges", [])
    if edge_list and isinstance(edge_list, list):
        sample = edge_list[0] if isinstance(edge_list[0], dict) else {}
        source_str = str(sample.get("source_node_id", ""))
        if "properties" in source_str or "$defs" in source_str:
            return True

    return False


def _resolve_prompt_path(path_str: str) -> tuple[str, str | None]:
    """Resolve prompt path, return (filename, base_directory)."""
    if os.path.isabs(path_str):
        return os.path.basename(path_str), os.path.dirname(path_str)
    return path_str, None


def _filter_llm_params(params: dict[str, Any]) -> dict[str, Any]:
    """Filter out internal parameters, keep only LLM API parameters."""
    return {k: v for k, v in params.items() if k not in _INTERNAL_PARAMS}


async def extract_content_graph(
    content: str,
    response_model: Type[BaseModel],
    custom_prompt: str | None = None,
    **kwargs,
) -> BaseModel:
    """
    Extract knowledge graph from text content.

    Args:
        content: Text content to extract from.
        response_model: Expected response Pydantic model.
        custom_prompt: Custom system prompt.
        **kwargs: Additional parameters passed to LLM.

    Returns:
        Extracted structured graph data.

    Raises:
        SchemaResponseError: LLM returns schema definition instead of data.
    """
    # Filter internal parameters
    api_params = _filter_llm_params(kwargs)

    # Determine system prompt
    if custom_prompt:
        sys_prompt = custom_prompt
    else:
        cfg = get_llm_config()
        prompt_file, base_dir = _resolve_prompt_path(cfg.graph_prompt_path)
        sys_prompt = render_prompt(prompt_file, {}, base_directory=base_dir)

    # Call LLM for extraction
    graph_output = await LLMService.extract_structured(content, sys_prompt, response_model, **api_params)

    # Verify output is not a schema definition
    if _detect_schema_in_response(graph_output):
        cfg = get_llm_config()
        msg = (
            f"[extract_content_graph] Model ({cfg.llm_model}) returned JSON Schema definition instead of graph data.\n"
            f"Possible causes:\n"
            f"  1. Model does not fully support json_schema response format\n"
            f"  2. Model misinterpreted schema as expected output\n"
            f"Solutions:\n"
            f"  - Set LLM_INSTRUCTOR_MODE=json_mode in .env\n"
            f"  - Or use a different model (e.g., gpt-4o-mini, gpt-4o)\n"
            f"Response preview: {str(graph_output)[:300]}..."
        )
        _log.error(msg)
        raise SchemaResponseError(msg)

    return graph_output
