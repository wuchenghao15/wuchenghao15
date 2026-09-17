"""
Text Summary Parser
===================

Parse text-format LLM output into structured SectionedSummary.
Handles various output formats with robust fallback logic.
"""

from __future__ import annotations

import re
from typing import List, Optional

import structlog

from m_flow.shared.data_models import Section, SectionedSummary

logger = structlog.get_logger("text_summary_parser")


class TextSummaryParser:
    """Parse text summary into structured sections."""

    # Section patterns (ordered by priority)
    SECTION_PATTERNS = [
        # Pattern 1: 【Title】Content (Chinese brackets - primary format)
        r"【([^】]+)】\s*(.+?)(?=【|$)",
        # Pattern 2: ## Title\nContent (Markdown headers)
        r"^##\s*(.+?)\n(.+?)(?=^##|\Z)",
        # Pattern 3: **Title**: Content (Bold with colon)
        r"\*\*([^*]+)\*\*:\s*(.+?)(?=\*\*|$)",
        # Pattern 4: Title:\nContent (Plain title with colon)
        r"^([A-Z][^:\n]{5,50}):\s*\n(.+?)(?=^[A-Z][^:\n]{5,50}:|\Z)",
        # Pattern 5: - Title: Content (list format)
        r"^-\s*([^:]+):\s*(.+?)(?=^-\s*[^:]+:|\Z)",
    ]

    @classmethod
    def parse(
        cls,
        text: str,
        fallback_title: str = "Content Summary",
    ) -> SectionedSummary:
        """
        Parse text into SectionedSummary.

        Args:
            text: Raw LLM text output
            fallback_title: Title to use if parsing fails

        Returns:
            SectionedSummary with parsed sections
        """
        if not text or not text.strip():
            return SectionedSummary(
                overall_topic=fallback_title or "Content Summary",
                sections=[],
            )

        text = text.strip()

        # Try to extract topic (first line or first sentence)
        topic = cls._extract_topic(text)

        # Try each pattern
        for pattern in cls.SECTION_PATTERNS:
            sections = cls._try_pattern(text, pattern)
            if sections and len(sections) >= 1:
                logger.debug(
                    "Parsed sections using pattern",
                    section_count=len(sections),
                    pattern_preview=pattern[:30],
                )
                return SectionedSummary(
                    overall_topic=topic or fallback_title,
                    sections=sections,
                )

        # Fallback: treat entire text as single section
        logger.warning(
            "No section pattern matched, using fallback",
            text_preview=text[:100],
        )
        # Ensure fallback_title is never None (defensive programming)
        safe_title = fallback_title or "Content Summary"
        return SectionedSummary(
            overall_topic=topic or safe_title,
            sections=[
                Section(
                    title=safe_title,
                    content=text,
                )
            ],
        )

    @classmethod
    def _extract_topic(cls, text: str) -> Optional[str]:
        """Extract overall topic from text."""
        # Try "Topic: ..." format
        topic_match = re.search(r"^(?:Topic|Overall Topic|Summary):\s*(.+?)(?:\n|$)", text, re.I)
        if topic_match:
            return topic_match.group(1).strip()

        # Try first line if it's short and doesn't look like a section header or Episode Name
        first_line = text.split("\n")[0].strip()
        if (
            10 < len(first_line) < 100
            and not first_line.startswith(("【", "-", "*", "#"))
            and not re.match(r"^Episode Name:", first_line, re.I)
        ):
            return first_line

        return None

    @classmethod
    def _try_pattern(cls, text: str, pattern: str) -> List[Section]:
        """Try to match sections with a specific pattern."""
        flags = re.MULTILINE | re.DOTALL
        matches = re.findall(pattern, text, flags)

        if not matches:
            return []

        sections = []
        for match in matches:
            if isinstance(match, tuple) and len(match) >= 2:
                title = match[0].strip()
                content = match[1].strip()

                # Validate: title and content should be non-empty
                # Content must be at least 10 chars to avoid false positives
                if title and content and len(content) > 10:
                    sections.append(Section(title=title, content=content))

        return sections
