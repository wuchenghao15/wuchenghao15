"""
Fragment digest construction from ingested content fragments.

This module converts raw :class:`ContentFragment` instances into
:class:`FragmentDigest` containers.  No LLM inference happens here;
section-level summaries are deferred to the episodic-memory writer
(``summarize_by_event``), keeping this stage purely structural.

Works identically regardless of the ``MFLOW_CONTENT_ROUTING`` setting
(document-level *or* sentence-level mode).
"""

from __future__ import annotations

from typing import Type
from uuid import uuid5

import structlog
from pydantic import BaseModel

from m_flow.ingestion.chunking.models.ContentFragment import ContentFragment
from m_flow.knowledge.summarization.exceptions import InvalidSummaryInputsError
from m_flow.knowledge.summarization.models import FragmentDigest

_log = structlog.get_logger("m_flow.summarization")


async def compress_text(data_chunks: list[ContentFragment], summarization_model: Type[BaseModel] = None):
    """
    Build :class:`FragmentDigest` wrappers around every supplied fragment.

    Each digest carries the full fragment text (consumed later by the
    procedural-memory path) and leaves ``sections`` as ``None`` because
    section generation is the responsibility of ``summarize_by_event``.

    Parameters
    ----------
    data_chunks:
        Content fragments produced by the chunking stage.
    summarization_model:
        Unused – retained only for backward-compatible call sites.

    Returns
    -------
    list[FragmentDigest]
        One digest per input fragment, in the same order.

    Raises
    ------
    InvalidSummaryInputsError
        If *data_chunks* is not a list or any element lacks a ``text``
        attribute.
    """
    _validate_input(data_chunks)

    if not data_chunks:
        return data_chunks

    digest_items: list[FragmentDigest] = []
    for fragment in data_chunks:
        digest_items.append(
            FragmentDigest(
                id=uuid5(fragment.id, "FragmentDigest"),
                made_from=fragment,
                text=fragment.text or "",
                sections=None,
                overall_topic=None,
            )
        )

    _log.info(
        "fragment_digests_created",
        count=len(digest_items),
        llm_used=False,
    )
    return digest_items


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _validate_input(chunks: object) -> None:
    """Raise early on obviously invalid arguments."""
    if not isinstance(chunks, list):
        raise InvalidSummaryInputsError(f"Expected a list of ContentFragment instances, got {type(chunks).__name__}.")
    for idx, item in enumerate(chunks):
        if not hasattr(item, "text"):
            raise InvalidSummaryInputsError(
                f"Item at position {idx} has no 'text' attribute – all elements must be ContentFragment-like."
            )
