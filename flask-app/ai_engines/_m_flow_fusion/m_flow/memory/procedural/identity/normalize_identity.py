# m_flow/memory/procedural/identity/normalize_identity.py
"""
Identity normalization for procedural memory

Normalize Procedure identity to stable canonical_key.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional

from m_flow.shared.tracing import TraceManager
from m_flow.shared.logging_utils import get_logger

logger = get_logger()


@dataclass
class IdentityResult:
    """Identity normalization result"""

    canonical_key: str  # Short, stable, aggregatable
    canonical_title: str  # More readable title
    canonical_search_text: str  # For retrieval
    identity_aliases: List[str] = field(default_factory=list)  # Aliases
    original_key: Optional[str] = None
    normalized: bool = False  # Whether normalization was performed


class IdentityNormalizer:
    """
    Identity normalizer.

    Rules:
    - canonical_key cannot contain: dates, quarters, environments (prod/staging), version numbers (v2)
    - Can contain: system/product name + action core
    """

    # Patterns to remove
    REMOVE_PATTERNS = [
        # Date patterns
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",  # 2024-01-01
        r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",  # 01-01-2024
        r"20\d{2}年?\d{1,2}月?\d{1,2}日?",  # 2024年1月1日
        r"q[1-4]\s*20\d{2}",  # Q1 2024
        r"20\d{2}\s*q[1-4]",  # 2024 Q1
        # Version number patterns
        r"v\d+(\.\d+)*",  # v1, v2.0, v1.2.3
        r"版本\s*\d+",  # 版本1
        r"version\s*\d+",  # version 1
        # Environment patterns
        r"\b(prod|production|staging|dev|development|test|testing|qa|uat)\b",
        r"\b(生产|测试|开发|预发|灰度)\b",
        # Temporary/one-time markers
        r"\b(temp|temporary|tmp|临时)\b",
        r"\b(old|new|旧|新)\b",
    ]

    # Stopwords
    STOPWORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "over",
        "after",
        "的",
        "了",
        "是",
        "在",
        "有",
        "和",
        "与",
        "或",
        "等",
        "及",
    }

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def normalize(
        self,
        title: str,
        search_text: str = "",
        summary: str = "",
        existing_keys: Optional[List[str]] = None,
    ) -> IdentityResult:
        """
        Normalize identity.

        Args:
            title: Original title
            search_text: Search text
            summary: Summary
            existing_keys: Existing keys (for matching)

        Returns:
            IdentityResult
        """
        original = title

        # 1. Basic cleaning
        cleaned = self._clean_text(title)

        # 2. Remove dates, versions, environments, etc.
        for pattern in self.REMOVE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # 3. Convert to key format
        canonical_key = self._to_key_format(cleaned)

        # 4. Generate canonical_title
        canonical_title = self._to_title_format(cleaned)

        # 5. Generate search_text
        canonical_search_text = self._generate_search_text(canonical_title, search_text, summary)

        # 6. Collect aliases
        aliases = self._collect_aliases(original, canonical_key, existing_keys)

        # 7. Try to match existing key
        if existing_keys:
            matched_key = self._match_existing_key(canonical_key, existing_keys)
            if matched_key:
                canonical_key = matched_key

        result = IdentityResult(
            canonical_key=canonical_key,
            canonical_title=canonical_title,
            canonical_search_text=canonical_search_text,
            identity_aliases=aliases,
            original_key=original if original != canonical_key else None,
            normalized=original != canonical_key,
        )

        # Tracing
        TraceManager.event(
            "procedural.identity.normalized",
            {
                "original": original[:50],
                "canonical_key": canonical_key,
                "aliases_count": len(aliases),
                "normalized": result.normalized,
            },
        )

        return result

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        text = text.strip()
        # Remove extra spaces
        text = re.sub(r"\s+", " ", text)
        return text

    def _to_key_format(self, text: str) -> str:
        """Convert to key format"""
        # Convert to lowercase
        text = text.lower()

        # Remove stopwords
        words = text.split()
        words = [w for w in words if w not in self.STOPWORDS]
        text = " ".join(words)

        # Replace special characters with underscore
        text = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text)

        # Remove consecutive underscores
        text = re.sub(r"_+", "_", text)

        # Remove leading/trailing underscores
        text = text.strip("_")

        # Limit length
        if len(text) > 60:
            text = text[:60].rsplit("_", 1)[0]

        return text or "unknown_procedure"

    def _to_title_format(self, text: str) -> str:
        """Convert to title format"""
        # Capitalize first letter
        words = text.split()
        titled_words = []
        for w in words:
            if w.lower() not in self.STOPWORDS:
                titled_words.append(w.capitalize())
            else:
                titled_words.append(w.lower())

        return " ".join(titled_words) or text

    def _generate_search_text(
        self,
        title: str,
        search_text: str,
        summary: str,
    ) -> str:
        """Generate search text"""
        parts = []

        if title:
            parts.append(title)

        if search_text:
            parts.append(search_text[:100])

        if summary:
            # Take first 100 characters of summary
            parts.append(summary[:100])

        combined = " ".join(parts)
        # Deduplicate words
        words = combined.split()
        seen = set()
        unique_words = []
        for w in words:
            w_lower = w.lower()
            if w_lower not in seen and w_lower not in self.STOPWORDS:
                seen.add(w_lower)
                unique_words.append(w)

        return " ".join(unique_words)[:200]

    def _collect_aliases(
        self,
        original: str,
        canonical_key: str,
        existing_keys: Optional[List[str]],
    ) -> List[str]:
        """Collect aliases"""
        aliases = []

        # Original text as alias
        if original and original.lower() != canonical_key:
            aliases.append(original)

        # Extract common variants
        variants = self._generate_variants(canonical_key)
        aliases.extend(variants)

        # Deduplicate
        aliases = list(set(aliases))

        # Limit count
        return aliases[:10]

    def _generate_variants(self, key: str) -> List[str]:
        """Generate common variants of key"""
        variants = []

        # Underscore <-> hyphen
        if "_" in key:
            variants.append(key.replace("_", "-"))
        if "-" in key:
            variants.append(key.replace("-", "_"))

        # CamelCase
        words = key.split("_")
        if len(words) > 1:
            camel = words[0] + "".join(w.capitalize() for w in words[1:])
            variants.append(camel)

        return variants

    def _match_existing_key(
        self,
        candidate: str,
        existing_keys: List[str],
    ) -> Optional[str]:
        """Try to match existing key"""
        candidate_normalized = candidate.lower().replace("-", "_")

        for existing in existing_keys:
            existing_normalized = existing.lower().replace("-", "_")

            # Exact match
            if candidate_normalized == existing_normalized:
                return existing

            # Containment relationship (candidate is substring of existing or vice versa)
            if candidate_normalized in existing_normalized or existing_normalized in candidate_normalized:
                # Return the shorter one
                if len(existing) <= len(candidate):
                    return existing

        return None


# ========== Convenience Functions ==========

_default_normalizer = IdentityNormalizer()


def normalize_identity(
    title: str,
    search_text: str = "",
    summary: str = "",
    existing_keys: Optional[List[str]] = None,
) -> IdentityResult:
    """
    Normalize Procedure identity.

    Args:
        title: Original title
        search_text: Search text
        summary: Summary
        existing_keys: Existing keys (for matching)

    Returns:
        IdentityResult
    """
    return _default_normalizer.normalize(
        title=title,
        search_text=search_text,
        summary=summary,
        existing_keys=existing_keys,
    )
