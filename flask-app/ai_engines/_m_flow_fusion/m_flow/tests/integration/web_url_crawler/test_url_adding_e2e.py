"""
End-to-end tests for URL adding and web content processing in M-flow.

These integration tests verify the complete workflow of:
1. Fetching web content from URLs
2. Storing HTML files correctly
3. Processing content with various loaders
4. Testing incremental vs full loading modes
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import m_flow
from m_flow.ingestion.pipeline_tasks import save_data_item_to_storage
from m_flow.shared.files.utils.get_data_file_path import get_data_file_path
from m_flow.shared.loaders.external.beautiful_soup_loader import BeautifulSoupLoader
from m_flow.shared.loaders.LoaderEngine import LoaderEngine

if TYPE_CHECKING:
    pass

# Test constants
SAMPLE_URL = "http://example.com/"
HTML_FILE_EXTENSION = ".html"
TEXT_FILE_EXTENSION = ".txt"


# ============================================================================
# Helper functions
# ============================================================================


async def reset_mflow_state() -> None:
    """Clear all M-flow data and system state for clean test isolation."""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)


def create_extraction_rules() -> dict:
    """Build standard extraction rules for HTML parsing tests."""
    return {
        "title": {"selector": "title"},
        "headings": {"selector": "h1, h2, h3", "all": True},
        "links": {"selector": "a", "attr": "href", "all": True},
        "paragraphs": {"selector": "p", "all": True},
    }


def validate_saved_file(file_path: str, expected_extension: str) -> Path:
    """Verify file exists, has content, and correct extension."""
    assert file_path.endswith(expected_extension), f"Expected extension {expected_extension}, got {file_path}"

    resolved_path = Path(file_path)
    assert resolved_path.exists(), f"File not found: {file_path}"

    file_size = resolved_path.stat().st_size
    assert file_size > 0, f"File is empty: {file_path}"

    return resolved_path


# ============================================================================
# Core URL storage tests
# ============================================================================


class TestUrlStorageBasics:
    """Tests for basic URL-to-file storage functionality."""

    @pytest.mark.asyncio
    async def test_url_stored_as_html_file(self) -> None:
        """Verify URL content is saved with .html extension."""
        await reset_mflow_state()

        original_path = await save_data_item_to_storage(SAMPLE_URL)
        resolved_path = get_data_file_path(original_path)

        validate_saved_file(resolved_path, HTML_FILE_EXTENSION)


# ============================================================================
# HTML validation tests
# ============================================================================


_skip_when_tavily_active = pytest.mark.skipif(
    os.getenv("TAVILY_API_KEY") is not None,
    reason="Tavily API handles parsing internally and returns text",
)


class TestHtmlValidation:
    """Tests for validating stored HTML content structure."""

    @_skip_when_tavily_active
    @pytest.mark.asyncio
    async def test_stored_html_contains_valid_structure(self) -> None:
        """Verify saved HTML is parseable and has expected elements."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("BeautifulSoup (bs4) not installed")

        await reset_mflow_state()

        saved_path = await save_data_item_to_storage(SAMPLE_URL)
        full_path = get_data_file_path(saved_path)
        html_content = Path(full_path).read_text(encoding="utf-8")

        parsed = BeautifulSoup(html_content, "html.parser")

        # Verify parseable
        assert parsed.find() is not None, "HTML should be parseable"

        # Check for common HTML structure elements
        structural_elements = ["html", "head", "body", "div", "p"]
        found_elements = [parsed.find(tag) for tag in structural_elements]
        assert any(found_elements), f"Expected at least one of: {structural_elements}"


# ============================================================================
# URL add operation tests
# ============================================================================


_skip_no_tavily_key = pytest.mark.skipif(
    os.getenv("TAVILY_API_KEY") is None,
    reason="需要 TAVILY_API_KEY 环境变量",
)


class TestUrlAddOperations:
    """Tests for the m_flow.add() URL ingestion operations."""

    @pytest.mark.asyncio
    async def test_basic_url_add(self) -> None:
        """Verify basic URL can be added without errors."""
        await reset_mflow_state()
        await m_flow.add(SAMPLE_URL)

    @_skip_no_tavily_key
    @pytest.mark.asyncio
    async def test_url_add_with_tavily_api(self) -> None:
        """Verify URL add works when TAVILY_API_KEY is configured."""

        await reset_mflow_state()
        await m_flow.add(SAMPLE_URL)

    @pytest.mark.asyncio
    async def test_url_add_without_incremental_mode(self) -> None:
        """Verify URL add works with incremental loading disabled."""
        await reset_mflow_state()
        await m_flow.add(SAMPLE_URL, incremental_loading=False)

    @pytest.mark.asyncio
    async def test_url_add_with_incremental_mode(self) -> None:
        """Verify URL add works with incremental loading enabled."""
        await reset_mflow_state()
        await m_flow.add(SAMPLE_URL, incremental_loading=True)


# ============================================================================
# Loader preference tests
# ============================================================================


class TestLoaderPreferences:
    """Tests for specifying preferred loaders during URL processing."""

    @pytest.mark.asyncio
    async def test_specify_loader_as_string_list(self) -> None:
        """Verify loader can be specified using string identifiers."""
        await reset_mflow_state()
        await m_flow.add(SAMPLE_URL, preferred_loaders=["beautiful_soup_loader"])

    @pytest.mark.asyncio
    async def test_add_with_extraction_rules_config(self) -> None:
        """Verify URL add accepts loader with extraction rules."""
        await reset_mflow_state()

        rules = create_extraction_rules()
        loader_config = {"beautiful_soup_loader": {"extraction_rules": rules}}

        await m_flow.add(SAMPLE_URL, preferred_loaders=loader_config)


# ============================================================================
# LoaderEngine behavior tests
# ============================================================================


class TestLoaderEngineSelection:
    """Tests for LoaderEngine's loader selection logic."""

    @pytest.mark.asyncio
    async def test_no_loader_when_not_registered(self) -> None:
        """Verify LoaderEngine returns None when no matching loader exists."""
        await reset_mflow_state()

        saved = await save_data_item_to_storage(SAMPLE_URL)
        file_path = get_data_file_path(saved)
        validate_saved_file(file_path, HTML_FILE_EXTENSION)

        engine = LoaderEngine()
        rules = create_extraction_rules()
        loader_prefs = {"beautiful_soup_loader": {"extraction_rules": rules}}

        selected = engine.get_loader(file_path, preferred_loaders=loader_prefs)
        assert selected is None, "Expected no loader when not registered"

    @pytest.mark.asyncio
    async def test_registered_loader_is_selected(self) -> None:
        """Verify registered loader is selected when preferences match."""
        await reset_mflow_state()

        saved = await save_data_item_to_storage(SAMPLE_URL)
        file_path = get_data_file_path(saved)
        validate_saved_file(file_path, HTML_FILE_EXTENSION)

        engine = LoaderEngine()
        bs_loader = BeautifulSoupLoader()
        engine.register_loader(bs_loader)

        rules = create_extraction_rules()
        prefs = {"beautiful_soup_loader": {"extraction_rules": rules}}

        selected = engine.get_loader(file_path, preferred_loaders=prefs)
        assert selected is bs_loader, "Expected BeautifulSoupLoader to be selected"


# ============================================================================
# File loading tests
# ============================================================================


class TestBeautifulSoupLoaderOperations:
    """Tests for BeautifulSoupLoader file processing."""

    @pytest.mark.asyncio
    async def test_loader_with_empty_config(self) -> None:
        """Verify loader works with minimal configuration."""
        await reset_mflow_state()

        saved = await save_data_item_to_storage(SAMPLE_URL)
        file_path = get_data_file_path(saved)
        validate_saved_file(file_path, HTML_FILE_EXTENSION)

        engine = LoaderEngine()
        engine.register_loader(BeautifulSoupLoader())

        # Test with empty config
        await engine.load_file(file_path, preferred_loaders={"beautiful_soup_loader": {}})

        # Test with extraction rules
        rules = create_extraction_rules()
        await engine.load_file(file_path, preferred_loaders={"beautiful_soup_loader": {"extraction_rules": rules}})

    @pytest.mark.asyncio
    async def test_loader_with_full_extraction_rules(self) -> None:
        """Verify loader processes file with complete extraction rules."""
        await reset_mflow_state()

        saved = await save_data_item_to_storage(SAMPLE_URL)
        file_path = get_data_file_path(saved)
        validate_saved_file(file_path, HTML_FILE_EXTENSION)

        engine = LoaderEngine()
        engine.register_loader(BeautifulSoupLoader())

        rules = create_extraction_rules()
        prefs = {"beautiful_soup_loader": {"extraction_rules": rules}}

        await engine.load_file(file_path, preferred_loaders=prefs)

    @pytest.mark.asyncio
    async def test_complete_html_to_text_conversion(self) -> None:
        """Verify HTML file is correctly converted to text file."""
        await reset_mflow_state()

        # Save original HTML
        saved = await save_data_item_to_storage(SAMPLE_URL)
        html_path = get_data_file_path(saved)
        html_file = validate_saved_file(html_path, HTML_FILE_EXTENSION)

        # Set up loader engine
        engine = LoaderEngine()
        bs_loader = BeautifulSoupLoader()
        engine.register_loader(bs_loader)

        rules = create_extraction_rules()
        prefs = {"beautiful_soup_loader": {"extraction_rules": rules}}

        # Verify correct loader selection
        selected = engine.get_loader(html_path, preferred_loaders=prefs)
        assert selected is bs_loader

        # Process file
        result = await engine.load_file(file_path=html_path, preferred_loaders=prefs)
        txt_path = get_data_file_path(result)

        # Validate output
        txt_file = validate_saved_file(txt_path, TEXT_FILE_EXTENSION)

        # Verify base names match (same document, different format)
        assert html_file.stem == txt_file.stem, f"Base names should match: {html_file.stem} != {txt_file.stem}"
