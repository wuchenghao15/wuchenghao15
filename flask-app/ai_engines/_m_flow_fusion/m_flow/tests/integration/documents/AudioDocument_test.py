"""M-Flow AudioDocument × TextChunker integration checks (no waveform decode).

This module validates that ``AudioDocument.read`` yields sentence-aligned slices
when the sentence-chunking task cannot obtain a tokenizer from the embedding
engine. We swap in a transcript-only script about product/checkout tension,
advance the async iterator in lockstep with a hand-built oracle, and fail fast if
any slice’s word budget, Unicode length, or cut marker drifts from that oracle.
"""

from __future__ import annotations

import sys
import uuid
from typing import NamedTuple
from unittest.mock import patch

import pytest

from m_flow.data.processing.document_types.AudioDocument import AudioDocument
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.tests.integration.documents.async_gen_zip import async_gen_zip


class _OracleSlice(NamedTuple):
    """One row of the reference table keyed to each emitted chunk in order."""

    word_budget: int
    unicode_width: int
    cut_marker: str


_ORACLE_ROWS: tuple[_OracleSlice, ...] = (
    _OracleSlice(57, 353, "sentence_end"),
    _OracleSlice(58, 358, "sentence_end"),
    _OracleSlice(41, 219, "sentence_cut"),
)

_CHUNK_SENTENCE_PKG = sys.modules.get("m_flow.ingestion.chunks.split_sentences")

_SYNTH_TRANSCRIPT_BODY = '''
"Mike, we need to talk about the payment processing service."
"Good timing. The board wants one-click checkout by end of quarter."
"That's exactly the problem. The service is held together with duct tape. One wrong move and—"
"Sarah, we've been over this. The market won't wait."
"And neither will a system collapse! The technical debt is crushing us. Every new feature takes twice as long as it should."
"Then work twice as hard. Our competitors—"
"Our competitors will laugh when our whole system goes down during Black Friday! We're talking about financial transactions here, not some blog comments section."
"Write up your concerns in a doc. Right now, we ship one-click."
"Then you'll ship it without me. I won't stake my reputation on a house of cards."
"Are you threatening to quit?"
"No, I'm threatening to be right. And when it breaks, I want it in writing that you chose this."
"The feature ships, Sarah. That's final."'''


def _embedding_stub_without_tokenizer():
    """Factory passed to ``side_effect``: engine object with no tokenizer attribute path."""

    class _StubEngine:
        tokenizer = None

    return _StubEngine()


# Shared by sibling document integration tests that patch ``split_sentences``.
mock_get_embedding_engine = _embedding_stub_without_tokenizer


def _actual_triplet(piece):
    """Project a chunk object into the three scalars we compare against the oracle."""

    return (piece.chunk_size, len(piece.text), piece.cut_type)


def _expected_triplet(row: _OracleSlice):
    """Project an oracle row into the same tuple shape as ``_actual_triplet``."""

    return (row.word_budget, row.unicode_width, row.cut_marker)


@pytest.mark.asyncio
async def test_audio_document_chunk_boundaries():
    """Each async step must reproduce the next oracle row as a (words, chars, cut) triple."""

    patch_engine = patch.object(
        _CHUNK_SENTENCE_PKG,
        "get_embedding_engine",
        side_effect=_embedding_stub_without_tokenizer,
    )
    patch_transcript = patch.object(
        AudioDocument,
        "transcribe_audio",
        return_value=_SYNTH_TRANSCRIPT_BODY,
    )

    audio_ingest_target = AudioDocument(
        id=uuid.uuid4(),
        name="mflow-audio-sample",
        processed_path="",
        external_metadata="",
        mime_type="",
    )
    chunk_iterable = audio_ingest_target.read(chunker_cls=TextChunker, max_chunk_size=64)
    zipped_walk = async_gen_zip(_ORACLE_ROWS, chunk_iterable)

    with patch_engine, patch_transcript:
        slot = 0
        async for oracle_row, live_chunk in zipped_walk:
            slot += 1
            observed = _actual_triplet(live_chunk)
            golden = _expected_triplet(oracle_row)
            if observed != golden:
                raise AssertionError(f"chunk index {slot - 1}: expected {golden}, observed {observed}")
