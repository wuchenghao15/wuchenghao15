"""Content summarization extraction."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.prompts import read_query_prompt
from m_flow.shared.logging_utils import get_logger

_log = get_logger("extract_summary")


async def extract_summary(
    content: str,
    response_model: Type[BaseModel],
) -> BaseModel:
    """Extract summary from content using LLM."""
    prompt = read_query_prompt("semantic_compressor.txt")
    return await LLMService.extract_structured(content, prompt, response_model)
