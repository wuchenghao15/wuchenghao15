"""Validate paragraph-level text splitting produces correct segments."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from m_flow.ingestion.chunks import split_paragraphs

_SENTENCE_MOD = sys.modules.get("m_flow.ingestion.chunks.split_sentences")


def _stub_embedding_engine():
    class _Stub:
        tokenizer = None

    return _Stub()


_DOC_ENDING_WITH_PERIOD = (
    "This is example text. It contains multiple sentences.\n"
    "This is a second paragraph. First two paragraphs are whole.\n"
    "Third paragraph is a bit longer and is finished with a dot."
)

_DOC_WITHOUT_TRAILING_PERIOD = (
    "This is example text. It contains multiple sentences.\n"
    "This is a second paragraph. First two paragraphs are whole.\n"
    "Third paragraph is cut and is missing the dot at the end"
)

_REFERENCE_SEGMENTS_PERIOD = [
    ("This is example text. It contains multiple sentences.", 8, "paragraph_end"),
    ("\nThis is a second paragraph. First two paragraphs are whole.", 10, "paragraph_end"),
    ("\nThird paragraph is a bit longer and is finished with a dot.", 12, "sentence_end"),
]

_REFERENCE_SEGMENTS_NO_PERIOD = [
    ("This is example text. It contains multiple sentences.", 8, "paragraph_end"),
    ("\nThis is a second paragraph. First two paragraphs are whole.", 10, "paragraph_end"),
    ("\nThird paragraph is cut and is missing the dot at the end", 12, "sentence_cut"),
]


@pytest.mark.parametrize(
    "document,reference_segments",
    [
        pytest.param(_DOC_ENDING_WITH_PERIOD, _REFERENCE_SEGMENTS_PERIOD, id="terminated"),
        pytest.param(
            _DOC_WITHOUT_TRAILING_PERIOD,
            _REFERENCE_SEGMENTS_NO_PERIOD,
            id="unterminated",
        ),
    ],
)
@patch.object(_SENTENCE_MOD, "get_embedding_engine", side_effect=_stub_embedding_engine)
def test_paragraph_splitting(mock_eng, document, reference_segments):
    """Splitting a multi-paragraph document must yield three segments with matching attributes."""
    produced = list(split_paragraphs(data=document, batch_paragraphs=False, max_chunk_size=12))

    assert len(produced) == len(reference_segments)

    for segment, (ref_text, ref_size, ref_cut) in zip(produced, reference_segments):
        assert segment["text"] == ref_text
        assert segment["chunk_size"] == ref_size
        assert segment["cut_type"] == ref_cut
