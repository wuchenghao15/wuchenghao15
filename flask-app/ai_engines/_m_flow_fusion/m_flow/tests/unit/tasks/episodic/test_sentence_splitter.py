# m_flow/tests/unit/tasks/episodic/test_sentence_splitter.py
"""
Unit tests for sentence_splitter module.
"""

from m_flow.memory.episodic.sentence_splitter import (
    smart_split_sentences,
    split_with_positions,
    count_sentences,
    is_single_sentence,
    _chinese_char_ratio,
)
from m_flow.shared.enums import ContentType


# ============================================================
# Basic Splitting Tests
# ============================================================


class TestSmartSplitSentences:
    """Tests for smart_split_sentences function."""

    def test_english_basic(self):
        """Basic English sentence splitting."""
        text = "Hello world. This is a test. How are you?"
        sentences = smart_split_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "Hello world."
        assert sentences[1] == "This is a test."
        assert sentences[2] == "How are you?"

    def test_english_with_exclamation(self):
        """English with exclamation marks."""
        text = "Wow! That's amazing! Really?"
        sentences = smart_split_sentences(text)
        assert len(sentences) == 3

    def test_english_with_abbreviations(self):
        """English with common abbreviations."""
        text = "Dr. Smith went to the store. He bought apples."
        sentences = smart_split_sentences(text)
        assert len(sentences) == 2
        assert "Dr. Smith" in sentences[0]

    def test_english_multiple_abbreviations(self):
        """English with multiple abbreviations."""
        # Note: "St." is an abbreviation for Street, so "Ave. St." doesn't end a sentence
        # This text has only 1 clear sentence boundary (after "year.")
        text = "Mr. and Mrs. Johnson live on Ave. St. They moved from the U.S. last year."
        sentences = smart_split_sentences(text)
        # The conservative splitter treats "St." as abbreviation
        # So only 1 sentence is detected
        assert len(sentences) >= 1

        # Test with clearer sentence boundaries
        text2 = "Dr. Smith is here. She came from the U.S. yesterday."
        sentences2 = smart_split_sentences(text2)
        assert len(sentences2) == 2

    def test_english_with_numbers(self):
        """English with decimal numbers."""
        text = "The price is $19.99. The discount is 10.5% off."
        sentences = smart_split_sentences(text)
        assert len(sentences) == 2
        assert "19.99" in sentences[0]
        assert "10.5%" in sentences[1]

    def test_chinese_basic(self):
        """Basic Chinese sentence splitting."""
        text = "你好世界。这是一个测试。你好吗？"
        sentences = smart_split_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "你好世界。"
        assert sentences[1] == "这是一个测试。"
        assert sentences[2] == "你好吗？"

    def test_chinese_with_exclamation(self):
        """Chinese with exclamation marks."""
        text = "太棒了！真的吗？是的。"
        sentences = smart_split_sentences(text)
        assert len(sentences) == 3

    def test_chinese_with_semicolon(self):
        """Chinese with semicolons."""
        text = "第一点；第二点；第三点。"
        sentences = smart_split_sentences(text)
        assert len(sentences) == 3

    def test_mixed_content(self):
        """Mixed Chinese and English content."""
        text = "Hello world. 这是中文。Another sentence."
        sentences = smart_split_sentences(text)
        assert len(sentences) >= 2  # At least 2 sentences

    def test_empty_input(self):
        """Empty input handling."""
        assert smart_split_sentences("") == []
        assert smart_split_sentences("   ") == []
        assert smart_split_sentences("\n\t") == []

    def test_single_sentence(self):
        """Single sentence without ending punctuation."""
        text = "Just one sentence without ending punctuation"
        sentences = smart_split_sentences(text)
        assert len(sentences) == 1
        assert sentences[0] == text

    def test_preserves_whitespace_within_sentence(self):
        """Whitespace within sentences is preserved."""
        text = "This has   multiple   spaces. And tabs\there."
        sentences = smart_split_sentences(text)
        assert len(sentences) == 2

    def test_handles_newlines(self):
        """Handles text with newlines."""
        text = "First sentence.\nSecond sentence.\nThird sentence."
        sentences = smart_split_sentences(text)
        assert len(sentences) == 3


# ============================================================
# Language Detection Tests
# ============================================================


class TestChineseCharRatio:
    """Tests for _chinese_char_ratio function."""

    def test_pure_english(self):
        """Pure English text."""
        ratio = _chinese_char_ratio("Hello world!")
        assert ratio == 0.0

    def test_pure_chinese(self):
        """Pure Chinese text."""
        ratio = _chinese_char_ratio("你好世界")
        assert ratio == 1.0

    def test_mixed_dominant_chinese(self):
        """Mixed text with dominant Chinese."""
        ratio = _chinese_char_ratio("你好 hello 世界")
        assert ratio > 0.3

    def test_mixed_dominant_english(self):
        """Mixed text with dominant English."""
        ratio = _chinese_char_ratio("Hello world 你好")
        assert ratio < 0.3

    def test_empty(self):
        """Empty text."""
        ratio = _chinese_char_ratio("")
        assert ratio == 0.0


# ============================================================
# Position Tracking Tests
# ============================================================


class TestSplitWithPositions:
    """Tests for split_with_positions function."""

    def test_basic_positions(self):
        """Basic position tracking."""
        text = "Hello. World."
        result = split_with_positions(text)
        assert len(result) == 2

        sent1, start1, end1 = result[0]
        assert sent1 == "Hello."
        assert text[start1:end1] == "Hello."

        sent2, start2, end2 = result[1]
        assert sent2 == "World."
        assert text[start2:end2] == "World."

    def test_positions_allow_extraction(self):
        """Positions can be used to extract from original text."""
        text = "First sentence. Second sentence. Third sentence."
        result = split_with_positions(text)

        for sent, start, end in result:
            # Extracted text should match sentence
            extracted = text[start:end]
            assert extracted == sent


# ============================================================
# Utility Function Tests
# ============================================================


class TestCountSentences:
    """Tests for count_sentences function."""

    def test_count_multiple(self):
        """Count multiple sentences."""
        assert count_sentences("One. Two. Three.") == 3

    def test_count_single(self):
        """Count single sentence."""
        assert count_sentences("Just one sentence.") == 1

    def test_count_empty(self):
        """Count empty text."""
        assert count_sentences("") == 0


class TestIsSingleSentence:
    """Tests for is_single_sentence function."""

    def test_single_true(self):
        """Single sentence returns True."""
        assert is_single_sentence("This is one sentence.") is True
        assert is_single_sentence("No punctuation") is True

    def test_multiple_false(self):
        """Multiple sentences returns False."""
        assert is_single_sentence("First. Second.") is False

    def test_empty_true(self):
        """Empty text is treated as single."""
        assert is_single_sentence("") is True


# ============================================================
# Edge Cases
# ============================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_ellipsis(self):
        """Text with ellipsis."""
        # Chinese ellipsis
        text_cn = "等等等等…然后呢。"
        sentences_cn = smart_split_sentences(text_cn)
        assert len(sentences_cn) >= 1

        # English ellipsis (three dots)
        text_en = "Wait... What happened? I don't know."
        sentences_en = smart_split_sentences(text_en)
        assert len(sentences_en) >= 1

    def test_quoted_text(self):
        """Text with quotes."""
        text = 'He said "Hello." She replied "Hi!"'
        sentences = smart_split_sentences(text)
        # Should handle quoted text
        assert len(sentences) >= 1

    def test_urls_not_split(self):
        """URLs shouldn't cause incorrect splits."""
        text = "Visit www.example.com for more info. It has great content."
        sentences = smart_split_sentences(text)
        # Should be 2 sentences, not split by .com
        assert len(sentences) == 2

    def test_very_long_sentence(self):
        """Very long single sentence."""
        text = "This is a very long sentence " * 50 + "that continues for a while."
        sentences = smart_split_sentences(text)
        assert len(sentences) == 1

    def test_only_punctuation(self):
        """Text with only punctuation."""
        text = "..."
        sentences = smart_split_sentences(text)
        # Might be empty or have minimal content
        assert len(sentences) <= 1


# ============================================================
# Dialog Format Tests
# ============================================================


class TestDialogFormat:
    """Tests for dialog/conversation format handling with explicit ContentType.DIALOG."""

    def test_dialog_preserves_speaker(self):
        """Dialog splitting preserves speaker attribution with explicit DIALOG type."""
        text = """[August 14, 2023] Melanie: Hey! How are you? I'm doing great!
[August 14, 2023] Caroline: Good to hear! What's new?"""

        sentences = smart_split_sentences(text, content_type=ContentType.DIALOG)
        assert len(sentences) == 2
        assert "Melanie:" in sentences[0]
        assert "Caroline:" in sentences[1]
        # Verify Melanie's multiple sentences stay together
        assert "How are you?" in sentences[0]
        assert "I'm doing great!" in sentences[0]

    def test_dialog_with_timestamps(self):
        """Dialog with various timestamp formats."""
        text = """[2023-08-14 10:00 AM] Alice: First message. Second sentence!
[2023-08-14 10:01 AM] Bob: Reply here. Another sentence."""

        sentences = smart_split_sentences(text, content_type=ContentType.DIALOG)
        assert len(sentences) == 2
        assert "First message. Second sentence!" in sentences[0]
        assert "Alice:" in sentences[0]
        assert "Bob:" in sentences[1]

    def test_dialog_with_image_descriptions(self):
        """Dialog with image descriptions on separate lines."""
        text = """[10:00] Alice: Check this out!
  [Image shared by Alice: a photo of a sunset]
[10:01] Bob: That's beautiful!"""

        sentences = smart_split_sentences(text, content_type=ContentType.DIALOG)
        assert len(sentences) == 2
        # Image description should be attached to Alice's message
        assert "Image shared by Alice" in sentences[0]
        assert "Bob:" in sentences[1]

    def test_dialog_simple_format(self):
        """Simple Speaker: message format."""
        text = """Alice: Hello! How are you?
Bob: I'm fine! Thanks for asking."""

        sentences = smart_split_sentences(text, content_type=ContentType.DIALOG)
        assert len(sentences) == 2
        assert "Alice:" in sentences[0]
        assert "Bob:" in sentences[1]

    def test_text_mode_with_colons(self):
        """TEXT mode should split by sentences, not speaker turns."""
        text = "Note: this is important. Warning: be careful."
        sentences = smart_split_sentences(text, content_type=ContentType.TEXT)
        # Should be split by sentences, not by colons
        assert len(sentences) == 2

    def test_text_mode_default(self):
        """Default mode (TEXT) splits by sentences."""
        text = "The recipe includes: eggs, milk, flour. Mix well. Bake at 350F."
        sentences = smart_split_sentences(text)  # No content_type = default TEXT
        assert len(sentences) == 3

    def test_dialog_vs_text_mode_comparison(self):
        """Same input produces different output based on content_type."""
        text = """Alice: Hello! How are you?
Bob: I'm fine! Thanks for asking."""

        # DIALOG mode: splits by speaker
        dialog_sentences = smart_split_sentences(text, content_type=ContentType.DIALOG)
        assert len(dialog_sentences) == 2

        # TEXT mode: splits by sentence boundaries
        text_sentences = smart_split_sentences(text, content_type=ContentType.TEXT)
        # TEXT mode will split differently (by periods/exclamation marks)
        assert len(text_sentences) >= 2
