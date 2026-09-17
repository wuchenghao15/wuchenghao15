"""M-Flow tokenizer abstraction layer.

Provides the foundational contract that every tokenizer backend must satisfy
in order to be plugged into the M-Flow pipeline.  The design deliberately
relies on :class:`typing.Protocol` so concrete implementations need *not*
inherit from this class — structural subtyping is sufficient.
"""

from __future__ import annotations

import sys
from abc import abstractmethod
from typing import Any, List, Protocol, runtime_checkable

if sys.version_info >= (3, 11):
    from typing import Self  # noqa: F401 — re-exported for downstream convenience
else:
    from typing_extensions import Self  # noqa: F401


@runtime_checkable
class TokenizerInterface(Protocol):
    """Structural protocol every M-Flow tokenizer must conform to.

    Three capabilities are required:

    * **tokenise** — split raw text into a sequence of token objects.
    * **measure** — report how many tokens a piece of text would produce.
    * **reverse-map** — convert a single integer token id back to its
      surface string.

    Concrete backends (tiktoken, SentencePiece, vendor-specific SDKs, …)
    implement these methods; the rest of M-Flow only depends on this
    protocol so backends can be swapped transparently.
    """

    __slots__ = ()

    @abstractmethod
    def extract_tokens(self, text: str) -> List[Any]:
        """Split *text* into its constituent token objects.

        Parameters
        ----------
        text:
            Arbitrary UTF-8 string to be tokenised.

        Returns
        -------
        List[Any]
            Ordered sequence of tokens whose concrete type is
            backend-specific (integers, bytes, custom objects …).
        """
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Return the number of tokens that *text* encodes to.

        Parameters
        ----------
        text:
            UTF-8 string to measure.

        Returns
        -------
        int
            Non-negative token count.
        """
        ...

    @abstractmethod
    def decode_single_token(self, token: int) -> str:
        """Map a single integer token id back to its surface string.

        Parameters
        ----------
        token:
            Numeric identifier previously produced by the same backend.

        Returns
        -------
        str
            The decoded text fragment corresponding to *token*.
        """
        ...
