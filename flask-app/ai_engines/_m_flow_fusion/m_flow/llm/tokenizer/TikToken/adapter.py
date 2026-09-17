"""
TikToken tokenizer adapter for OpenAI models.

Implements the TokenizerInterface using OpenAI's tiktoken library.
"""

from __future__ import annotations

from typing import Any, List, Optional

import tiktoken

from ..tokenizer_interface import TokenizerInterface


class TikTokenTokenizer(TokenizerInterface):
    """
    Tokenizer for OpenAI GPT models using tiktoken.

    Attributes:
        model: Model name for encoding selection.
        max_completion_tokens: Maximum tokens for trimming.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        max_completion_tokens: int = 8191,
    ) -> None:
        """
        Initialize with optional model-specific encoding.

        Args:
            model: OpenAI model name (e.g., "gpt-4").
            max_completion_tokens: Token limit for trimming.
        """
        self.model = model
        self.max_completion_tokens = max_completion_tokens

        if model:
            self._enc = tiktoken.encoding_for_model(model)
        else:
            self._enc = tiktoken.get_encoding("cl100k_base")

    def extract_tokens(self, text: str) -> List[Any]:
        """Return list of token IDs for the input text."""
        return self._enc.encode(text)

    def count_tokens(self, text: str) -> int:
        """Count tokens in the input text."""
        return len(self._enc.encode(text))

    def decode_token_list(self, tokens: List[Any]) -> List[str]:
        """Decode a list of token IDs to strings."""
        if not isinstance(tokens, list):
            tokens = [tokens]
        return [self._enc.decode([t]) for t in tokens]

    def decode_single_token(self, token: int) -> str:
        """Decode a single token ID to its string representation."""
        raw = self._enc.decode_single_token_bytes(token)
        return raw.decode("utf-8", errors="replace")

    def trim_text_to_max_completion_tokens(self, text: str) -> str:
        """
        Trim text to fit within max_completion_tokens.

        Args:
            text: Input text to potentially trim.

        Returns:
            Trimmed text if exceeding limit, otherwise original.
        """
        ids = self._enc.encode(text)

        if len(ids) <= self.max_completion_tokens:
            return text

        trimmed = ids[: self.max_completion_tokens]
        return self._enc.decode(trimmed)
