"""Content category extraction."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.prompts import read_query_prompt


async def extract_categories(
    content: str,
    response_model: Type[BaseModel],
) -> BaseModel:
    """Extract categories from content using LLM."""
    prompt = read_query_prompt("content_classifier.txt")
    return await LLMService.extract_structured(content, prompt, response_model)
