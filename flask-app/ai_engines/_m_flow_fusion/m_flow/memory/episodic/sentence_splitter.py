# m_flow/memory/episodic/sentence_splitter.py
"""
Sentence Splitter for Content Routing

Pure Python implementation with no external dependencies.
Supports both English and Chinese text.

Features:
- Conservative splitting to avoid incorrect sentence breaks
- Language auto-detection (Chinese vs English)
- Handles common abbreviations in English
- Preserves sentence boundaries with punctuation
- Dialog-aware: keeps each speaker's utterance as one unit
"""

import re
from typing import List, Tuple, Union

from m_flow.shared.enums import ContentType


# Known non-dialog prefixes that look like "Label: content"
_NON_DIALOG_PREFIXES = frozenset(
    [
        # Code/documentation labels
        "note",
        "warning",
        "error",
        "todo",
        "fixme",
        "hack",
        "xxx",
        "tip",
        "hint",
        "example",
        "usage",
        "syntax",
        "output",
        "input",
        "step",
        "result",
        "conclusion",
        "introduction",
        "method",
        "abstract",
        "summary",
        "description",
        "definition",
        "explanation",
        "answer",
        "question",
        # Config/data keys
        "key",
        "value",
        "name",
        "type",
        "id",
        "url",
        "path",
        "file",
        "host",
        "port",
        "database",
        "server",
        "client",
        "user",
        "password",
        "config",
        "setting",
        "version",
        "date",
        "time",
        "status",
        "state",
        "mode",
        "level",
        "priority",
        "category",
        "tag",
        "label",
        "title",
        "author",
        "source",
        "target",
        "from",
        "to",
        # Programming/API docs
        "returns",
        "return",
        "param",
        "params",
        "args",
        "kwargs",
        "raises",
        "yields",
        # Programming languages and tech terms (often used as "Python: description")
        "python",
        "java",
        "javascript",
        "typescript",
        "rust",
        "go",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "perl",
        "bash",
        "shell",
        "sql",
        "html",
        "css",
        "react",
        "vue",
        "angular",
        "node",
        "django",
        "flask",
        "spring",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "linux",
        "windows",
        "macos",
        "android",
        "ios",
    ]
)

# Dialog line pattern - stricter matching for conversation format
# Requires: [timestamp] SpeakerName: message (with proper name capitalization)
_DIALOG_WITH_TIMESTAMP = re.compile(
    r"^\s*"  # Optional leading whitespace
    r"\[.+?\]\s*"  # Required timestamp in brackets
    r"[A-Z][a-zA-Z\'\-]*"  # Speaker name (capitalized, letters only)
    r"(?:\s+[A-Z][a-zA-Z\'\-]*)*"  # Optional additional name parts
    r"\s*:\s*"  # Colon separator
    r".{10,}",  # Message content (at least 10 chars)
    re.MULTILINE,
)

# Simple dialog: "SpeakerName: message" without timestamp
_DIALOG_SIMPLE = re.compile(
    r"^\s*"  # Optional leading whitespace
    r"[A-Z][a-zA-Z\'\-]{1,15}"  # Speaker name (capitalized, 2-16 chars)
    r"\s*:\s*"  # Colon separator
    r".{10,}",  # Message content (at least 10 chars)
    re.MULTILINE,
)


def _is_dialog_line(line: str) -> bool:
    """Check if a line looks like a dialog utterance start."""
    # Check timestamp format first
    if _DIALOG_WITH_TIMESTAMP.match(line):
        return True
    # Check simple format
    if _DIALOG_SIMPLE.match(line):
        # Verify it's not a known non-dialog prefix
        match = re.match(r"^\s*([A-Z][a-zA-Z\'\-]{1,15})\s*:", line)
        if match and match.group(1).lower() not in _NON_DIALOG_PREFIXES:
            return True
    return False


def _split_dialog(text: str) -> List[str]:
    """
    Split dialog text by speaker utterances.

    Each speaker's complete utterance (even if containing multiple sentences)
    is kept as one unit to preserve speaker attribution.

    Args:
        text: Dialog text

    Returns:
        List of utterances (one per speaker turn)
    """
    lines = text.split("\n")
    utterances = []
    current_utterance = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line starts a new speaker's turn
        if _is_dialog_line(stripped):
            # Save previous utterance if exists
            if current_utterance:
                utterances.append(" ".join(current_utterance))
            current_utterance = [stripped]
        else:
            # Continuation of current speaker's utterance
            # (e.g., image descriptions, multi-line messages)
            if current_utterance:
                current_utterance.append(stripped)
            else:
                # Orphan line without speaker, treat as standalone
                utterances.append(stripped)

    # Don't forget the last utterance
    if current_utterance:
        utterances.append(" ".join(current_utterance))

    return utterances


def smart_split_sentences(
    text: str,
    content_type: Union[ContentType, str] = ContentType.TEXT,
) -> List[str]:
    """
    Smart sentence splitting based on explicit content type declaration.

    Args:
        text: Original text to split
        content_type: Explicit content type declaration
            - ContentType.TEXT (default): Split by sentence boundaries
            - ContentType.DIALOG: Split by speaker utterances, keeping each
              speaker's turn as one unit to preserve attribution

    Returns:
        List of sentences/utterances

    Examples:
        >>> smart_split_sentences("Hello world. This is a test.")
        ['Hello world.', 'This is a test.']

        >>> smart_split_sentences("你好世界。这是测试。")
        ['你好世界。', '这是测试。']

        >>> smart_split_sentences(
        ...     "[10:00] Alice: Hi! How are you?\\n[10:01] Bob: I'm good!",
        ...     content_type=ContentType.DIALOG
        ... )
        ['[10:00] Alice: Hi! How are you?', "[10:01] Bob: I'm good!"]

    Note:
        When enable_content_routing=True (default), content_type must be
        explicitly declared in ingest()/memorize() calls.
    """
    if not text or not text.strip():
        return []

    # DIALOG mode: split by speaker utterances
    if content_type == ContentType.DIALOG or content_type == "dialog":
        utterances = _split_dialog(text)
        return [u.strip() for u in utterances if u.strip()]

    # TEXT mode (default): language-based sentence splitting
    chinese_ratio = _chinese_char_ratio(text)

    if chinese_ratio > 0.3:
        sentences = _split_chinese(text)
    else:
        sentences = _split_english(text)

    return [s.strip() for s in sentences if s.strip()]


def _chinese_char_ratio(text: str) -> float:
    """
    Calculate the ratio of Chinese characters in text.

    Args:
        text: Input text

    Returns:
        Ratio of Chinese characters (0.0 to 1.0)
    """
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    # Count non-whitespace characters
    total_chars = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    return chinese_chars / total_chars if total_chars > 0 else 0


def _split_chinese(text: str) -> List[str]:
    """
    Split Chinese text into sentences.

    Chinese sentence delimiters: 。！？；…

    Args:
        text: Chinese text

    Returns:
        List of sentences
    """
    # Chinese sentence-ending punctuation
    pattern = r"([。！？；…]+)"
    parts = re.split(pattern, text)

    sentences = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and re.match(pattern, parts[i + 1]):
            # Append punctuation to the sentence
            sentences.append(parts[i] + parts[i + 1])
            i += 2
        else:
            if parts[i].strip():
                sentences.append(parts[i])
            i += 1

    return sentences


# Common English abbreviations that shouldn't end a sentence
_ABBREVIATIONS = frozenset(
    [
        "Mr.",
        "Mrs.",
        "Ms.",
        "Dr.",
        "Prof.",
        "Jr.",
        "Sr.",
        "Inc.",
        "Ltd.",
        "Co.",
        "Corp.",
        "vs.",
        "etc.",
        "e.g.",
        "i.e.",
        "Fig.",
        "fig.",
        "No.",
        "no.",
        "Vol.",
        "vol.",
        "pp.",
        "p.",
        "Jan.",
        "Feb.",
        "Mar.",
        "Apr.",
        "Jun.",
        "Jul.",
        "Aug.",
        "Sep.",
        "Sept.",
        "Oct.",
        "Nov.",
        "Dec.",
        "Mon.",
        "Tue.",
        "Wed.",
        "Thu.",
        "Fri.",
        "Sat.",
        "Sun.",
        "St.",
        "Ave.",
        "Rd.",
        "Blvd.",
        "Mt.",
        "Ft.",
        "U.S.",
        "U.K.",
        "U.N.",
        "E.U.",
        "a.m.",
        "p.m.",
        "A.M.",
        "P.M.",
    ]
)


def _split_english(text: str) -> List[str]:
    """
    Split English text into sentences.

    Conservative strategy: only split at clear sentence boundaries.
    Handles common abbreviations to avoid incorrect splits.

    Args:
        text: English text

    Returns:
        List of sentences
    """
    # Protect abbreviations by replacing with placeholders
    protected_text = text
    placeholders = {}

    for i, abbr in enumerate(_ABBREVIATIONS):
        placeholder = f"__ABBR_{i}__"
        if abbr in protected_text:
            placeholders[placeholder] = abbr
            protected_text = protected_text.replace(abbr, placeholder)

    # Also protect common patterns like "1.2" or "3.14"
    # Pattern: digit + period + digit
    number_pattern = r"(\d+)\.(\d+)"
    protected_text = re.sub(number_pattern, r"\1__DOT__\2", protected_text)

    # Split at sentence boundaries:
    # Period/exclamation/question mark followed by whitespace,
    # then uppercase letter, quote, or non-ASCII character (for mixed content)
    # Also handle cases where sentence ends with quote after punctuation
    pattern = r'(?<=[.!?])\s+(?=[A-Z"\'\u4e00-\u9fff])|(?<=[.!?]["\'"])\s+(?=[A-Z\u4e00-\u9fff])'
    sentences = re.split(pattern, protected_text)

    # Restore abbreviations and numbers
    restored = []
    for sent in sentences:
        # Restore abbreviations
        for placeholder, abbr in placeholders.items():
            sent = sent.replace(placeholder, abbr)
        # Restore decimal numbers
        sent = sent.replace("__DOT__", ".")
        restored.append(sent)

    return restored


def split_with_positions(
    text: str,
    content_type: Union[ContentType, str] = ContentType.TEXT,
) -> List[Tuple[str, int, int]]:
    """
    Split text into sentences and return position information.

    Useful for tracing sentences back to their original positions in text.

    Args:
        text: Original text
        content_type: Content type declaration (TEXT or DIALOG)

    Returns:
        List of (sentence, start_pos, end_pos) tuples
    """
    sentences = smart_split_sentences(text, content_type=content_type)
    result = []

    current_pos = 0
    for sent in sentences:
        start = text.find(sent, current_pos)
        if start == -1:
            start = current_pos
        end = start + len(sent)
        result.append((sent, start, end))
        current_pos = end

    return result


def count_sentences(
    text: str,
    content_type: Union[ContentType, str] = ContentType.TEXT,
) -> int:
    """
    Count the number of sentences in text.

    Args:
        text: Input text
        content_type: Content type declaration (TEXT or DIALOG)

    Returns:
        Number of sentences
    """
    return len(smart_split_sentences(text, content_type=content_type))


def is_single_sentence(
    text: str,
    content_type: Union[ContentType, str] = ContentType.TEXT,
) -> bool:
    """
    Check if text contains only a single sentence.

    Useful for short-circuit logic in content routing.

    Args:
        text: Input text
        content_type: Content type declaration (TEXT or DIALOG)

    Returns:
        True if text is a single sentence
    """
    return count_sentences(text, content_type=content_type) <= 1
