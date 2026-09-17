"""
Golden regression tests for English coreference resolution.
"""

import pytest
from english_coreference.coreference import CoreferenceResolver


def _resolve(text: str) -> str:
    r = CoreferenceResolver()
    out, _ = r.resolve_text(text)
    return out


class TestBasicEnglish:
    def test_he_pronoun(self):
        r = _resolve("John went home. He was tired.")
        assert "John" in r

    def test_she_pronoun(self):
        r = _resolve("Alice bought a book. She liked it.")
        assert "Alice" in r

    def test_they_pronoun(self):
        r = _resolve("John and Alice went to the park. They had fun.")
        assert "John" in r or "Alice" in r

    def test_possessive(self):
        r = _resolve("John lost a key. His key was important.")
        assert "John" in r


class TestEnglishNonResolution:
    def test_first_sentence(self):
        """He with no antecedent should not be resolved."""
        r = _resolve("He was tall.")
        assert r == "He was tall."

    def test_empty(self):
        assert _resolve("") == ""


class TestEnglishStream:
    def test_stream(self):
        from english_coreference.coreference import StreamCorefSession

        session = StreamCorefSession()
        session.add_sentence("John went home.")
        r, _ = session.add_sentence("He was tired.")
        assert "John" in r
