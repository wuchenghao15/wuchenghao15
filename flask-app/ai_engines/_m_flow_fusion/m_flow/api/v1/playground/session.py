"""Playground session management — short-term memory buffer + long-term flush."""

from __future__ import annotations

import asyncio
import time
import uuid as _uuid_mod
from dataclasses import dataclass, field
from uuid import UUID

import tiktoken

from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)

_enc = tiktoken.get_encoding("cl100k_base")

# In-memory session store (keyed by session_id)
_sessions: dict[str, PlaygroundSession] = {}


def _count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def _to_uuid(val: str) -> UUID:
    """Safely convert a string dataset_id to UUID object."""
    return UUID(val) if not isinstance(val, UUID) else val


@dataclass
class FlushResult:
    ok: bool
    episodes_created: int = 0
    datasets_affected: list[str] = field(default_factory=list)
    tokens_flushed: int = 0
    turns_flushed: int = 0
    error: str | None = None


@dataclass
class PlaygroundSession:
    session_id: str
    face_recognition_url: str
    user_id: str = ""
    created_at: float = field(default_factory=time.time)

    messages: list[dict] = field(default_factory=list)
    buffer_tokens: int = 0
    buffer_turns: int = 0

    flush_token_threshold: int = 2000
    flush_turn_threshold: int = 10

    # {face_registered_id: [dataset_id_str, ...]}
    face_dataset_mapping: dict[int, list[str]] = field(default_factory=dict)
    # {face_registered_id: display_name} — populated by face_bridge / link-face
    face_name_mapping: dict[int, str] = field(default_factory=dict)
    participants: set[int] = field(default_factory=set)
    # ALL faces ever seen in frame during this session (for flush to all datasets)
    all_seen_faces: set[int] = field(default_factory=set)

    # Per-session LLM override (None = use global .env config)
    llm_model_override: str | None = None
    llm_endpoint_override: str | None = None
    llm_api_key_override: str | None = None

    # Tracks messages in current buffer window (indices into self.messages)
    _buffer_start_idx: int = 0
    _flush_in_progress: bool = False
    _last_flush_time: float = 0.0
    _total_flushes: int = 0
    _flush_retry_count: int = 0
    _max_flush_retries: int = 3
    # Strong references to background memorize tasks to prevent GC
    _background_tasks: set = field(default_factory=set)
    # Dataset UUIDs currently being memorized (prevent concurrent memorize on same dataset)
    _memorizing_datasets: set = field(default_factory=set)

    def add_message(self, role: str, content: str, speaker_face_id: int | None = None):
        self.messages.append(
            {
                "role": role,
                "content": content,
                "speaker_face_id": speaker_face_id,
                "timestamp": time.time(),
            }
        )
        # Count only user messages as "turns" (1 turn = 1 user message).
        # Both user and assistant contribute to token count.
        if role == "user":
            self.buffer_turns += 1
        if role in ("user", "assistant"):
            self.buffer_tokens += _count_tokens(content)
        if speaker_face_id is not None:
            self.participants.add(speaker_face_id)

    def should_flush(self) -> bool:
        if self._flush_in_progress:
            return False
        return self.buffer_tokens >= self.flush_token_threshold or self.buffer_turns >= self.flush_turn_threshold

    def get_recent_messages(self, max_turns: int = 20) -> list[dict]:
        recent = [m for m in self.messages if m["role"] in ("user", "assistant")]
        return recent[-max_turns:]

    def _get_buffer_messages(self) -> list[dict]:
        """Return messages in the current unflushed buffer window."""
        return self.messages[self._buffer_start_idx :]

    def _format_episode_text(self, buffer_msgs: list[dict]) -> str:
        """Format buffered messages into an episode transcript."""
        lines: list[str] = []
        for m in buffer_msgs:
            if m["role"] == "system":
                continue
            fid = m.get("speaker_face_id")
            if m["role"] == "user" and fid is not None:
                name = self._resolve_speaker_name(fid)
                lines.append(f"[{name}] {m['content']}")
            elif m["role"] == "user":
                lines.append(f"[User] {m['content']}")
            else:
                lines.append(f"[AI] {m['content']}")
        return "\n".join(lines)

    def _format_participant_summary(self, buffer_msgs: list[dict], participant_fid: int) -> str:
        """Create a short summary for a secondary participant."""
        name = self._resolve_speaker_name(participant_fid)
        main_topics: list[str] = []
        for m in buffer_msgs:
            if m.get("speaker_face_id") == participant_fid and m["role"] == "user":
                main_topics.append(m["content"][:80])
        topics_str = "; ".join(main_topics[:3]) if main_topics else "(listener)"
        all_names = {self._resolve_speaker_name(fid) for fid in self.participants if fid is not None}
        participants_str = ", ".join(sorted(all_names)) or "unknown participants"
        return f"{name} participated in a conversation. Participants: {participants_str}. {name} said: {topics_str}"

    def _resolve_speaker_name(self, face_id: int) -> str:
        """Resolve face_id to a human-readable name."""
        name = self.face_name_mapping.get(face_id)
        if name:
            return name
        return f"User#{face_id}"

    async def flush_to_long_term(self, user=None) -> FlushResult:
        """Pack the buffer into episodes and push to M-Flow long-term memory.

        Two-step process per the plan:
        1. add() — raw content ingestion (creates Data records)
        2. memorize() — generates searchable Episode/Facet/Entity + vectors
        memorize runs async to not block the conversation.
        """
        if self._flush_in_progress:
            return FlushResult(ok=False, error="Flush already in progress")

        buffer_msgs = self._get_buffer_messages()
        conv_msgs = [m for m in buffer_msgs if m["role"] in ("user", "assistant")]
        if not conv_msgs:
            return FlushResult(ok=False, error="No messages to flush")

        self._flush_in_progress = True
        tokens_to_flush = self.buffer_tokens
        turns_to_flush = self.buffer_turns

        try:
            from m_flow import add as m_flow_add

            episode_text = self._format_episode_text(conv_msgs)
            datasets_affected: list[str] = []
            datasets_to_memorize_uuids: list[UUID] = []
            pushed_datasets: set[str] = set()

            # Collect ALL unique datasets from every face that ever appeared in this session
            all_ds_ids: list[str] = []
            for fid in self.all_seen_faces:
                for ds_id in self.face_dataset_mapping.get(fid, []):
                    if ds_id not in pushed_datasets:
                        pushed_datasets.add(ds_id)
                        all_ds_ids.append(ds_id)
            # Also check -1 (anonymous) fallback
            for ds_id in self.face_dataset_mapping.get(-1, []):
                if ds_id not in pushed_datasets:
                    pushed_datasets.add(ds_id)
                    all_ds_ids.append(ds_id)
            # Last resort: any mapped dataset
            if not all_ds_ids:
                for ds_list in self.face_dataset_mapping.values():
                    for ds_id in ds_list:
                        if ds_id not in pushed_datasets:
                            pushed_datasets.add(ds_id)
                            all_ds_ids.append(ds_id)

            # Push full transcript to ALL collected datasets
            for ds_id_str in all_ds_ids:
                try:
                    ds_uuid = _to_uuid(ds_id_str)
                    await m_flow_add(episode_text, dataset_id=ds_uuid, user=user)
                    datasets_affected.append(ds_id_str)
                    datasets_to_memorize_uuids.append(ds_uuid)
                except Exception as e:
                    _log.error(f"add() failed for dataset {ds_id_str}: {e}")

            if not datasets_affected:
                _log.warning(f"Session {self.session_id}: no datasets mapped, buffer preserved")
                return FlushResult(
                    ok=False,
                    error="No datasets linked to current participants — buffer preserved",
                    tokens_flushed=0,
                    turns_flushed=0,
                )

            # Immediately advance buffer and reset counts to prevent:
            # 1. Duplicate add() on re-Save (buffer_start moved past flushed messages)
            # 2. Excessive auto-flush triggers (counts reset, new messages start from 0)
            self._buffer_start_idx = len(self.messages)
            self.buffer_tokens = 0
            self.buffer_turns = 0
            self.participants.clear()

            # Launch memorize in background — skip datasets already being memorized
            unique_memorize_uuids = list(dict.fromkeys(datasets_to_memorize_uuids))
            pending = [u for u in unique_memorize_uuids if str(u) not in self._memorizing_datasets]
            if pending:
                for u in pending:
                    self._memorizing_datasets.add(str(u))
                snapshot = {"tokens": tokens_to_flush, "turns": turns_to_flush}
                task = asyncio.create_task(self._memorize_then_clear(pending, user, snapshot))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            elif unique_memorize_uuids:
                _log.info(
                    f"Session {self.session_id}: memorize skipped — already in progress for {unique_memorize_uuids}"
                )

            _log.info(
                f"Session {self.session_id}: add() done for {tokens_to_flush} tokens, "
                f"{turns_to_flush} turns → {len(datasets_affected)} datasets; memorize pending"
            )

            return FlushResult(
                ok=True,
                episodes_created=len(datasets_affected),
                datasets_affected=datasets_affected,
                tokens_flushed=tokens_to_flush,
                turns_flushed=turns_to_flush,
            )

        except Exception as e:
            _log.error(f"flush_to_long_term failed: {e}")
            self._schedule_flush_retry(user)
            return FlushResult(ok=False, error=str(e))

        finally:
            self._flush_in_progress = False

    async def _memorize_then_clear(self, dataset_uuids: list[UUID], user, snapshot: dict):
        """Run memorize in background. Buffer already cleared after add()."""
        try:
            from m_flow import memorize as m_flow_memorize

            await m_flow_memorize(datasets=dataset_uuids, user=user, run_in_background=False)
            self._last_flush_time = time.time()
            self._total_flushes += 1
            _log.info(f"Session {self.session_id}: memorize completed for {dataset_uuids}")
        except Exception as e:
            _log.error(
                f"Session {self.session_id}: memorize failed for {dataset_uuids}: {e} "
                f"— data already ingested via add(), retry memorize from Build Graph page"
            )
        finally:
            for u in dataset_uuids:
                self._memorizing_datasets.discard(str(u))

    def _schedule_flush_retry(self, user=None):
        """Schedule a background retry for failed flush with exponential backoff."""
        if self._flush_retry_count >= self._max_flush_retries:
            _log.warning(
                f"Session {self.session_id}: max flush retries ({self._max_flush_retries}) "
                f"exhausted, buffer preserved for manual flush"
            )
            return

        self._flush_retry_count += 1
        delay = 2**self._flush_retry_count
        _log.info(f"Session {self.session_id}: scheduling flush retry #{self._flush_retry_count} in {delay}s")

        async def _retry():
            await asyncio.sleep(delay)
            result = await self.flush_to_long_term(user=user)
            if result.ok:
                self._flush_retry_count = 0
                _log.info(f"Session {self.session_id}: flush retry succeeded")

        task = asyncio.create_task(_retry())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)


def create_session(face_recognition_url: str, user_id: str = "") -> PlaygroundSession:
    sid = f"pg_{_uuid_mod.uuid4().hex[:12]}"
    session = PlaygroundSession(session_id=sid, face_recognition_url=face_recognition_url, user_id=user_id)
    _sessions[sid] = session
    _log.info(f"Playground session created: {sid} for user {user_id}")
    return session


def get_session(session_id: str, user_id: str = "") -> PlaygroundSession | None:
    session = _sessions.get(session_id)
    if session and user_id and session.user_id != user_id:
        return None
    return session
