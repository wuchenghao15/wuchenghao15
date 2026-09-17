"""M-Flow 图片文档分块验证模块"""

from __future__ import annotations

import sys
import uuid

import pytest
from unittest.mock import patch

from m_flow.data.processing.document_types.ImageDocument import ImageDocument
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.tests.integration.documents.AudioDocument_test import mock_get_embedding_engine
from m_flow.tests.integration.documents.async_gen_zip import async_gen_zip

_sentence_splitter = sys.modules.get("m_flow.ingestion.chunks.split_sentences")

SAMPLE_DESCRIPTION = (
    "A dramatic confrontation unfolds as a red fox and river otter engage in an "
    "energetic wrestling match at the water's edge. The fox, teeth bared in a playful "
    "snarl, has its front paws locked with the otter's flippers as they roll through "
    "the shallow stream, sending water spraying in all directions. The otter, displaying "
    "its surprising agility on land, counters by twisting its sleek body and attempting "
    "to wrap itself around the fox's shoulders, its whiskered face inches from the "
    "fox's muzzle.\n"
    "The commotion has attracted an audience: a murder of crows has gathered in the "
    "low branches, their harsh calls adding to the chaos as they hop excitedly from "
    "limb to limb. One particularly bold crow dive-bombs the wrestling pair, causing "
    "both animals to momentarily freeze mid-tussle, creating a perfect snapshot of "
    "suspended action\u2014the fox's fur dripping wet, the otter's body coiled like a "
    "spring, and the crow's wings spread wide against the golden morning light."
)

CHUNK_SPECS = [
    {"word_cnt": 51, "char_len": 298, "boundary": "sentence_end"},
    {"word_cnt": 62, "char_len": 369, "boundary": "sentence_end"},
    {"word_cnt": 44, "char_len": 294, "boundary": "sentence_end"},
]


@patch.object(
    _sentence_splitter,
    "get_embedding_engine",
    side_effect=mock_get_embedding_engine,
)
@pytest.mark.asyncio
async def test_image_doc_produces_correct_chunks(_patched_engine):
    """验证 ImageDocument 转录后的文本能被正确切分为预期的块"""
    img_doc = ImageDocument(
        id=uuid.uuid4(),
        name="photo-chunk-validation",
        processed_path="",
        external_metadata="",
        mime_type="",
    )

    with patch.object(ImageDocument, "describe_image", return_value=SAMPLE_DESCRIPTION):
        async for spec, produced in async_gen_zip(
            CHUNK_SPECS, img_doc.read(chunker_cls=TextChunker, max_chunk_size=64)
        ):
            assert produced.chunk_size == spec["word_cnt"], (
                f"词数不符: 期望 {spec['word_cnt']}, 实际 {produced.chunk_size}"
            )
            assert len(produced.text) == spec["char_len"], (
                f"字符数不符: 期望 {spec['char_len']}, 实际 {len(produced.text)}"
            )
            assert produced.cut_type == spec["boundary"], (
                f"边界类型不符: 期望 {spec['boundary']}, 实际 {produced.cut_type}"
            )
