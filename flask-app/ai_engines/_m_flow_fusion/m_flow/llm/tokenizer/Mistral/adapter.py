"""M-Flow tokenizer backend powered by ``mistral_common``.

This module wraps the official Mistral tokenizer library so it conforms to
:class:`~m_flow.llm.tokenizer.tokenizer_interface.TokenizerInterface`.
All heavy imports from ``mistral_common`` are deferred to keep the top-level
import lightweight.
"""

from __future__ import annotations

from typing import Any, List

from ..tokenizer_interface import TokenizerInterface


class MistralTokenizer(TokenizerInterface):
    """Offline tokenizer for Mistral model families.

    Tokenisation is performed entirely on the local machine via the
    ``mistral_common`` package — no network calls are required.  The
    backend encodes text as if it were a single-turn chat completion
    request so the token count matches what the Mistral API would see.

    Attributes
    ----------
    model : str
        Model identifier used to select the correct vocabulary
        (e.g. ``"mistral-tiny"``).
    max_completion_tokens : int
        Downstream hint for maximum generation length.
    """

    __slots__ = ("model", "max_completion_tokens", "_backing_tokenizer")

    def __init__(
        self,
        model: str,
        max_completion_tokens: int = 3072,
    ) -> None:
        self.model: str = model
        self.max_completion_tokens: int = max_completion_tokens

        from mistral_common.tokens.tokenizers.mistral import (
            MistralTokenizer as _MistralBackend,
        )

        self._backing_tokenizer = _MistralBackend.from_model(model)

    # ------------------------------------------------------------------
    # Token extraction
    # ------------------------------------------------------------------

    def extract_tokens(self, text: str) -> List[Any]:
        """Tokenise *text* using the Mistral chat-completion encoding.

        The input is wrapped in a single ``UserMessage`` so the resulting
        token sequence includes any special / role tokens that the model
        expects.

        Parameters
        ----------
        text:
            Raw string to tokenise.

        Returns
        -------
        List[Any]
            Sequence of token objects produced by the Mistral backend.
        """
        from mistral_common.protocol.instruct.messages import UserMessage
        from mistral_common.protocol.instruct.request import ChatCompletionRequest

        chat_payload = ChatCompletionRequest(
            messages=[UserMessage(role="user", content=text)],
            model=self.model,
        )
        tokenized_output = self._backing_tokenizer.encode_chat_completion(chat_payload)
        return tokenized_output.tokens

    # ------------------------------------------------------------------
    # Token counting
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Return the number of tokens *text* would produce.

        Delegates to :meth:`extract_tokens` and measures the result.
        """
        return len(self.extract_tokens(text))

    # ------------------------------------------------------------------
    # Single-token decoding (unsupported)
    # ------------------------------------------------------------------

    def decode_single_token(self, encoding: int) -> str:
        """Not available — the Mistral backend has no per-token decoder.

        Raises
        ------
        NotImplementedError
            Always, because ``mistral_common`` does not expose a
            vocabulary-level decode API.
        """
        raise NotImplementedError(
            "MistralTokenizer does not support single-token decoding; "
            "the mistral_common library lacks a per-id decode method."
        )
