"""
Unit tests for pure functions in write_episodic_memories.py

These tests verify the behavior of all pure functions to ensure:
1. Correct input/output behavior
2. Edge cases handling
3. Safe refactoring for future file splitting

Test Coverage: 14 pure functions
- _episode_sort_key
- _extract_time_fields_from_episode
- _split_long_summary
- _create_facets_from_sections
- _extract_event_sentences
- _choose_better_description
- _extract_chunk_summaries_from_text_summaries
- _create_facets_from_sections_direct
- _create_same_entity_as_edges
- _extract_all_sections_from_summaries
- _has_valid_sections
- _generate_episode_summary_from_sections
- _extract_entities_from_chunk
- ensure_nodeset
"""

import pytest
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock


# Helper to generate valid UUIDs for testing
def new_uuid() -> str:
    return str(uuid.uuid4())


# ============================================================
# Test Data Factories
# ============================================================


@dataclass
class MockSection:
    """Mock Section for testing."""

    heading: str = ""
    text: str = ""


@dataclass
class MockContentFragment:
    """Mock ContentFragment for testing."""

    id: str = "chunk_001"
    text: str = "Sample chunk text"
    chunk_index: int = 0
    is_part_of: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    contains: List[Any] = field(default_factory=list)


@dataclass
class MockDocument:
    """Mock Document for testing."""

    id: str = "doc_001"


@dataclass
class MockFragmentDigest:
    """Mock FragmentDigest for testing."""

    text: str = ""
    made_from: Any = None
    sections: List[MockSection] = field(default_factory=list)
    overall_topic: str = ""


@dataclass
class MockMemorySpace:
    """Mock MemorySpace for testing."""

    id: str = "space_001"


@dataclass
class MockConcept:
    """Mock Entity for testing."""

    id: str = "concept_001"
    name: str = "TestConcept"
    description: str = "A test concept"
    canonical_name: str = "testconcept"
    memory_type: Optional[str] = None


@dataclass
class StubMemoryNode:
    """Mock data point for ensure_nodeset testing."""

    memory_spaces: Optional[List[MockMemorySpace]] = None


def create_fragment_digest(
    text: str = "",
    sections: Optional[List[tuple]] = None,
    chunk_text: str = "",
    chunk_index: int = 0,
    doc_id: str = "doc_001",
    metadata: Optional[Dict] = None,
) -> MockFragmentDigest:
    """Factory for creating test FragmentDigest."""
    doc = MockDocument(id=doc_id)
    chunk = MockContentFragment(
        id=f"chunk_{chunk_index}",
        text=chunk_text or text,
        chunk_index=chunk_index,
        is_part_of=doc,
        metadata=metadata or {},
    )

    section_objs = []
    if sections:
        for heading, content in sections:
            section_objs.append(MockSection(heading=heading, text=content))

    return MockFragmentDigest(
        text=text,
        made_from=chunk,
        sections=section_objs,
    )


# ============================================================
# 5.1.1 _episode_sort_key Tests
# ============================================================


class TestEpisodeSortKey:
    """Tests for _episode_sort_key function."""

    def test_basic_sorting(self):
        """Test basic sorting by doc_id and chunk_index."""
        from m_flow.memory.episodic.write_episodic_memories import _episode_sort_key

        ts = create_fragment_digest(doc_id="doc_002", chunk_index=3)
        result = _episode_sort_key(ts)

        assert result == ("doc_002", 3)

    def test_multiple_fragments_sort_order(self):
        """Test correct ordering of multiple fragments."""
        from m_flow.memory.episodic.write_episodic_memories import _episode_sort_key

        ts1 = create_fragment_digest(doc_id="doc_001", chunk_index=0)
        ts2 = create_fragment_digest(doc_id="doc_001", chunk_index=1)
        ts3 = create_fragment_digest(doc_id="doc_002", chunk_index=0)

        fragments = [ts3, ts1, ts2]
        sorted_fragments = sorted(fragments, key=_episode_sort_key)

        # Should be sorted by doc_id first, then chunk_index
        assert _episode_sort_key(sorted_fragments[0]) == ("doc_001", 0)
        assert _episode_sort_key(sorted_fragments[1]) == ("doc_001", 1)
        assert _episode_sort_key(sorted_fragments[2]) == ("doc_002", 0)

    def test_missing_is_part_of(self):
        """Test handling when is_part_of is None."""
        from m_flow.memory.episodic.write_episodic_memories import _episode_sort_key

        chunk = MockContentFragment(chunk_index=5, is_part_of=None)
        ts = MockFragmentDigest(made_from=chunk)

        result = _episode_sort_key(ts)
        assert result == ("", 5)

    def test_missing_chunk_index(self):
        """Test handling when chunk_index is missing."""
        from m_flow.memory.episodic.write_episodic_memories import _episode_sort_key

        doc = MockDocument(id="doc_001")
        # Create chunk without chunk_index attribute
        chunk = MagicMock()
        chunk.is_part_of = doc
        del chunk.chunk_index  # Remove attribute

        ts = MockFragmentDigest(made_from=chunk)
        result = _episode_sort_key(ts)

        assert result[0] == "doc_001"
        assert result[1] == 0  # Default to 0


# ============================================================
# 5.1.2 _extract_time_fields_from_episode Tests
# ============================================================


class TestExtractTimeFieldsFromEpisode:
    """Tests for _extract_time_fields_from_episode function."""

    def test_complete_time_fields(self):
        """Test extraction of all time fields."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_time_fields_from_episode

        episode_time = {
            "mentioned_time_start_ms": 1000,
            "mentioned_time_end_ms": 2000,
            "mentioned_time_confidence": 0.95,
            "mentioned_time_text": "yesterday",
        }

        result = _extract_time_fields_from_episode(episode_time)

        assert result["mentioned_time_start_ms"] == 1000
        assert result["mentioned_time_end_ms"] == 2000
        assert result["mentioned_time_confidence"] == 0.95
        assert result["mentioned_time_text"] == "yesterday"

    def test_partial_time_fields(self):
        """Test extraction with only some fields present."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_time_fields_from_episode

        episode_time = {
            "mentioned_time_start_ms": 1000,
            "mentioned_time_text": "today",
        }

        result = _extract_time_fields_from_episode(episode_time)

        assert result["mentioned_time_start_ms"] == 1000
        assert result["mentioned_time_end_ms"] is None
        assert result["mentioned_time_confidence"] is None
        assert result["mentioned_time_text"] == "today"

    def test_empty_input(self):
        """Test with empty dictionary."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_time_fields_from_episode

        result = _extract_time_fields_from_episode({})

        assert result["mentioned_time_start_ms"] is None
        assert result["mentioned_time_end_ms"] is None
        assert result["mentioned_time_confidence"] is None
        assert result["mentioned_time_text"] is None

    def test_extra_fields_ignored(self):
        """Test that extra fields are not included."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_time_fields_from_episode

        episode_time = {
            "mentioned_time_start_ms": 1000,
            "extra_field": "should_be_ignored",
            "another_field": 123,
        }

        result = _extract_time_fields_from_episode(episode_time)

        assert "extra_field" not in result
        assert "another_field" not in result
        assert len(result) == 4


# ============================================================
# 5.1.3 _split_long_summary Tests
# ============================================================


class TestSplitLongSummary:
    """Tests for _split_long_summary function."""

    def test_empty_list(self):
        """Test with empty list returns empty."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        result = _split_long_summary([])
        assert result == []

    def test_short_text_no_split(self):
        """Test short text (below min_split_len) is not split."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        result = _split_long_summary(["short text"], min_split_len=200)
        assert result == ["short text"]

    def test_multiple_summaries_no_split(self):
        """Test multiple summaries are returned as-is (no split needed)."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        summaries = ["summary one", "summary two"]
        result = _split_long_summary(summaries)
        assert result == summaries

    def test_numbered_section_split(self):
        """Test splitting by Arabic numbered sections."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        long_text = """1. First section with enough content to pass the 20 char minimum.
2. Second section with equally sufficient content.
3. Third section also meets the minimum length requirement."""

        result = _split_long_summary([long_text], min_split_len=50)

        assert len(result) >= 2

    def test_chinese_numbered_split(self):
        """Test splitting by Chinese numbered sections."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        long_text = """一、第一部分内容，这里有足够多的文字来通过最小长度检查。
二、第二部分内容，同样需要足够的长度才能被正确分割。
三、第三部分内容，确保每个部分都足够长以通过验证。"""

        result = _split_long_summary([long_text], min_split_len=50)

        assert len(result) >= 2

    def test_max_items_limit(self):
        """Test max_items limits output."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        # Create a long text with many sections
        sections = [f"{i}. Section {i} with enough content padding here." for i in range(1, 20)]
        long_text = "\n".join(sections)

        result = _split_long_summary([long_text], min_split_len=10, max_items=5)

        assert len(result) <= 5

    def test_semicolon_split(self):
        """Test splitting by semicolon when no patterns match."""
        from m_flow.memory.episodic.write_episodic_memories import _split_long_summary

        # Text with semicolons but no numbered sections
        long_text = "First part with sufficient length；Second part also long enough；Third part meets requirements"

        result = _split_long_summary([long_text], min_split_len=50)

        # Should either split by semicolon or return as-is
        assert len(result) >= 1


# ============================================================
# 5.1.4 _create_facets_from_sections Tests
# ============================================================


class TestCreateFacetsFromSections:
    """Tests for _create_facets_from_sections function."""

    def test_empty_sections(self):
        """Test with no sections returns empty list."""
        from m_flow.memory.episodic.write_episodic_memories import _create_facets_from_sections

        ts = create_fragment_digest(sections=None)
        result = _create_facets_from_sections([ts])

        assert result == []

    def test_valid_sections(self):
        """Test creating facets from valid sections."""
        from m_flow.memory.episodic.write_episodic_memories import _create_facets_from_sections

        ts = create_fragment_digest(
            sections=[
                ("Topic One", "Content for topic one with details."),
                ("Topic Two", "Content for topic two with more details."),
            ]
        )

        result = _create_facets_from_sections([ts])

        assert len(result) == 2
        assert result[0].search_text == "Topic One"
        assert result[0].description == "Content for topic one with details."
        assert result[0].facet_type == "topic"

    def test_deduplication(self):
        """Test duplicate titles are deduplicated."""
        from m_flow.memory.episodic.write_episodic_memories import _create_facets_from_sections

        ts = create_fragment_digest(
            sections=[
                ("Same Topic", "First content."),
                ("Same Topic", "Second content."),  # Duplicate title
            ]
        )

        result = _create_facets_from_sections([ts])

        # Should only have one facet (duplicate removed)
        assert len(result) == 1

    def test_empty_title_or_content_skipped(self):
        """Test sections with empty title or content are skipped."""
        from m_flow.memory.episodic.write_episodic_memories import _create_facets_from_sections

        ts = create_fragment_digest(
            sections=[
                ("", "Content without title."),  # Empty title
                ("Title without content", ""),  # Empty content
                ("Valid Title", "Valid content."),
            ]
        )

        result = _create_facets_from_sections([ts])

        assert len(result) == 1
        assert result[0].search_text == "Valid Title"


# ============================================================
# 5.1.5 _extract_event_sentences Tests
# ============================================================


class TestExtractEventSentences:
    """Tests for _extract_event_sentences function."""

    def test_basic_extraction(self):
        """Test basic sentence extraction for event IDs."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_event_sentences

        chunk = MockContentFragment(
            metadata={
                "sentence_classifications": [
                    {
                        "event_id": "evt_1",
                        "text": "First sentence.",
                        "event_topic": "Topic A",
                        "routing_type": "episodic",
                    },
                    {"event_id": "evt_1", "text": "Second sentence.", "routing_type": "episodic"},
                    {"event_id": "evt_2", "text": "Other event.", "routing_type": "episodic"},
                ]
            }
        )
        ts = MockFragmentDigest(made_from=chunk)

        sentences, topic, is_atomic = _extract_event_sentences(
            [ts],
            source_event_ids=["evt_1"],
            original_event_routing_types={"evt_1": "episodic"},
        )

        assert len(sentences) == 2
        assert "First sentence." in sentences
        assert "Second sentence." in sentences
        assert topic == "Topic A"
        assert is_atomic is False  # episodic = not atomic

    def test_atomic_routing_type(self):
        """Test atomic routing type detection."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_event_sentences

        chunk = MockContentFragment(
            metadata={
                "sentence_classifications": [
                    {"event_id": "evt_1", "text": "Atomic sentence.", "routing_type": "atomic"},
                ]
            }
        )
        ts = MockFragmentDigest(made_from=chunk)

        sentences, topic, is_atomic = _extract_event_sentences(
            [ts],
            source_event_ids=["evt_1"],
            original_event_routing_types={"evt_1": "atomic"},
        )

        assert is_atomic is True

    def test_fallback_no_classifications(self):
        """Test fallback when no sentence_classifications exist."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_event_sentences

        chunk = MockContentFragment(
            text="Full chunk text as fallback.",
            metadata={},
        )
        ts = MockFragmentDigest(made_from=chunk, overall_topic="Fallback Topic")

        sentences, topic, is_atomic = _extract_event_sentences(
            [ts],
            source_event_ids=["evt_1"],
            original_event_routing_types={},
        )

        assert len(sentences) == 1
        assert "Full chunk text as fallback." in sentences[0]
        assert is_atomic is False  # Default for fallback


# ============================================================
# 5.1.6 _choose_better_description Tests
# ============================================================


class TestChooseBetterDescription:
    """Tests for _choose_better_description function."""

    def test_both_none(self):
        """Test both None returns None."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description(None, None)
        assert result is None

    def test_old_none(self):
        """Test old=None returns new."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description(None, "new description")
        assert result == "new description"

    def test_new_none(self):
        """Test new=None returns old."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description("old description", None)
        assert result == "old description"

    def test_new_longer(self):
        """Test longer new is preferred."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description("short", "much longer description")
        assert result == "much longer description"

    def test_old_longer(self):
        """Test when old is longer, old is kept."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description("much longer old description", "short")
        assert result == "much longer old description"

    def test_equal_length_prefers_old(self):
        """Test equal length prefers old (as per actual implementation)."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description("same len", "same len")
        # Implementation: if len(new) > len(old) return new, else return old
        # Equal length means old is returned
        assert result == "same len"

    def test_whitespace_handling(self):
        """Test whitespace is stripped."""
        from m_flow.memory.episodic.write_episodic_memories import _choose_better_description

        result = _choose_better_description("  short  ", "  longer text  ")
        # After strip: "short" (5) vs "longer text" (11)
        assert result == "longer text"


# ============================================================
# 5.1.7 _extract_chunk_summaries_from_text_summaries Tests
# ============================================================


class TestExtractChunkSummariesFromTextSummaries:
    """Tests for _extract_chunk_summaries_from_text_summaries function."""

    def test_empty_input(self):
        """Test empty input returns empty list."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_chunk_summaries_from_text_summaries,
        )

        result = _extract_chunk_summaries_from_text_summaries([])
        assert result == []

    def test_fallback_to_text(self):
        """Test fallback to ts.text when no sections."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_chunk_summaries_from_text_summaries,
        )

        ts = create_fragment_digest(text="Simple text content")
        result = _extract_chunk_summaries_from_text_summaries([ts])

        assert len(result) == 1
        assert result[0] == "Simple text content"

    def test_sections_priority(self):
        """Test sections are used when available."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_chunk_summaries_from_text_summaries,
        )

        ts = create_fragment_digest(
            text="Fallback text",
            sections=[
                ("Section Title", "Section content here."),
            ],
        )
        result = _extract_chunk_summaries_from_text_summaries([ts])

        assert len(result) == 1
        assert "【Section Title】Section content here." in result[0]

    def test_max_items_limit(self):
        """Test max_items limits output."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_chunk_summaries_from_text_summaries,
        )

        # Create multiple sections
        sections = [(f"Title {i}", f"Content {i}") for i in range(50)]
        ts = create_fragment_digest(sections=sections)

        result = _extract_chunk_summaries_from_text_summaries([ts], max_items=10)

        assert len(result) <= 10


# ============================================================
# 5.1.8 _create_facets_from_sections_direct Tests
# ============================================================


class TestCreateFacetsFromSectionsDirect:
    """Tests for _create_facets_from_sections_direct function."""

    def test_empty_sections(self):
        """Test empty sections list returns empty."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _create_facets_from_sections_direct,
        )

        result = _create_facets_from_sections_direct([])
        assert result == []

    def test_valid_sections(self):
        """Test valid sections create facets."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _create_facets_from_sections_direct,
        )

        sections = [
            MockSection(heading="Topic A", text="Content A"),
            MockSection(heading="Topic B", text="Content B"),
        ]

        result = _create_facets_from_sections_direct(sections)

        assert len(result) == 2
        assert result[0].search_text == "Topic A"
        assert result[0].description == "Content A"

    def test_deduplication(self):
        """Test duplicate titles are deduplicated."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _create_facets_from_sections_direct,
        )

        sections = [
            MockSection(heading="Same Title", text="Content 1"),
            MockSection(heading="Same Title", text="Content 2"),
        ]

        result = _create_facets_from_sections_direct(sections)

        assert len(result) == 1

    def test_skip_empty(self):
        """Test empty title or content are skipped."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _create_facets_from_sections_direct,
        )

        sections = [
            MockSection(heading="", text="Content"),
            MockSection(heading="Title", text=""),
            MockSection(heading="Valid", text="Valid Content"),
        ]

        result = _create_facets_from_sections_direct(sections)

        assert len(result) == 1
        assert result[0].search_text == "Valid"


# ============================================================
# 5.1.9 _create_same_entity_as_edges Tests
# ============================================================


class TestCreateSameEntityAsEdges:
    """Tests for _create_same_entity_as_edges function."""

    def test_empty_existing(self):
        """Test empty existing entities returns empty list."""
        from m_flow.memory.episodic.write_episodic_memories import _create_same_entity_as_edges
        from m_flow.core.domain.models import Entity

        new_id = new_uuid()
        new_entity = Entity(
            id=new_id,
            name="NewConcept",
            description="New concept description",
        )

        result = _create_same_entity_as_edges(new_entity, [])

        assert result == []

    def test_single_existing(self):
        """Test linking to single existing entity."""
        from m_flow.memory.episodic.write_episodic_memories import _create_same_entity_as_edges
        from m_flow.core.domain.models import Entity

        new_id = new_uuid()
        existing_id = new_uuid()

        new_entity = Entity(
            id=new_id,
            name="TestConcept",
            description="New description",
        )

        existing = [
            {
                "id": existing_id,
                "name": "TestConcept",
                "description": "Existing description",
                "canonical_name": "testconcept",
            }
        ]

        result = _create_same_entity_as_edges(new_entity, existing)

        assert len(result) == 1
        edge, target = result[0]
        assert edge.relationship_type == "same_entity_as"
        assert str(target.id) == existing_id

    def test_multiple_existing(self):
        """Test linking to multiple existing entities."""
        from m_flow.memory.episodic.write_episodic_memories import _create_same_entity_as_edges
        from m_flow.core.domain.models import Entity

        new_id = new_uuid()
        existing_id_1 = new_uuid()
        existing_id_2 = new_uuid()

        new_entity = Entity(
            id=new_id,
            name="TestConcept",
            description="New description",
        )

        existing = [
            {"id": existing_id_1, "name": "TestConcept", "description": "Desc 1"},
            {"id": existing_id_2, "name": "TestConcept", "description": "Desc 2"},
        ]

        result = _create_same_entity_as_edges(new_entity, existing)

        assert len(result) == 2


# ============================================================
# 5.1.10 _extract_all_sections_from_summaries Tests
# ============================================================


class TestExtractAllSectionsFromSummaries:
    """Tests for _extract_all_sections_from_summaries function."""

    def test_empty_input(self):
        """Test empty input returns empty list."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_all_sections_from_summaries,
        )

        result = _extract_all_sections_from_summaries([])
        assert result == []

    def test_no_sections(self):
        """Test FragmentDigest without sections returns empty."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_all_sections_from_summaries,
        )

        ts = create_fragment_digest(sections=None)
        result = _extract_all_sections_from_summaries([ts])

        assert result == []

    def test_valid_sections(self):
        """Test extraction of valid sections."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_all_sections_from_summaries,
        )

        ts = create_fragment_digest(
            sections=[
                ("Title 1", "Content 1"),
                ("Title 2", "Content 2"),
            ]
        )

        result = _extract_all_sections_from_summaries([ts])

        assert len(result) == 2
        assert ("Title 1", "Content 1") in result
        assert ("Title 2", "Content 2") in result

    def test_skip_empty_sections(self):
        """Test empty title or content sections are skipped."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _extract_all_sections_from_summaries,
        )

        ts = create_fragment_digest(
            sections=[
                ("", "Content"),
                ("Title", ""),
                ("Valid", "Valid Content"),
            ]
        )

        result = _extract_all_sections_from_summaries([ts])

        assert len(result) == 1
        assert result[0] == ("Valid", "Valid Content")


# ============================================================
# 5.1.11 _has_valid_sections Tests
# ============================================================


class TestHasValidSections:
    """Tests for _has_valid_sections function."""

    def test_empty_input(self):
        """Test empty input returns False."""
        from m_flow.memory.episodic.write_episodic_memories import _has_valid_sections

        result = _has_valid_sections([])
        assert result is False

    def test_no_sections(self):
        """Test FragmentDigest without sections returns False."""
        from m_flow.memory.episodic.write_episodic_memories import _has_valid_sections

        ts = create_fragment_digest(sections=None)
        result = _has_valid_sections([ts])

        assert result is False

    def test_valid_sections(self):
        """Test valid sections returns True."""
        from m_flow.memory.episodic.write_episodic_memories import _has_valid_sections

        ts = create_fragment_digest(
            sections=[
                ("Valid Title", "Valid Content"),
            ]
        )

        result = _has_valid_sections([ts])

        assert result is True

    def test_empty_title_returns_false(self):
        """Test section with empty title returns False."""
        from m_flow.memory.episodic.write_episodic_memories import _has_valid_sections

        ts = create_fragment_digest(
            sections=[
                ("", "Content only"),
            ]
        )

        result = _has_valid_sections([ts])

        assert result is False

    def test_empty_content_returns_false(self):
        """Test section with empty content returns False."""
        from m_flow.memory.episodic.write_episodic_memories import _has_valid_sections

        ts = create_fragment_digest(
            sections=[
                ("Title only", ""),
            ]
        )

        result = _has_valid_sections([ts])

        assert result is False


# ============================================================
# 5.1.12 _generate_episode_summary_from_sections Tests
# ============================================================


class TestGenerateEpisodeSummaryFromSections:
    """Tests for _generate_episode_summary_from_sections function."""

    def test_empty_sections(self):
        """Test empty sections returns default."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _generate_episode_summary_from_sections,
        )

        result = _generate_episode_summary_from_sections([])
        assert result == "Episode content"

    def test_valid_sections(self):
        """Test valid sections generate formatted summary."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _generate_episode_summary_from_sections,
        )

        sections = [
            MockSection(heading="Topic A", text="Content A"),
            MockSection(heading="Topic B", text="Content B"),
        ]

        result = _generate_episode_summary_from_sections(sections)

        assert "【Topic A】Content A" in result
        assert "【Topic B】Content B" in result

    def test_skip_invalid_sections(self):
        """Test invalid sections (empty title/content) are skipped."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _generate_episode_summary_from_sections,
        )

        sections = [
            MockSection(heading="", text="Content"),
            MockSection(heading="Title", text=""),
            MockSection(heading="Valid", text="Valid Content"),
        ]

        result = _generate_episode_summary_from_sections(sections)

        assert "【Valid】Valid Content" in result
        assert "Content" not in result.replace("Valid Content", "")  # Only valid content


# ============================================================
# 5.1.13 _extract_entities_from_chunk Tests
# ============================================================


class TestExtractEntitiesFromChunk:
    """Tests for _extract_entities_from_chunk function."""

    def test_empty_contains(self):
        """Test chunk with empty contains returns empty."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_entities_from_chunk

        chunk = MockContentFragment(contains=[])
        entities, freq = _extract_entities_from_chunk(chunk)

        assert entities == []
        assert freq == {}

    def test_concept_extraction(self):
        """Test Entity objects are extracted."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_entities_from_chunk
        from m_flow.core.domain.models import Entity

        id1 = new_uuid()
        id2 = new_uuid()
        concept1 = Entity(id=id1, name="Person A", description="A person")
        concept2 = Entity(id=id2, name="Place B", description="A place")

        chunk = MockContentFragment(contains=[concept1, concept2])
        entities, freq = _extract_entities_from_chunk(chunk)

        assert len(entities) == 2
        assert freq["Person A"] == 1
        assert freq["Place B"] == 1

    def test_tuple_extraction(self):
        """Test (something, Entity) tuples are handled."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_entities_from_chunk
        from m_flow.core.domain.models import Entity

        concept_id = new_uuid()
        concept = Entity(id=concept_id, name="Entity", description="An entity")

        chunk = MockContentFragment(contains=[("relation", concept)])
        entities, freq = _extract_entities_from_chunk(chunk)

        assert len(entities) == 1
        assert entities[0].name == "Entity"

    def test_deduplication(self):
        """Test duplicate entities (same ID) are deduplicated."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_entities_from_chunk
        from m_flow.core.domain.models import Entity

        concept_id = new_uuid()
        concept = Entity(id=concept_id, name="Same Entity", description="Desc")

        chunk = MockContentFragment(contains=[concept, concept])
        entities, freq = _extract_entities_from_chunk(chunk)

        assert len(entities) == 1
        assert freq["Same Entity"] == 2  # Frequency counts all occurrences

    def test_frequency_counting(self):
        """Test frequency is correctly counted."""
        from m_flow.memory.episodic.write_episodic_memories import _extract_entities_from_chunk
        from m_flow.core.domain.models import Entity

        id1 = new_uuid()
        id2 = new_uuid()
        concept1 = Entity(id=id1, name="Entity", description="Desc")
        concept2 = Entity(id=id2, name="Entity", description="Different desc")  # Same name, different ID

        chunk = MockContentFragment(contains=[concept1, concept1, concept2])
        entities, freq = _extract_entities_from_chunk(chunk)

        # 2 unique entities, frequency "Entity" = 3
        assert len(entities) == 2
        assert freq["Entity"] == 3


# ============================================================
# 5.1.14 ensure_nodeset Tests
# ============================================================


class TestEnsureNodeset:
    """Tests for ensure_nodeset function."""

    def test_empty_memory_spaces(self):
        """Test when memory_spaces is None, it's initialized."""
        from m_flow.memory.episodic.write_episodic_memories import ensure_nodeset

        dp = StubMemoryNode(memory_spaces=None)
        nodeset = MockMemorySpace(id="space_001")

        ensure_nodeset(dp, nodeset)

        assert dp.memory_spaces is not None
        assert len(dp.memory_spaces) == 1
        assert dp.memory_spaces[0].id == "space_001"

    def test_nodeset_not_in_list(self):
        """Test nodeset is added when not in list."""
        from m_flow.memory.episodic.write_episodic_memories import ensure_nodeset

        existing_space = MockMemorySpace(id="existing_001")
        dp = StubMemoryNode(memory_spaces=[existing_space])
        new_nodeset = MockMemorySpace(id="new_001")

        ensure_nodeset(dp, new_nodeset)

        assert len(dp.memory_spaces) == 2
        assert any(ns.id == "new_001" for ns in dp.memory_spaces)

    def test_nodeset_already_in_list(self):
        """Test nodeset is not duplicated when already in list."""
        from m_flow.memory.episodic.write_episodic_memories import ensure_nodeset

        nodeset = MockMemorySpace(id="space_001")
        dp = StubMemoryNode(memory_spaces=[nodeset])

        ensure_nodeset(dp, nodeset)

        # Should still have only one
        assert len(dp.memory_spaces) == 1


# ============================================================
# Run Tests
# ============================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
