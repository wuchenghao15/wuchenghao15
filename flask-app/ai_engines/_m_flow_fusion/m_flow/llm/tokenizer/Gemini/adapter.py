"""M-Flow tokenizer backend for Google Gemini models.

.. deprecated::
    Token counting with Gemini requires a synchronous round-trip to Google's
    REST API for every call, making it impractical for M-Flow workloads that
    need high-throughput token estimation.  Prefer a local tokenizer when
    possible.
"""

from __future__ import annotations

from typing import Any, List, NoReturn

from ..tokenizer_interface import TokenizerInterface


class GeminiTokenizer(TokenizerInterface):
    """Google Gemini tokenizer backend (network-dependent).

    Because the Gemini SDK does not expose an offline tokenizer, every
    :meth:`count_tokens` call hits Google's ``countTokens`` endpoint.
    :meth:`extract_tokens` and :meth:`decode_single_token` are **not
    supported** by this backend.

    Attributes
    ----------
    llm_model : str
        Fully-qualified Gemini model id (e.g. ``"gemini-pro"``).
    max_completion_tokens : int
        Upper bound on output tokens for downstream callers.
    """

    __slots__ = ("llm_model", "max_completion_tokens", "_api_client")

    def __init__(
        self,
        llm_model: str,
        max_completion_tokens: int = 3072,
    ) -> None:
        self.llm_model: str = llm_model
        self.max_completion_tokens: int = max_completion_tokens

        from m_flow.llm.config import get_llm_config

        llm_cfg = get_llm_config()

        from google import genai  # type: ignore[import-untyped]

        self._api_client = genai.Client(api_key=llm_cfg.llm_api_key)

    # ------------------------------------------------------------------
    # TokenizerInterface — unsupported operations
    # ------------------------------------------------------------------

    def extract_tokens(self, text: str) -> List[Any]:  # noqa: D401
        """Not available — Gemini SDK lacks offline tokenisation."""
        raise NotImplementedError(
            "GeminiTokenizer cannot extract individual tokens; the Gemini SDK only supports remote token counting."
        )

    def decode_single_token(self, encoding: int) -> str:  # noqa: D401
        """Not available — Gemini SDK cannot reverse-map token ids."""
        raise NotImplementedError(
            "GeminiTokenizer cannot decode token ids; the Gemini SDK does not expose a vocabulary mapping."
        )

    # ------------------------------------------------------------------
    # TokenizerInterface — supported operations
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Count tokens by delegating to the Gemini ``countTokens`` RPC.

        Parameters
        ----------
        text:
            Raw string whose token length is to be measured.

        Returns
        -------
        int
            Number of tokens as reported by the Gemini API.

        Note
        ----
        This method performs a **synchronous network call**; callers that
        need non-blocking behaviour should run it inside an executor.
        """
        api_result = self._api_client.models.count_tokens(
            model=self.llm_model,
            contents=text,
        )
        return api_result.total_tokens
