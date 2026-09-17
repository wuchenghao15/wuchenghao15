"""Tests for Obsidian wikilink alias escaping."""

from hyperextract.utils.obsidian import _wikilink


def test_alias_strips_brackets():
    # "Array[0]" sanitizes to stem "Array 0"; the alias must not reintroduce [ ].
    out = _wikilink("Array 0", "Array[0]")
    assert out == "[[Array 0]]"


def test_alias_strips_pipe():
    out = _wikilink("A B", "A | B")
    assert out.count("|") == 0
    assert out == "[[A B]]"


def test_normal_alias_preserved():
    assert _wikilink("apple", "Apple Inc") == "[[apple|Apple Inc]]"
