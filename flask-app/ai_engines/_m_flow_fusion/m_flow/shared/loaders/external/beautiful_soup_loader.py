"""
HTML content extraction using BeautifulSoup.

Provides a loader implementation for parsing HTML documents and
extracting structured text content using CSS selectors or XPath.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from bs4 import BeautifulSoup

from m_flow.shared.loaders.LoaderInterface import LoaderInterface
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

# Supported file types for this loader
_HTML_EXTENSIONS = frozenset(["html", "htm"])
_HTML_MIME_TYPES = frozenset(["text/html", "text/plain"])


@dataclass(frozen=False)
class ExtractionRule:
    """
    Specification for extracting content from HTML elements.

    At least one of `selector` or `xpath` must be provided.

    Attributes:
        selector: CSS selector string.
        xpath: XPath expression (requires lxml).
        attr: Attribute name to extract instead of text content.
        all: Whether to match all elements or just the first.
        join_with: Separator for joining multiple matches.
    """

    selector: Optional[str] = None
    xpath: Optional[str] = None
    attr: Optional[str] = None
    all: bool = False
    join_with: str = " "


def _build_default_rules() -> dict[str, dict[str, Any]]:
    """
    Construct the default extraction rules dictionary.

    Returns comprehensive selectors for common HTML semantic elements.
    """
    rules: dict[str, dict[str, Any]] = {}

    # Document metadata
    rules["title"] = {"selector": "title"}
    rules["meta_description"] = {
        "selector": "meta[name='description']",
        "attr": "content",
    }
    rules["meta_keywords"] = {
        "selector": "meta[name='keywords']",
        "attr": "content",
    }

    # Open Graph
    rules["og_title"] = {
        "selector": "meta[property='og:title']",
        "attr": "content",
    }
    rules["og_description"] = {
        "selector": "meta[property='og:description']",
        "attr": "content",
    }

    # Semantic content containers
    for tag in ("article", "main", "section"):
        rules[tag] = {"selector": tag, "all": True, "join_with": "\n\n"}

    # Headings h1-h6
    for level in range(1, 7):
        rules[f"h{level}"] = {"selector": f"h{level}", "all": True, "join_with": "\n"}

    # Text blocks
    rules["paragraphs"] = {"selector": "p", "all": True, "join_with": "\n\n"}
    rules["blockquotes"] = {"selector": "blockquote", "all": True, "join_with": "\n\n"}
    rules["preformatted"] = {"selector": "pre", "all": True, "join_with": "\n\n"}
    rules["code_blocks"] = {"selector": "code", "all": True, "join_with": "\n"}

    # Lists
    for list_sel in ("ol", "ul", "li", "dl"):
        rules[list_sel] = {"selector": list_sel, "all": True, "join_with": "\n"}

    # Tables
    rules["tables"] = {"selector": "table", "all": True, "join_with": "\n\n"}
    rules["captions"] = {"selector": "caption", "all": True, "join_with": "\n"}

    # Media descriptions
    rules["figures"] = {"selector": "figure", "all": True, "join_with": "\n\n"}
    rules["figcaptions"] = {"selector": "figcaption", "all": True, "join_with": "\n"}
    rules["img_alts"] = {"selector": "img", "attr": "alt", "all": True, "join_with": " "}

    # Links and emphasis
    rules["links"] = {"selector": "a", "all": True, "join_with": " "}
    for em_tag in ("strong", "em", "mark"):
        rules[em_tag] = {"selector": em_tag, "all": True, "join_with": " "}

    # Temporal and data elements
    rules["time_elements"] = {"selector": "time", "all": True, "join_with": " "}
    rules["data_elements"] = {"selector": "data", "all": True, "join_with": " "}

    # Structural
    rules["asides"] = {"selector": "aside", "all": True, "join_with": "\n\n"}
    rules["details"] = {"selector": "details", "all": True, "join_with": "\n"}
    rules["summary"] = {"selector": "summary", "all": True, "join_with": "\n"}
    rules["nav"] = {"selector": "nav", "all": True, "join_with": "\n"}
    rules["footer"] = {"selector": "footer", "all": True, "join_with": "\n"}

    # Common content divs
    rules["content_divs"] = {
        "selector": "div[role='main'], div[role='article'], div.content, div#content",
        "all": True,
        "join_with": "\n\n",
    }

    return rules


def _parse_rule(raw: str | dict[str, Any]) -> ExtractionRule:
    """
    Convert a raw rule specification to an ExtractionRule.

    Args:
        raw: Either a CSS selector string or a dict with rule parameters.

    Returns:
        Normalized ExtractionRule instance.

    Raises:
        ValueError: If the rule format is invalid.
    """
    if isinstance(raw, str):
        return ExtractionRule(selector=raw)

    if not isinstance(raw, dict):
        raise ValueError(f"Rule must be str or dict, got {type(raw).__name__}")

    return ExtractionRule(
        selector=raw.get("selector"),
        xpath=raw.get("xpath"),
        attr=raw.get("attr"),
        all=bool(raw.get("all", False)),
        join_with=raw.get("join_with", " "),
    )


def _extract_with_bs4(soup: BeautifulSoup, rule: ExtractionRule) -> str:
    """
    Extract text from parsed HTML using a CSS selector.

    Args:
        soup: Parsed BeautifulSoup document.
        rule: Extraction rule with selector and options.

    Returns:
        Extracted and joined text content.
    """
    if not rule.selector:
        return ""

    if rule.all:
        elements = soup.select(rule.selector)
        pieces: list[str] = []
        for el in elements:
            if rule.attr:
                val = el.get(rule.attr)
                if val:
                    pieces.append(str(val).strip())
            else:
                text = el.get_text(strip=True)
                if text:
                    pieces.append(text)
        return rule.join_with.join(pieces)

    # Single element extraction
    el = soup.select_one(rule.selector)
    if el is None:
        return ""
    if rule.attr:
        return str(el.get(rule.attr, "")).strip()
    return el.get_text(strip=True)


def _extract_with_xpath(html_bytes: bytes, rule: ExtractionRule) -> str:
    """
    Extract text using XPath (requires lxml).

    Args:
        html_bytes: Raw HTML bytes.
        rule: Extraction rule with xpath expression.

    Returns:
        Extracted and joined text content.

    Raises:
        RuntimeError: If lxml is not installed.
    """
    try:
        from lxml import html as lxml_html
    except ImportError as e:
        raise RuntimeError("XPath extraction requires lxml. Install with: pip install lxml") from e

    doc = lxml_html.fromstring(html_bytes)
    nodes = doc.xpath(rule.xpath)

    texts: list[str] = []
    for node in nodes:
        if hasattr(node, "text_content"):
            content = node.text_content()
        else:
            content = str(node)
        content = content.strip()
        if content:
            texts.append(content)

    return rule.join_with.join(texts)


class BeautifulSoupLoader(LoaderInterface):
    """
    HTML document loader using BeautifulSoup for content extraction.

    Parses HTML files and extracts text content based on configurable
    CSS selector or XPath rules. Falls back to plain text if no HTML
    structure is detected.
    """

    @property
    def supported_extensions(self) -> list[str]:
        """File extensions this loader can handle."""
        return list(_HTML_EXTENSIONS)

    @property
    def supported_mime_types(self) -> list[str]:
        """MIME types this loader can handle."""
        return list(_HTML_MIME_TYPES)

    @property
    def loader_name(self) -> str:
        """Unique identifier for this loader."""
        return "beautiful_soup_loader"

    def can_handle(self, extension: str, mime_type: str) -> bool:
        """
        Check if this loader can process the given file type.

        Args:
            extension: File extension (without dot).
            mime_type: MIME type string.

        Returns:
            True if this loader supports the file type.
        """
        ext_ok = extension.lower() in _HTML_EXTENSIONS
        mime_ok = mime_type.lower() in _HTML_MIME_TYPES
        return ext_ok and mime_ok

    def _get_default_extraction_rules(self) -> dict[str, dict[str, Any]]:
        """Return the default extraction rules dictionary."""
        return _build_default_rules()

    async def load(
        self,
        file_path: str,
        extraction_rules: dict[str, Any] | None = None,
        join_all_matches: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Load and extract content from an HTML file.

        Args:
            file_path: Path to the HTML file.
            extraction_rules: Custom extraction rules (default: comprehensive set).
            join_all_matches: Force all rules to extract all matches.
            **kwargs: Additional arguments (unused).

        Returns:
            Path to the stored extracted text file.
        """
        # Use defaults if no rules provided
        if extraction_rules is None:
            extraction_rules = _build_default_rules()
            _log.info("Using default extraction rules for HTML processing")

        _log.info("Processing HTML file: %s", file_path)

        # Lazy imports to avoid circular dependencies
        from m_flow.shared.files.storage import get_file_storage, get_storage_config
        from m_flow.shared.files.utils.get_file_metadata import get_file_metadata

        # Read file and compute hash
        with open(file_path, "rb") as fp:
            metadata = await get_file_metadata(fp)
            fp.seek(0)
            html_bytes = fp.read()

        content_hash = metadata["content_hash"]
        output_filename = f"text_{content_hash}.txt"

        # Normalize rules
        rules: list[ExtractionRule] = []
        for raw_rule in extraction_rules.values():
            parsed = _parse_rule(raw_rule)
            if join_all_matches:
                parsed.all = True
            rules.append(parsed)

        # Extract content
        extracted_parts: list[str] = []
        soup = BeautifulSoup(html_bytes, "html.parser")

        for rule in rules:
            if rule.xpath:
                text = _extract_with_xpath(html_bytes, rule)
            else:
                text = _extract_with_bs4(soup, rule)

            if text:
                extracted_parts.append(text)

        combined = " ".join(extracted_parts).strip()

        # Fallback: treat as plain text if no HTML structure found
        if not combined and not soup.find():
            _log.warning(
                "No HTML tags in %s, treating as plain text (may be pre-extracted content)",
                file_path,
            )
            combined = html_bytes.decode("utf-8", errors="replace").strip()

        if not combined:
            _log.warning("No content extracted from: %s", file_path)

        # Store extracted content
        storage_cfg = get_storage_config()
        storage = get_file_storage(storage_cfg["data_root_directory"])
        stored_path = await storage.store(output_filename, combined)

        _log.info("Extracted %d characters from HTML", len(combined))
        return stored_path
