"""
实体提取测试
"""

from __future__ import annotations

import asyncio
import pathlib

import m_flow
import m_flow.ingestion.core as ingestion
from m_flow.auth.methods import get_seed_user
from m_flow.data.processing.document_types import TextDocument
from m_flow.ingestion.chunking.TextChunker import TextChunker
from m_flow.ingestion.documents import segment_documents
from m_flow.ingestion.pipeline_tasks import save_data_item_to_storage
from m_flow.llm import get_max_chunk_tokens
from m_flow.llm.extraction import extract_content_graph
from m_flow.shared.data_models import ExtractedGraph
from m_flow.shared.files.utils.open_data_file import open_data_file

_TARGET_TERMS = ("qubit", "algorithm", "superposition")
_TEST_FILE = pathlib.Path(__file__).parent.parent.parent / "test_data" / "Quantum_computers.txt"
_REPS = 5
_THRESHOLD = 0.8


async def _extract_and_check(chunks: list) -> bool:
    """提取图并检查实体"""
    results = await asyncio.gather(*[extract_content_graph(c.text, ExtractedGraph) for c in chunks])

    return all(any(term in n.name.lower() for r in results for n in r.nodes) for term in _TARGET_TERMS)


async def run_entity_extraction_test():
    """运行实体提取测试"""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add("NLP is a subfield of computer science.")

    path = await save_data_item_to_storage(str(_TEST_FILE))

    async with open_data_file(path) as f:
        classified = ingestion.classify(f)
        data_id = await ingestion.identify(classified, await get_seed_user())

    await m_flow.add(str(_TEST_FILE))

    doc = TextDocument(
        id=data_id,
        type="text",
        mime_type="text/plain",
        name="quantum",
        processed_path=str(_TEST_FILE),
        external_metadata=None,
    )

    chunks = []
    async for chunk in segment_documents([doc], max_chunk_size=get_max_chunk_tokens(), chunker=TextChunker):
        chunks.append(chunk)

    results = await asyncio.gather(*[_extract_and_check(chunks) for _ in range(_REPS)])
    passed = sum(1 for r in results if r)

    assert passed >= _THRESHOLD * _REPS, f"通过率: {passed}/{_REPS}"


if __name__ == "__main__":
    asyncio.run(run_entity_extraction_test())
