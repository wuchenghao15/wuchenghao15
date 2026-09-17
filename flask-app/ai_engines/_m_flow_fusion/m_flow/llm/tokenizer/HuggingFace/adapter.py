"""
HuggingFace Transformers tokenizer adapter.

Implements TokenizerInterface using the transformers library.
"""

from __future__ import annotations

from typing import Any, List

from ..tokenizer_interface import TokenizerInterface


class HuggingFaceTokenizer(TokenizerInterface):
    """
    Tokenizer using HuggingFace AutoTokenizer.

    Attributes:
        model: HuggingFace model identifier.
        max_completion_tokens: Token limit for generation.
    """

    def __init__(
        self,
        model: str,
        max_completion_tokens: int = 512,
    ) -> None:
        """
        Initialize tokenizer from a pretrained model.

        Args:
            model: HuggingFace model name or path.
            max_completion_tokens: Maximum tokens for outputs.
        """
        self.model = model
        self.max_completion_tokens = max_completion_tokens

        # Lazy import for optional dependency
        from transformers import AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(model)

    def extract_tokens(self, text: str) -> List[Any]:
        """Extract tokens from input text."""
        return self._tokenizer.tokenize(text)

    def count_tokens(self, text: str) -> int:
        """Count number of tokens in text."""
        return len(self._tokenizer.tokenize(text))

    def decode_single_token(self, encoding: int) -> str:
        """
        Decode a single token ID.

        Note: HuggingFace tokenizers don't support single-token decoding.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError("HuggingFace tokenizer does not support single-token decoding")
