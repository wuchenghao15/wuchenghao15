# m_flow/memory/episodic/sentence_level_routing.py
"""
Content Routing - Sentence-Level Grouping

Classifies content at sentence granularity, allowing a single ContentFragment
to contain multiple episodic events and/or atomic sentences.

Key Design Decisions:
- Input/Output type consistency: List[ContentFragment] → List[ContentFragment]
- Classification stored in chunk.metadata["sentence_classifications"]
- Downstream tasks read metadata to determine routing
- Fallback strategy: any error → all sentences marked as episodic

Controlled by: MFLOW_CONTENT_ROUTING (default: true)
- When true: This task is included in pipeline, performs sentence-level LLM classification
- When false: This task is not called, chunks are processed as single events

This task should be placed BEFORE compress_text in the pipeline.
"""

from __future__ import annotations

from typing import List
from uuid import uuid4

from m_flow.ingestion.chunking.models import ContentFragment
from m_flow.llm.prompts import read_query_prompt
from m_flow.llm.LLMGateway import LLMService
from m_flow.memory.episodic.models import (
    SentenceClassification,
    SentenceRoutingResult,
    EventClassification,
)
from m_flow.memory.episodic.sentence_splitter import smart_split_sentences
from m_flow.shared.enums import ContentType
from m_flow.shared.llm_concurrency import get_global_llm_semaphore
from m_flow.shared.logging_utils import get_logger

import os
import re

logger = get_logger("sentence_level_routing")

_SPEAKER_LINE_RE = re.compile(
    r"^(?:\[.*?\]\s*)?"  # optional [timestamp]
    r"(?P<speaker>"
    r"[A-Za-z\u4e00-\u9fff]"  # first char of speaker name
    r"[^:\n()\[\]{}=.]{0,20}"  # rest of name (no code punctuation)
    r")"
    r"\s*[:：]\s*"  # colon separator (ascii or fullwidth)
    r"(?P<body>.{4,})$",  # message body: at least 4 chars (CJK-safe)
    re.MULTILINE,
)


def _detect_dialog(sample_text: str, threshold: float = 0.35) -> bool:
    """Return True if *sample_text* looks like multi-speaker dialog.

    Checks whether a significant fraction of non-empty lines match the
    ``[timestamp] Speaker: message`` pattern AND at least two distinct
    speakers appear (with at least one recurring).  The speaker-repetition
    check prevents false positives on code (type annotations, config files).
    """
    lines = [ln for ln in sample_text.split("\n") if ln.strip()]
    if len(lines) < 4:
        return False

    speakers: list[str] = []
    for ln in lines:
        m = _SPEAKER_LINE_RE.match(ln.strip())
        if m:
            speakers.append(m.group("speaker").strip())

    if len(speakers) / len(lines) < threshold:
        return False

    from collections import Counter

    counts = Counter(speakers)
    distinct_speakers = len(counts)
    repeated_speakers = sum(1 for c in counts.values() if c >= 2)
    return distinct_speakers >= 2 and repeated_speakers >= 1


async def route_content_v2(
    chunks: List[ContentFragment],
    content_type: ContentType = ContentType.TEXT,
) -> List[ContentFragment]:
    """
    Sentence-level content routing.

    Creates sentence_classifications for ALL chunks, enabling unified downstream processing.
    This function is called only when MFLOW_CONTENT_ROUTING=true.

    Key Design:
    - Input/output types are identical (maintains Pipeline linearity)
    - Classification results stored in chunk.metadata["sentence_classifications"]
    - Downstream tasks read metadata to determine routing

    Note:
        Function name 'route_content_v2' preserved for backward compatibility.

    Args:
        chunks: List of ContentFragment objects
        content_type: Content type declaration (TEXT or DIALOG)
            - TEXT: Split by sentence boundaries
            - DIALOG: Split by speaker utterances

    Returns:
        Same chunks with metadata["sentence_classifications"] added
    """
    if not chunks:
        return chunks

    if content_type == ContentType.TEXT and os.getenv("MFLOW_AUTO_DETECT_DIALOG", "true").lower() not in (
        "0",
        "false",
        "no",
        "off",
    ):
        sample = "\n".join(ch.text for ch in chunks[:3] if ch.text)
        if _detect_dialog(sample):
            content_type = ContentType.DIALOG
            logger.info(f"[sentence_routing] Auto-detected DIALOG content type (sampled {len(chunks[:3])} chunks)")

    logger.info(
        f"[sentence_grouping] Processing {len(chunks)} chunks with sentence-level LLM classification "
        f"(content_type={content_type})"
    )

    for chunk_idx, chunk in enumerate(chunks):
        try:
            await _route_single_chunk(chunk, chunk_idx, content_type)
        except Exception as e:
            logger.error(f"[sentence_grouping] Error processing chunk {chunk_idx}: {e}")
            _fallback_all_episodic_to_metadata(chunk, content_type)

    logger.info(f"[sentence_grouping] Completed sentence-level routing for {len(chunks)} chunks")

    return chunks


async def _route_single_chunk(
    chunk: ContentFragment,
    chunk_idx: int,
    content_type: ContentType = ContentType.TEXT,
) -> None:
    """
    Process a single chunk and store classification in metadata.

    Args:
        chunk: ContentFragment to process
        chunk_idx: Index for logging
        content_type: Content type declaration (TEXT or DIALOG)
    """
    sentences = smart_split_sentences(chunk.text, content_type=content_type)

    if not sentences:
        logger.warning(f"[sentence_routing] Chunk {chunk_idx} has no sentences")
        chunk.metadata["sentence_classifications"] = []
        return

    # Step 2: Single sentence → decide atomic vs episodic based on length
    if len(sentences) == 1:
        text = sentences[0]
        from m_flow.memory.episodic.sentence_splitter import _chinese_char_ratio

        is_chinese = _chinese_char_ratio(text) > 0.3
        is_short = (is_chinese and len(text) <= 50) or (not is_chinese and len(text) <= 150)

        if is_short:
            routing_type = "atomic"
            event_id = f"atomic_{chunk.id}_0_{uuid4().hex[:6]}"
            event_topic = f"[Atomic] {text[:50]}..." if len(text) > 50 else f"[Atomic] {text}"
            event_focus = "Short single sentence - atomic processing"
        else:
            routing_type = "episodic"
            event_id = f"evt_{chunk.id}_{uuid4().hex[:8]}"
            event_topic = "Single sentence content"
            event_focus = "Single sentence - direct episodic processing"

        chunk.metadata["sentence_classifications"] = [
            SentenceClassification(
                sentence_idx=0,
                text=text,
                routing_type=routing_type,
                event_id=event_id,
                event_topic=event_topic,
                event_focus=event_focus,
            ).model_dump()
        ]
        logger.debug(
            f"[sentence_routing] Chunk {chunk_idx}: single sentence "
            f"({len(text)} chars, {'zh' if is_chinese else 'en'}), "
            f"default {routing_type}"
        )
        return

    # Step 3: Multiple sentences → call LLM for classification with retry logic
    # Retry once on any validation failure (invalid indices or incomplete coverage)
    max_retries = 1

    for attempt in range(max_retries + 1):
        routing_result = await _llm_route_sentences(sentences, chunk_idx)

        # Validate indices are within bounds
        indices_valid = routing_result.validate_indices(len(sentences))

        # Check coverage completeness
        is_complete = routing_result.is_complete(len(sentences))

        if indices_valid and is_complete:
            # Success
            if attempt > 0:
                logger.info(f"[sentence_routing] Retry succeeded for chunk {chunk_idx} on attempt {attempt + 1}")
            break

        # Diagnose the failure
        if not indices_valid:
            logger.warning(
                f"[sentence_routing] Invalid indices for chunk {chunk_idx} (attempt {attempt + 1}/{max_retries + 1})"
            )
        elif not is_complete:
            # Calculate coverage details
            covered = set()
            for event in routing_result.events:
                covered.update(event.sentence_indices)
            covered.update(routing_result.atomic_indices)
            expected = set(range(len(sentences)))
            missing = expected - covered

            logger.warning(
                f"[sentence_routing] Missing indices for chunk {chunk_idx}: "
                f"total={len(sentences)}, covered={len(covered)}, missing={len(missing)}, "
                f"events={len(routing_result.events)} (attempt {attempt + 1}/{max_retries + 1})"
            )

        # Retry if we have attempts left
        if attempt < max_retries:
            logger.info(f"[sentence_routing] Retrying LLM for chunk {chunk_idx}")
        else:
            # All retries exhausted, use fallback
            logger.warning(f"[sentence_routing] Retry failed for chunk {chunk_idx}, using fallback")
            routing_result = _create_fallback_result(len(sentences))

    # Step 5: Build SentenceClassification list
    classifications = []

    # Process episodic events
    for event in routing_result.events:
        event_id = f"evt_{chunk.id}_{uuid4().hex[:8]}"
        for sent_idx in event.sentence_indices:
            classifications.append(
                SentenceClassification(
                    sentence_idx=sent_idx,
                    text=sentences[sent_idx],
                    routing_type="episodic",
                    event_id=event_id,
                    event_topic=event.suggested_topic,
                    event_focus=event.focus,  # Pass semantic focus from LLM
                ).model_dump()
            )

    # Process atomic sentences - each atomic sentence becomes its own "atomic episode"
    # This allows atomic content to go through the full episodic ingestion pipeline
    for sent_idx in routing_result.atomic_indices:
        # Each atomic sentence gets its own event_id for Episode creation
        atomic_event_id = f"atomic_{chunk.id}_{sent_idx}_{uuid4().hex[:6]}"
        atomic_text = sentences[sent_idx]
        # Create a brief topic from the sentence (first 50 chars)
        atomic_topic = f"[Atomic] {atomic_text[:50]}..." if len(atomic_text) > 50 else f"[Atomic] {atomic_text}"

        classifications.append(
            SentenceClassification(
                sentence_idx=sent_idx,
                text=atomic_text,
                routing_type="atomic",
                event_id=atomic_event_id,  # Now has event_id for Episode creation
                event_topic=atomic_topic,
            ).model_dump()
        )

    # Sort by sentence_idx for consistency
    classifications.sort(key=lambda x: x["sentence_idx"])
    chunk.metadata["sentence_classifications"] = classifications

    # Log statistics
    episodic_count = sum(1 for c in classifications if c["routing_type"] == "episodic")
    atomic_count = len(classifications) - episodic_count
    event_count = len(routing_result.events)

    logger.info(
        f"[sentence_routing] Chunk {chunk_idx}: "
        f"{len(sentences)} sentences → "
        f"{event_count} events, {episodic_count} episodic, {atomic_count} atomic"
    )


async def _llm_route_sentences(
    sentences: List[str],
    chunk_idx: int,
) -> SentenceRoutingResult:
    """
    Call LLM to classify sentences.

    Args:
        sentences: List of sentences to classify
        chunk_idx: Index for logging

    Returns:
        SentenceRoutingResult with classification
    """
    system_prompt = read_query_prompt("sentence_grouping.txt")

    # Format sentences
    sentences_text = "\n".join(f"[{i}]: {sent}" for i, sent in enumerate(sentences))

    user_prompt = system_prompt.replace("{total_sentences}", str(len(sentences)))
    user_prompt = user_prompt.replace("{sentences_with_indices}", sentences_text)

    logger.debug(f"[sentence_routing] LLM prompt for chunk {chunk_idx}")

    _llm_semaphore = get_global_llm_semaphore()
    async with _llm_semaphore:
        result = await LLMService.extract_structured(
            text_input=user_prompt,
            system_prompt="",
            response_model=SentenceRoutingResult,
        )

    # Log raw result
    logger.debug(
        f"[sentence_routing] LLM result for chunk {chunk_idx}: "
        f"events={len(result.events)}, atomic={len(result.atomic_indices)}"
    )

    return result


def _create_fallback_result(total_sentences: int) -> SentenceRoutingResult:
    """
    Create fallback result: all sentences in one episodic event.

    Args:
        total_sentences: Total number of sentences

    Returns:
        SentenceRoutingResult with all sentences as episodic
    """
    return SentenceRoutingResult(
        events=[
            EventClassification(
                sentence_indices=list(range(total_sentences)),
                focus="Fallback grouping - all sentences as one event",
                suggested_topic="Unnamed episode",
            )
        ],
        atomic_indices=[],
    )


def _fallback_all_episodic_to_metadata(
    chunk: ContentFragment,
    content_type: ContentType = ContentType.TEXT,
) -> None:
    """
    Fallback: mark all content as episodic in metadata.

    Used when an error occurs during routing.

    Args:
        chunk: ContentFragment to update
        content_type: Content type declaration (TEXT or DIALOG)
    """
    sentences = smart_split_sentences(chunk.text, content_type=content_type)

    if not sentences:
        chunk.metadata["sentence_classifications"] = []
        return

    event_id = f"evt_{chunk.id}_{uuid4().hex[:8]}"
    chunk.metadata["sentence_classifications"] = [
        SentenceClassification(
            sentence_idx=i,
            text=sent,
            routing_type="episodic",
            event_id=event_id,
            event_topic="Unnamed episode",
            event_focus="Fallback - error recovery episodic processing",
        ).model_dump()
        for i, sent in enumerate(sentences)
    ]


# ============================================================
# Helper Functions for Downstream Tasks
# ============================================================


def get_sentence_classifications(chunk: ContentFragment) -> List[dict]:
    """
    Get sentence classifications from chunk metadata.

    Args:
        chunk: ContentFragment

    Returns:
        List of classification dicts, or empty list if not available
    """
    return chunk.metadata.get("sentence_classifications", [])


def has_v2_routing(chunk: ContentFragment) -> bool:
    """
    Check if chunk has sentence-level routing.

    Note:
        Function name 'has_v2_routing' preserved for backward compatibility.

    Args:
        chunk: ContentFragment

    Returns:
        True if sentence-level routing is present
    """
    return "sentence_classifications" in chunk.metadata


def get_episodic_sentences(chunk: ContentFragment) -> List[dict]:
    """
    Get only episodic sentences from chunk.

    Args:
        chunk: ContentFragment

    Returns:
        List of episodic sentence classifications
    """
    classifications = get_sentence_classifications(chunk)
    return [c for c in classifications if c.get("routing_type") == "episodic"]


def get_atomic_sentences(chunk: ContentFragment) -> List[dict]:
    """
    Get only atomic sentences from chunk.

    Args:
        chunk: ContentFragment

    Returns:
        List of atomic sentence classifications
    """
    classifications = get_sentence_classifications(chunk)
    return [c for c in classifications if c.get("routing_type") == "atomic"]


def group_by_event(classifications: List[dict]) -> dict:
    """
    Group episodic sentences by event_id.

    NOTE: This function only processes EPISODIC sentences.
    For processing ALL sentences (episodic + atomic), use group_all_events().

    Args:
        classifications: List of sentence classifications

    Returns:
        Dict mapping event_id → {"sentences": [...], "topic": "..."}
    """
    groups = {}

    for c in classifications:
        if c.get("routing_type") != "episodic":
            continue

        event_id = c.get("event_id")
        if not event_id:
            continue

        if event_id not in groups:
            groups[event_id] = {
                "sentences": [],
                "topic": c.get("event_topic", ""),
            }
        groups[event_id]["sentences"].append(c["text"])

    return groups


def group_all_events(classifications: List[dict]) -> dict:
    """
    Group ALL sentences by event_id (both episodic AND atomic).

    Different from group_by_event (only handles episodic), this function handles all types.
    Used for Event-Level Sections functionality.

    Args:
        classifications: List of sentence classifications

    Returns:
        Dict mapping event_id → {
            "sentences": [...],
            "topic": "...",
            "routing_type": "episodic" | "atomic"
        }
    """
    groups = {}

    for c in classifications:
        event_id = c.get("event_id")
        if not event_id:
            continue

        if event_id not in groups:
            groups[event_id] = {
                "sentences": [],
                "topic": c.get("event_topic", ""),
                "routing_type": c.get("routing_type", "episodic"),
            }

        text = c.get("text", "")
        if text:
            groups[event_id]["sentences"].append(text)

    return groups
