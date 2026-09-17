"""
Jaccard similarity-based chunk retriever.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Optional, Set

from m_flow.retrieval.lexical_retriever import LexicalRetriever


class JaccardChunksRetriever(LexicalRetriever):
    """
    Retriever using Jaccard similarity for lexical matching.
    """

    def __init__(
        self,
        top_k: int = 10,
        with_scores: bool = False,
        stop_words: Optional[List[str]] = None,
        multiset_jaccard: bool = False,
    ) -> None:
        """
        Initialize Jaccard retriever.

        Parameters
        ----------
        top_k
            Number of results to return.
        with_scores
            Whether to include similarity scores.
        stop_words
            Tokens to filter out.
        multiset_jaccard
            Use frequency-aware Jaccard if True.
        """
        self._stop_words: Set[str] = {t.lower() for t in stop_words} if stop_words else set()
        self._multiset = multiset_jaccard

        super().__init__(
            tokenizer=self._tokenize,
            scorer=self._score,
            top_k=top_k,
            with_scores=with_scores,
        )

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercased words, filtering stopwords."""
        tokens = re.findall(r"\w+", text.lower())
        return [t for t in tokens if t not in self._stop_words]

    def _score(self, query_tokens: List[str], chunk_tokens: List[str]) -> float:
        """Compute Jaccard similarity between token sets."""
        if self._multiset:
            q_cnt, c_cnt = Counter(query_tokens), Counter(chunk_tokens)
            all_keys = set(q_cnt) | set(c_cnt)
            numer = sum(min(q_cnt[k], c_cnt[k]) for k in all_keys)
            denom = sum(max(q_cnt[k], c_cnt[k]) for k in all_keys)
            return numer / denom if denom else 0.0

        q_set, c_set = set(query_tokens), set(chunk_tokens)
        if not q_set or not c_set:
            return 0.0
        return len(q_set & c_set) / len(q_set | c_set)
