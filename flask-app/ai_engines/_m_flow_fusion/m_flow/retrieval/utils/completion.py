"""
LLM completion utilities for retrieval operations.

Provides helper functions for generating completions and
summaries using the LLM gateway.
"""

from __future__ import annotations

from typing import Any, Optional, Type

from m_flow.llm.LLMGateway import LLMService
from m_flow.llm.prompts import read_query_prompt, render_prompt
from m_flow.knowledge.summarization.summarize_text import compress_text as compress_text


def _build_system_prompt(
    prompt_path: str,
    custom_prompt: Optional[str],
    history: Optional[str],
) -> str:
    """
    Construct the final system prompt.

    Uses custom prompt if provided, otherwise loads from file.
    Prepends conversation history if available.
    """
    base = custom_prompt if custom_prompt else read_query_prompt(prompt_path)

    if history:
        # Prefix history before the task instructions
        return f"{history}\nTASK:{base}"

    return base


async def generate_completion(
    query: str,
    context: str,
    user_prompt_path: str,
    system_prompt_path: str,
    system_prompt: Optional[str] = None,
    conversation_history: Optional[str] = None,
    response_model: Type = str,
) -> Any:
    """
    Generate an LLM completion with context.

    Renders the user prompt with query and context, then calls
    the LLM gateway for structured output generation.

    Args:
        query: User's question.
        context: Retrieved context for answering.
        user_prompt_path: Template path for user prompt.
        system_prompt_path: Template path for system prompt.
        system_prompt: Optional custom system prompt.
        conversation_history: Previous conversation for context.
        response_model: Expected response type.

    Returns:
        LLM-generated response matching response_model.
    """
    # Render user prompt with variables
    prompt_vars = {"question": query, "context": context}
    user_message = render_prompt(user_prompt_path, prompt_vars)

    # Build complete system prompt
    sys_message = _build_system_prompt(
        system_prompt_path,
        system_prompt,
        conversation_history,
    )

    return await LLMService.extract_structured(
        text_input=user_message,
        system_prompt=sys_message,
        response_model=response_model,
    )


async def summarize_text(
    text: str,
    system_prompt_path: str = "search_result_deduplicator.txt",
    system_prompt: Optional[str] = None,
) -> str:
    """
    Summarize text content using LLM.

    Args:
        text: Content to summarize.
        system_prompt_path: Default prompt template path.
        system_prompt: Optional custom summarization prompt.

    Returns:
        Summarized text string.
    """
    sys_message = system_prompt if system_prompt else read_query_prompt(system_prompt_path)

    return await LLMService.extract_structured(
        text_input=text,
        system_prompt=sys_message,
        response_model=str,
    )
