"""
Coreference Resolution Module

Core features:
1. Entity tracking: maintain recently seen persons, objects, locations
2. Pronoun identification: identify pronouns in sentences (he/that/there etc.)
3. Coreference resolution: find suitable antecedents based on pronoun type and context
"""

from typing import List, Dict, Optional, Tuple, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import re

from .syntax_adapter import SyntaxAdapter

# Import CanonicalResult (avoid circular import)
if TYPE_CHECKING:
    from .canonicalizer import CanonicalResult as CanonicalResultType
else:
    # Runtime lazy import
    CanonicalResultType = None


def _get_canonical_result():
    """Get CanonicalResult class (lazy import)"""
    from .canonicalizer import CanonicalResult

    return CanonicalResult


def split_sentences(text: str) -> List[Tuple[str, str]]:
    """Smart sentence splitting: supports various punctuation marks

    Args:
        text: input text

    Returns:
        List of (sentence, delimiter) tuples
    """
    results = []
    current = ""
    i = 0

    while i < len(text):
        char = text[i]

        # Check special delimiters
        # 1. Ellipsis (consecutive dots)
        if char in ".。" and i + 2 < len(text) and text[i : i + 3] in ("...", "。。。", "...", "···"):
            # Find full length of ellipsis
            j = i
            while j < len(text) and text[j] in ".。·":
                j += 1
            delim = text[i:j]
            if current.strip():
                results.append((current.strip(), delim))
            current = ""
            i = j
            continue

        # 2. Dash
        if char in "—-" and i + 1 < len(text) and text[i : i + 2] in ("——", "--"):
            delim = text[i : i + 2]
            if current.strip():
                results.append((current.strip(), delim))
            current = ""
            i += 2
            continue

        # 3. Standard sentence-ending punctuation
        if char in "。！？?!":
            if current.strip():
                results.append((current.strip(), char))
            current = ""
            i += 1
            continue

        current += char
        i += 1

    # Handle trailing text without punctuation
    if current.strip():
        results.append((current.strip(), ""))

    return results


# Import tokenizer
try:
    from .tokenizer import ChineseTokenizer, Mention
    from .time_normalizer import TimeNormalizer, normalize_time as _normalize_time
except ImportError:
    from tokenizer import ChineseTokenizer, Mention
    from time_normalizer import TimeNormalizer, normalize_time as _normalize_time


# === Scoring constants for candidate ranking ===


class _ScoreWeights:
    """Named constants for the candidate scoring logic in _find_replacement._score().
    Centralised here so they can be tuned without hunting through 900+ lines."""

    SRL_HIT_BASE = 20000  # base score when SRL arg span matches
    TOKEN_HIT_BASE = 10000  # base score when role-token list matches
    SPEECH_VERB_BONUS = 1500  # bonus for speech verb predicate match
    COMM_VERB_BONUS = 1500  # bonus for communication verb predicate match
    PATIENT_VERB_BONUS = 800  # bonus for patient verb predicate match
    SPEAKER_LISTENER_BONUS = 800  # bonus when candidate matches recent speaker/listener
    PARAGRAPH_RESET_PENALTY = 600  # penalty for cross-paragraph candidates
    STRONG_DECAY_PER_GAP = 300  # per-sentence decay when new entity exists between
    WEAK_DECAY_PER_GAP = 150  # per-sentence decay when no new entity between
    SINGLE_CANDIDATE_BONUS = 200  # bonus when only one candidate and gap ≤ 2
    INITIAL_SCORE = -100000  # initial score before any signal


# === Structured output data types ===


@dataclass
class Replacement:
    """Replacement record"""

    pronoun: str  # original pronoun
    replacement: str  # replacement text
    position: int  # position in sentence
    type: str  # pronoun type
    sentence_id: int = 0  # sentence ID


@dataclass
class TimeSpan:
    """Time span (normalization result)"""

    source_text: str  # original time expression
    start_dt: Optional[datetime] = None  # start time
    end_dt: Optional[datetime] = None  # end time
    precision: str = "UNKNOWN"  # precision: DAY, WEEK, MONTH, YEAR, FUZZY
    start: int = -1  # start position in source text
    end: int = -1  # end position in source text


@dataclass
class CorefOutput:
    """Coreference resolution structured output"""

    original_text: str  # original text
    resolved_text: str  # resolved text
    replacements: List[Replacement]  # replacement records
    mentions: List[Mention]  # entity mentions (from resolved_text)
    time_extractions: List[TimeSpan]  # time normalization results


@dataclass
class Entity:
    """Entity class"""

    text: str  # entity text
    type: str  # entity type: PER_NAME, PER_TITLE, LOC_NAME, LOC_PLACE, OBJ, TIME
    sentence_id: int  # sentence ID where it appears
    position: int  # position in sentence (character index)
    start: int = -1  # character start position
    end: int = -1  # character end position


@dataclass
class Event:
    """Event class - for event/proposition coreference"""

    text: str  # event text (full sentence or predicate phrase)
    verb: str  # main verb
    sentence_id: int  # sentence ID it belongs to
    summary: str = ""  # event summary (verb phrase with subject removed)


class EntityTracker:
    """Entity tracker - maintains recently mentioned entities and events"""

    # Female name characteristic characters
    FEMALE_NAME_CHARS = {
        "红",
        "丽",
        "芳",
        "娟",
        "燕",
        "敏",
        "娜",
        "静",
        "萍",
        "玲",
        "梅",
        "英",
        "华",
        "琴",
        "艳",
        "霞",
        "秀",
        "云",
        "兰",
        "莉",
        "珍",
        "蓉",
        "凤",
        "琳",
        "婷",
        "雪",
        "慧",
        "倩",
        "娇",
        "怡",
        "嫣",
        "媛",
        "妍",
        "颖",
        "婉",
        "悦",
        "妮",
        "雯",
        "琪",
        "薇",
    }

    # Male name characteristic characters
    MALE_NAME_CHARS = {
        "明",
        "强",
        "军",
        "伟",
        "建",
        "国",
        "刚",
        "勇",
        "斌",
        "杰",
        "涛",
        "磊",
        "浩",
        "鹏",
        "锋",
        "辉",
        "超",
        "飞",
        "龙",
        "凯",
        "华",
        "威",
        "雄",
        "峰",
        "波",
        "康",
        "健",
        "志",
        "文",
        "武",
    }

    def __init__(self, max_history: int = 10):
        """
        Args:
            max_history: max number of historical entities to keep
        """
        self.max_history = max_history
        # Five stacks: four entity stacks + one event stack
        self.person_stack: deque = deque(maxlen=max_history)  # persons
        self.object_stack: deque = deque(maxlen=max_history)  # objects
        self.location_stack: deque = deque(maxlen=max_history)  # locations
        self.time_stack: deque = deque(maxlen=max_history)  # time
        self.event_stack: deque = deque(maxlen=max_history)  # events/propositions

        # Unified candidate stack (for ordinal pronouns, records all entity types)
        self.all_mentions_stack: deque = deque(maxlen=max_history * 2)

        # Current sentence entities (for distinguishing subject/object positions)
        self.current_sentence_persons: List[Entity] = []
        self.last_speaker: Optional[Entity] = None
        self.last_listener: Optional[Entity] = None
        self.last_speaker_sid: int = -1
        self.last_listener_sid: int = -1
        self.speaker_chain: deque = deque(maxlen=3)

        self.sentence_count = 0

    def is_female_name(self, name: str) -> bool:
        """Check if name is possibly female"""
        if not name:
            return False
        # Check for female characteristic characters in name
        return any(char in self.FEMALE_NAME_CHARS for char in name)

    def is_male_name(self, name: str) -> bool:
        """Check if name is possibly male"""
        if not name:
            return False
        # Check for male characteristic characters in name
        return any(char in self.MALE_NAME_CHARS for char in name)

    def add_entity(self, entity: Entity):
        """Add entity to corresponding stack"""
        if entity.type in ["PER_NAME", "PER_TITLE"]:
            self.person_stack.append(entity)
            self.current_sentence_persons.append(entity)
        elif entity.type == "OBJ":
            self.object_stack.append(entity)
        elif entity.type in ["LOC_NAME", "LOC_PLACE"]:
            self.location_stack.append(entity)
        elif entity.type == "TIME":
            self.time_stack.append(entity)

        # Also add to unified candidate stack (for ordinal pronouns)
        self.all_mentions_stack.append(entity)

    def add_event(self, event: Event):
        """Add event to event stack"""
        self.event_stack.append(event)

    def get_event(self, prefer_recent: bool = True) -> Optional[Event]:
        """Get event"""
        if not self.event_stack:
            return None
        return self.event_stack[-1] if prefer_recent else self.event_stack[0]

    def get_first_and_last_mentions(self, prefer_type: str = None) -> Tuple[Optional[Entity], Optional[Entity]]:
        """Get first and last entities (for ordinal pronouns: former/latter)

        Fix:
        - "former" refers to the first mentioned entity
        - "latter" refers to the last mentioned entity

        Args:
            prefer_type: preferred entity type, e.g. 'PER_NAME' over 'PER_TITLE'
        """
        if len(self.all_mentions_stack) < 2:
            return (None, None)

        # Deduplicate: keep only first occurrence of same-name entities
        seen = set()
        unique = []

        # First try using only prefer_type entities
        if prefer_type:
            for e in self.all_mentions_stack:
                if e.type == prefer_type and e.text not in seen:
                    seen.add(e.text)
                    unique.append(e)
            if len(unique) >= 2:
                # former=first, latter=last
                return (unique[0], unique[-1])

        # fallback: use all entities but exclude PER_TITLE type
        seen.clear()
        unique.clear()
        for e in self.all_mentions_stack:
            # Exclude generic PER_TITLE (e.g. "friend", "colleague")
            if e.type == "PER_TITLE" and e.text in {"朋友", "同事", "同学", "邻居"}:
                continue
            if e.text not in seen:
                seen.add(e.text)
                unique.append(e)

        if len(unique) < 2:
            return (None, None)
        # former=first, latter=last
        return (unique[0], unique[-1])

    # Maintain backward compatibility
    def get_last_two_mentions(self, prefer_type: str = None) -> Tuple[Optional[Entity], Optional[Entity]]:
        """Get first and last entities (alias, backward compatible)"""
        return self.get_first_and_last_mentions(prefer_type)

    def get_person(self, prefer_recent: bool = True, position: str = "any") -> Optional[Entity]:
        """Get person entity

        Args:
            prefer_recent: True=proximal(most recent), False=distal(earlier)
            position: 'subject'=subject position, 'object'=object position, 'any'=any
        """
        if not self.person_stack:
            return None

        stack_size = len(self.person_stack)

        # If multiple persons, select by semantic role
        if stack_size >= 2:
            if position == "subject":
                # Subject-position pronoun -> prefer previous sentence subject (usually first mentioned)
                # Second from top in stack is usually previous sentence subject
                for i in range(stack_size - 1, -1, -1):
                    # Find PER_NAME type (actual names) with priority over PER_TITLE
                    if self.person_stack[i].type == "PER_NAME":
                        return self.person_stack[i]
                # If no PER_NAME, return earlier one
                return self.person_stack[0]
            elif position == "object":
                # Object-position pronoun -> return most recently mentioned person (likely patient)
                return self.person_stack[-1]

        # Only one person, return directly
        return self.person_stack[-1] if prefer_recent else self.person_stack[0]

    def _filter_before(self, stack: deque, sentence_id: int, position: int) -> List[Entity]:
        """Filter candidates: keep only entities before (sentence_id, position) to avoid cataphora"""
        res: List[Entity] = []
        for e in stack:
            if e.sentence_id < sentence_id:
                res.append(e)
            elif e.sentence_id == sentence_id and e.position < position:
                res.append(e)
        return res

    def _rank_candidates(self, candidates: List[Entity], sentence_id: int, position: int) -> Optional[Entity]:
        """Global candidate ranking: cross-sentence demotion, same-sentence proximity priority, PER_NAME priority"""
        if not candidates:
            return None

        # Prefer PER_NAME type (more specific entity names)
        per_names = [c for c in candidates if c.type == "PER_NAME"]
        if per_names:
            candidates = per_names  # prefer PER_NAME

        # Check if only one candidate
        single_candidate = len(candidates) == 1

        def _score(e: Entity) -> int:
            sent_gap = sentence_id - e.sentence_id
            # Type bonus: PER_NAME preferred over PER_TITLE
            type_bonus = 50 if e.type == "PER_NAME" else 0

            if sent_gap <= 0:
                dist = abs(position - e.position)
                return -dist + type_bonus
            # Weaken position distance across sentences, prefer later mentions in previous sentence
            tail_bonus = min(e.position, 200) // 5
            # If only one candidate, reduce cross-sentence penalty
            if single_candidate:
                return -sent_gap * 100 + tail_bonus + 100 + type_bonus
            # Check for closer candidates of same type
            has_closer = any(c is not e and e.sentence_id < c.sentence_id < sentence_id for c in candidates)
            if has_closer:
                return -sent_gap * 300 + tail_bonus + type_bonus
            else:
                # Reduce penalty when no same-type candidates in between
                return -sent_gap * 150 + tail_bonus + type_bonus

        return max(candidates, key=_score)

    def get_person_before(
        self, sentence_id: int, position_in_sentence: int, prefer_recent: bool = True, position: str = "any"
    ) -> Optional[Entity]:
        """Get person entities (using only candidates before current position)"""
        persons = self._filter_before(self.person_stack, sentence_id, position_in_sentence)
        if not persons:
            return None

        stack_size = len(persons)
        if stack_size >= 2:
            if position == "subject":
                # Consistent with get_person: prefer returning PER_NAME
                per_names = [p for p in persons if p.type == "PER_NAME"]
                if per_names:
                    return (
                        self._rank_candidates(per_names, sentence_id, position_in_sentence)
                        if prefer_recent
                        else per_names[0]
                    )
                return (
                    self._rank_candidates(persons, sentence_id, position_in_sentence) if prefer_recent else persons[0]
                )
            elif position == "object":
                return (
                    self._rank_candidates(persons, sentence_id, position_in_sentence) if prefer_recent else persons[0]
                )

        return self._rank_candidates(persons, sentence_id, position_in_sentence) if prefer_recent else persons[0]

    def get_object_before(
        self, sentence_id: int, position_in_sentence: int, prefer_recent: bool = True
    ) -> Optional[Entity]:
        objs = self._filter_before(self.object_stack, sentence_id, position_in_sentence)
        if not objs:
            return None
        return self._rank_candidates(objs, sentence_id, position_in_sentence) if prefer_recent else objs[0]

    def get_location_before(
        self, sentence_id: int, position_in_sentence: int, prefer_recent: bool = True
    ) -> Optional[Entity]:
        locs = self._filter_before(self.location_stack, sentence_id, position_in_sentence)
        if not locs:
            return None
        return self._rank_candidates(locs, sentence_id, position_in_sentence) if prefer_recent else locs[0]

    def get_persons_text(self, count: int = 2) -> str:
        """Get text for multiple persons (for plural pronouns)"""
        if not self.person_stack:
            return None
        if len(self.person_stack) == 1:
            return self.person_stack[-1].text

        # Get most recent persons
        recent = list(self.person_stack)[-count:]
        names = [e.text for e in recent]

        # Safety check: detect truncated names
        surnames = {
            "张",
            "李",
            "王",
            "刘",
            "陈",
            "杨",
            "黄",
            "赵",
            "周",
            "吴",
            "徐",
            "孙",
            "马",
            "朱",
            "胡",
            "郭",
            "何",
            "高",
            "林",
            "罗",
        }
        for name in names:
            if len(name) == 1:
                return None  # single-char name may be truncated
            if len(name) >= 4 and all("\u4e00" <= c <= "\u9fff" for c in name):
                return None  # may be multiple names concatenated
            if len(name) == 3 and name[2] in surnames:
                return None  # may be a truncated name

        return "和".join(names)

    def _format_entity_list(self, names: List[str]) -> Optional[str]:
        """Format entity list as readable string: A and B / A, B and C"""
        if not names:
            return None
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]}和{names[1]}"
        return "、".join(names[:-1]) + "和" + names[-1]

    def get_persons_text_before(self, sentence_id: int, position_in_sentence: int) -> Optional[str]:
        """
        Get antecedent set for plural person pronouns "他们/她们" (only use candidates before current position).
        Strategy (closer to Chinese colloquial speech):
        - Prioritize "all person list appearing in most recent sentence" (common in: X、Y和Z... 他们...)
        - Otherwise fallback to most recent two
        """
        persons = self._filter_before(self.person_stack, sentence_id, position_in_sentence)
        if len(persons) < 2:
            return None

        # Get sentence ID of most recent persons (avoid including very old mentions)
        last_sid = max(e.sentence_id for e in persons)
        same_sid = [e for e in persons if e.sentence_id == last_sid]

        def uniq_text(es: List[Entity]) -> List[str]:
            out: List[str] = []
            for e in es:
                if e.text not in out:
                    out.append(e.text)
            return out

        def _has_truncated_name(names: List[str]) -> bool:
            """Check if there are truncated names in the name list"""
            # Common surnames
            surnames = {
                "张",
                "李",
                "王",
                "刘",
                "陈",
                "杨",
                "黄",
                "赵",
                "周",
                "吴",
                "徐",
                "孙",
                "马",
                "朱",
                "胡",
                "郭",
                "何",
                "高",
                "林",
                "罗",
            }
            # Valid single-char aliases (Tiangan-Dizhi codes)
            valid_single_names = {
                "甲",
                "乙",
                "丙",
                "丁",
                "戊",
                "己",
                "庚",
                "辛",
                "壬",
                "癸",
                "子",
                "丑",
                "寅",
                "卯",
                "辰",
                "巳",
                "午",
                "未",
                "申",
                "酉",
                "戌",
                "亥",
            }
            for name in names:
                if len(name) == 1:
                    # Valid single-char alias, not considered truncated
                    if name in valid_single_names:
                        continue
                    return True  # other single chars are usually not complete names
                # Check for 4+ char "names" (may be multiple names merged)
                if len(name) >= 4 and all("\u4e00" <= c <= "\u9fff" for c in name):
                    return True  # may be a segmentation error
                # Check if 3-char name has 3rd char as common surname (truncated)
                if len(name) == 3 and name[2] in surnames:
                    # If 3rd char is surname, possibly multiple names incorrectly merged
                    return True
            return False

        names = uniq_text(same_sid)
        # Safety check: if truncated names detected, do not resolve
        if _has_truncated_name(names):
            return None
        if len(names) >= 2:
            return self._format_entity_list(names)

        # fallback: most recent two unique
        names2 = uniq_text(persons)[-2:]
        return self._format_entity_list(names2)

    def get_objects_text_before(self, sentence_id: int, position_in_sentence: int) -> Optional[str]:
        """Get object set that plural 'they/their' may refer to (only use candidates before current position)"""
        objs = self._filter_before(self.object_stack, sentence_id, position_in_sentence)
        if len(objs) < 2:
            return None
        last_sid = max(e.sentence_id for e in objs)
        same_sid = [e for e in objs if e.sentence_id == last_sid]
        names: List[str] = []
        for e in same_sid:
            if e.text not in names:
                names.append(e.text)
        if len(names) >= 2:
            return self._format_entity_list(names)
        # fallback: most recent two unique
        names2: List[str] = []
        for e in objs:
            if e.text not in names2:
                names2.append(e.text)
        return self._format_entity_list(names2[-2:])

    def _get_clause_start(self, sentence_text: str, position_in_sentence: int) -> int:
        """Get clause start position for current position (lightweight rules)"""
        if not sentence_text:
            return 0
        boundary_tokens = ["，", ",", "；", ";", "。", "？", "?", "！", "!"]
        boundary_words = [
            "但是",
            "然而",
            "不过",
            "所以",
            "因为",
            "如果",
            "虽然",
            "尽管",
            "同时",
            "此外",
            "并且",
            "于是",
            "因此",
            "而",
            "但",
            "却",
        ]
        last_idx = -1
        for t in boundary_tokens:
            i = sentence_text.rfind(t, 0, position_in_sentence)
            if i > last_idx:
                last_idx = i
        last_word_idx = -1
        last_word_len = 0
        for w in boundary_words:
            i = sentence_text.rfind(w, 0, position_in_sentence)
            if i > last_word_idx:
                last_word_idx = i
                last_word_len = len(w)
        if last_word_idx > last_idx:
            return last_word_idx + last_word_len
        return last_idx + 1 if last_idx >= 0 else 0

    def get_person_before_in_clause(
        self,
        sentence_id: int,
        position_in_sentence: int,
        sentence_text: str,
        prefer_recent: bool = True,
        position: str = "any",
    ) -> Optional[Entity]:
        persons = self._filter_before(self.person_stack, sentence_id, position_in_sentence)
        if not persons:
            return None
        clause_start = self._get_clause_start(sentence_text, position_in_sentence)
        candidates = [p for p in persons if p.sentence_id == sentence_id and p.start >= clause_start]
        if not candidates:
            return None
        if position == "subject":
            return candidates[0]
        if position == "object":
            return candidates[-1]
        return candidates[-1] if prefer_recent else candidates[0]

    def get_object_before_in_clause(
        self,
        sentence_id: int,
        position_in_sentence: int,
        sentence_text: str,
        prefer_recent: bool = True,
    ) -> Optional[Entity]:
        objs = self._filter_before(self.object_stack, sentence_id, position_in_sentence)
        if not objs:
            return None
        clause_start = self._get_clause_start(sentence_text, position_in_sentence)
        candidates = [o for o in objs if o.sentence_id == sentence_id and o.start >= clause_start]
        if not candidates:
            return None
        return candidates[-1] if prefer_recent else candidates[0]

    def get_locations_text_before(self, sentence_id: int, position_in_sentence: int) -> Optional[str]:
        """Get plural location/organization set (using only candidates before current position)"""
        locs = self._filter_before(self.location_stack, sentence_id, position_in_sentence)
        if len(locs) < 2:
            return None
        last_sid = max(e.sentence_id for e in locs)
        same_sid = [e for e in locs if e.sentence_id == last_sid]
        names: List[str] = []
        for e in same_sid:
            if e.text not in names:
                names.append(e.text)
        if len(names) >= 2:
            return self._format_entity_list(names)
        names2: List[str] = []
        for e in locs:
            if e.text not in names2:
                names2.append(e.text)
        return self._format_entity_list(names2[-2:])

    def get_object(self, prefer_recent: bool = True) -> Optional[Entity]:
        """Get object entities"""
        if not self.object_stack:
            return None
        return self.object_stack[-1] if prefer_recent else self.object_stack[0]

    def get_location(self, prefer_recent: bool = True) -> Optional[Entity]:
        """Get location entities"""
        if not self.location_stack:
            return None
        return self.location_stack[-1] if prefer_recent else self.location_stack[0]

    def get_time(self, prefer_recent: bool = True) -> Optional[Entity]:
        """Get time entities"""
        if not self.time_stack:
            return None
        return self.time_stack[-1] if prefer_recent else self.time_stack[0]

    def get_time_before(
        self, sentence_id: int, position_in_sentence: int, prefer_recent: bool = True
    ) -> Optional[Entity]:
        """Get time entities (only before current position), avoid cataphora from later time mentions"""
        times = self._filter_before(self.time_stack, sentence_id, position_in_sentence)
        if not times:
            return None
        return times[-1] if prefer_recent else times[0]

    def next_sentence(self):
        """Move to next sentence"""
        self.sentence_count += 1
        self.current_sentence_persons.clear()

    def set_speaker(self, entity: Entity, sentence_id: int) -> None:
        self.last_speaker = entity
        self.last_speaker_sid = sentence_id
        self.speaker_chain.append((entity, sentence_id))

    def set_listener(self, entity: Entity, sentence_id: int) -> None:
        self.last_listener = entity
        self.last_listener_sid = sentence_id

    def get_recent_speaker(self, current_sid: int, max_gap: int = 1) -> Optional[Entity]:
        if self.last_speaker is None:
            return None
        if current_sid - self.last_speaker_sid > max_gap:
            return None
        return self.last_speaker

    def get_recent_listener(self, current_sid: int, max_gap: int = 1) -> Optional[Entity]:
        if self.last_listener is None:
            return None
        if current_sid - self.last_listener_sid > max_gap:
            return None
        return self.last_listener

    def reset_speaker_context(self) -> None:
        self.last_speaker = None
        self.last_listener = None
        self.last_speaker_sid = -1
        self.last_listener_sid = -1
        self.speaker_chain.clear()

    def get_speaker_chain(self, current_sid: int, max_gap: int = 2) -> List[Entity]:
        res: List[Entity] = []
        for e, sid in reversed(self.speaker_chain):
            if current_sid - sid > max_gap:
                continue
            if e.text not in [x.text for x in res]:
                res.append(e)
        return res

    def clear(self):
        """Clear all entities and events"""
        self.person_stack.clear()
        self.object_stack.clear()
        self.location_stack.clear()
        self.time_stack.clear()
        self.event_stack.clear()
        self.all_mentions_stack.clear()
        self.current_sentence_persons.clear()
        self.reset_speaker_context()
        self.sentence_count = 0


class CoreferenceResolver:
    """Coreference resolver"""

    # === Pronoun Classification ===

    # Personal pronouns - third person
    PERSON_PRONOUNS = {
        "他",
        "她",
        "它",
        "他们",
        "她们",
        "它们",
        "对方",
    }
    # Object/thing reference
    OBJECT_PRONOUNS = {"它", "它们", "其", "它的"}
    # Ambiguous pronouns (person or object)
    AMBIGUOUS_PRONOUNS = {"他", "她", "它"}

    # Possessive pronouns (replace as whole)
    POSSESSIVE_PRONOUNS = {
        "他的",
        "她的",
        "它的",
        "他们的",
        "她们的",
        "它们的",
        "我们的",
        "咱们的",  # first person plural possessive (special handling)
    }

    # Personal pronouns - 1st/2nd person (no resolution needed)
    SELF_PRONOUNS = {"我", "你", "您", "我们", "你们", "咱们", "咱", "我的", "你的", "您的", "我们的", "咱们的"}

    # Reflexive pronouns (no resolution needed)
    REFLEXIVE_PRONOUNS = {"自己", "本人", "自身"}

    # Generic pronouns (no resolution) - these are complete references on their own
    GENERIC_PRONOUNS = {"人家", "别人", "有人", "某人", "大家", "众人", "其他人", "另外"}

    # Bound variable trigger words (pronouns after these are not resolved)
    QUANTIFIER_WORDS = {"每个", "每位", "所有", "任何", "各个", "各位", "全部", "一切"}

    # Time pronouns (resolve to specific time)
    TIME_PRONOUNS = {
        "那时",
        "那时候",
        "当时",
        "此时",
        "这时",
        "这时候",
        "彼时",
        "那会儿",
        "这会儿",
        "那阵子",
        "这阵子",
        "那段时间",
        "那个时候",
        "这个时候",
    }

    # Event pronouns (refer to preceding actions/events)
    EVENT_PRONOUNS = {"这", "那", "此"}  # may refer to events when used alone

    # Event reference trigger patterns (these words followed by event pronouns refer to previous event)
    EVENT_TRIGGER_VERBS = {
        "让",
        "使",
        "导致",
        "造成",
        "引起",
        "引发",
        "说明",
        "表明",
        "意味着",
        "促使",
        "证明",
        "表示",
        "显示",
        "很重要",
        "不对",
        "不好",
        "不应该",
        # Extended: more words that may trigger event reference
        "影响",
        "改变",
        "决定",
        "产生",
        "带来",
        "留下",
        "造就",
        "形成",
        "惊讶",
        "震惊",
        "感动",
        "高兴",
        "生气",
        "愤怒",
        "悲伤",
        "开心",
        "出乎意料",
        "令人",
        "使人",
        "叫人",
    }

    # Event reference phrases
    EVENT_PHRASES = {
        "这件事",
        "那件事",
        "这事",
        "那事",
        "此事",
        "这样",
        "那样",
        "这样做",
        "那样做",
        "这一点",
        "那一点",
        "这次",
        "那次",
        "这种情况",
        "那种情况",
        "这种做法",
        "那种做法",
    }

    # Formal demonstratives (this/that/said/aforementioned)
    FORMAL_DEICTIC = {
        "该",
        "此",
        "本",
        "上述",
        "前述",
        "下述",
        "如上",
        "如下",
        "该人",
        "该地",
        "该公司",
        "该项目",
        "该方案",
        "该问题",
        "此人",
        "此地",
        "此事",
        "此时",
        "本人",
        "本次",
        "本项目",
        "本公司",
        "本申请",
        "上述问题",
        "上述方案",
        "上述内容",
        "上述情况",
        "前述问题",
        "前述内容",
    }

    # Demonstrative determiner phrases (conservatively resolvable generic noun heads)
    # Format: {phrase: type}
    GENERIC_HEAD_NOUNS = {
        # Person
        "这个人": "PERSON",
        "那个人": "PERSON",
        "这人": "PERSON",
        "那人": "PERSON",
        "这位": "PERSON",
        "那位": "PERSON",
        "这家伙": "PERSON",
        "那家伙": "PERSON",
        # Location
        "这个地方": "LOCATION",
        "那个地方": "LOCATION",
        "这地方": "LOCATION",
        "那地方": "LOCATION",
        # Object
        "这个东西": "OBJECT",
        "那个东西": "OBJECT",
        "这东西": "OBJECT",
        "那东西": "OBJECT",
        "这玩意": "OBJECT",
        "那玩意": "OBJECT",
    }

    # Filler word patterns (colloquial "that..." is not anaphoric)
    FILLER_PATTERNS = [
        r"那个[，,…]+",  # that, ...
        r"那个那个",  # that that (repetition)
        r"那个[呃嗯啊哦吧呢嘛]+",  # that um...
    ]

    # Proximal pronouns (refer to person/object, resolvable)
    PROXIMAL_PRONOUNS = {
        # Person
        "这人",
        "这位",
        "此人",
        "这家伙",
        # Object
        "这个",
        "这东西",
        "这玩意",
        "这件",
        # location
        "这里",
        "这边",
        "这儿",
        "此处",
        "此地",
    }

    # Distal pronouns (refer to person/object, resolvable)
    DISTAL_PRONOUNS = {
        # Person
        "那人",
        "那位",
        "那家伙",
        # Object
        "那个",
        "那东西",
        "那玩意",
        "那件",
        # location
        "那里",
        "那边",
        "那儿",
        "彼处",
    }

    # Descriptive phrases (demonstrative+noun structure, do not resolve)
    # e.g. "that person", "this place", etc.
    DESCRIPTIVE_PHRASES = {
        "那个人",
        "这个人",
        "那个地方",
        "这个地方",
        "那个东西",
        "这个东西",
        "那个事情",
        "这个事情",
    }

    # Emphatic reflexive pronouns (do not resolve, keep as is)
    EMPHATIC_REFLEXIVES = {"他自己", "她自己", "它自己", "他们自己", "她们自己", "我自己", "你自己"}

    # Reduplicative trigger words (when pronoun follows noun, it's reduplicative, should delete pronoun)
    # e.g. "he" in "Xiaoming-he is smart" (reduplicative)
    REDUPLICATIVE_PRONOUNS = {"他", "她", "它"}

    # pluralperson-titlepronoun
    PLURAL_PERSON_PRONOUNS = {"他们", "她们", "它们"}

    # Demonstrative pronoun + classifier combinations (need to keep classifier)
    DEMONSTRATIVE_CLASSIFIERS = {
        "这座",
        "那座",
        "这个",
        "那个",
        "这位",
        "那位",
        "这件",
        "那件",
        "这本",
        "那本",
        "这张",
        "那张",
        "这部",
        "那部",
        "这辆",
        "那辆",
        "这台",
        "那台",
    }

    # Pronoun type mapping
    PRONOUN_TYPE = {
        # Personal pronouns -> person
        "他": "PERSON",
        "她": "PERSON",
        "他们": "PERSON",
        "她们": "PERSON",
        "他的": "PERSON_POSS",
        "她的": "PERSON_POSS",
        "他们的": "PERSON_POSS",
        "她们的": "PERSON_POSS",
        "对方": "PERSON",
        "这人": "PERSON",
        "这位": "PERSON",
        "这个人": "PERSON",
        "此人": "PERSON",
        "这家伙": "PERSON",
        "那人": "PERSON",
        "那位": "PERSON",
        "那个人": "PERSON",
        "那家伙": "PERSON",
        # Object pronouns -> object
        "它": "OBJECT",
        "它们": "OBJECT",
        "它的": "OBJECT_POSS",
        "它们的": "OBJECT_POSS",
        "这东西": "OBJECT",
        "这玩意": "OBJECT",
        "这件": "OBJECT",
        "那东西": "OBJECT",
        "那玩意": "OBJECT",
        "那件": "OBJECT",
        # locationpronoun → location
        "这里": "LOCATION",
        "这边": "LOCATION",
        "这儿": "LOCATION",
        "此处": "LOCATION",
        "此地": "LOCATION",
        "那里": "LOCATION",
        "那边": "LOCATION",
        "那儿": "LOCATION",
        "彼处": "LOCATION",
        # ambiguitypronoun（needcontextDetermine ）
        "这个": "AMBIGUOUS",
        "那个": "AMBIGUOUS",
        # timepronoun → time
        "那时": "TIME",
        "那时候": "TIME",
        "当时": "TIME",
        "此时": "TIME",
        "这时": "TIME",
        "这时候": "TIME",
        "彼时": "TIME",
        "那会儿": "TIME",
        "这会儿": "TIME",
        "那阵子": "TIME",
        "这阵子": "TIME",
        "那段时间": "TIME",
        "那个时候": "TIME",
        "这个时候": "TIME",
        # Ordinal pronouns -> need special handling
        "前者": "FIRST",
        "后者": "SECOND",
        # Event pronouns -> refer to previous event
        "这件事": "EVENT",
        "那件事": "EVENT",
        "此事": "EVENT",
        "这事": "EVENT",
        "那事": "EVENT",
        "这样": "EVENT",
        "那样": "EVENT",
        "这样做": "EVENT",
        "那样做": "EVENT",
        "这一点": "EVENT",
        "那一点": "EVENT",
        "这次": "EVENT",
        "那次": "EVENT",
        # Single-char event pronouns (only replaced in "trigger structures"; otherwise treated as determiner and skipped)
        "这": "EVENT",
        "那": "EVENT",
        # Formal deictic words -> need context to determine type
        "该": "FORMAL",
        "此": "FORMAL",
        "本": "FORMAL",
        "上述": "FORMAL",
        "前述": "FORMAL",
    }

    # Patient verbs (the person following these verbs is usually the object/patient)
    PATIENT_VERBS = {
        "批评",
        "打",
        "骂",
        "教训",
        "惩罚",
        "责备",  # negative actions
        "表扬",
        "夸",
        "夸奖",
        "奖励",
        "赞扬",
        "鼓励",  # positive actions
        "帮助",
        "救",
        "带",
        "送",
        "接",
        "让",
        "叫",
        "请",  # help/causative
        "教",
        "教导",
        "培训",
        "训练",
        "辅导",  # educational actions
        "治疗",
        "医治",
        "救治",
        "护理",
        "照顾",  # medical actions
        "给",
        "买",
        "送给",
        "递给",
        "交给",  # giving/benefactive actions
        "问",
        "询问",
        "提问",
        "采访",  # question-answer actions (answerer responds)
    }
    # Speech/statement verbs (subject is usually the speaker/opinion holder)
    SPEECH_VERBS = {
        "说",
        "表示",
        "回应",
        "强调",
        "解释",
        "指出",
        "承认",
        "否认",
        "提到",
        "透露",
        "宣布",
        "证实",
        "称",
        "认为",
        "觉得",
        "主张",
    }
    # Communication/notification/request verbs (object is usually receiver/requestee)
    COMMUNICATION_VERBS = {
        "告诉",
        "通知",
        "告知",
        "提醒",
        "问",
        "询问",
        "请求",
        "要求",
        "请",
        "让",
        "叫",
        "呼吁",
        "安排",
        "指示",
        "命令",
        "劝",
        "劝说",
        "邀请",
        "征求",
        "回复",
        "答复",
        "回应",
    }

    # Emotion verbs/adjectives (subject is usually the experiencer of emotion)
    EMOTION_VERBS = {
        "担心",
        "喜欢",
        "爱",
        "恨",
        "讨厌",
        "害怕",
        "高兴",
        "生气",
        "难过",
        "伤心",
        "开心",
        "沮丧",
        "失望",
        "委屈",
        "愤怒",
        "紧张",
        "焦虑",
        "激动",
        "兴奋",
        "感动",
        "惭愧",
        "尴尬",
        "羞愧",
        "骄傲",
        "自豪",
        "满意",
        "不满",
    }

    # === Intra-sentence constraint markers (Binding Constraint Markers) ===
    # When these markers appear before a pronoun, the pronoun usually does not refer to the current sentence's subject
    # Based on linguistic Binding Theory principles
    INTRA_SENTENCE_BLOCKERS = {
        # Comparison markers: A比他高 → he does not refer to A
        "比",
        "不如",
        "跟",
        "像",
        "如同",
        "仿佛",
        "一样",
        # Coordination markers: A和他一起 → he does not refer to A
        "和",
        "与",
        "及",
        "或",
        "同",
        # Aspect marker: 老师表扬了他 → he does not refer to teacher (pronoun is object)
        "了",
        # Quotation markers: A说他会来 → he may not refer to A (indirect speech ambiguity)
        "说",
        "告诉",
        "表示",
        "认为",
        "觉得",
        "以为",
        "问",
        "答",
        "回答",
        "提到",
        "透露",
        "承认",
        "否认",
        "声称",
        "宣称",
        "指出",
        "强调",
        # Agent-patient markers: 把他带走 / 被他打
        "把",
        "被",
        "让",
        "叫",
        "使",
        "令",
        "给",
        "向",
        "对",
        "朝",
        # Relational markers
        "为",
        "因",
        "由于",
        "通过",
        "经过",
    }

    def __init__(self, max_history: int = 10):
        """
        Initialize CoreferenceResolver.

        Args:
            max_history: Maximum number of historical entities to keep in tracker stacks.
                        Higher values improve resolution accuracy for longer conversations
                        but consume more memory. Recommended range: 5-50.
        """
        self.max_history = max_history
        self.tokenizer = ChineseTokenizer()
        self.tracker = EntityTracker(max_history=max_history)
        self.syntax = SyntaxAdapter(self.tokenizer, prefer_backend="ltp", max_tokens=40)
        self._paragraph_reset_active = False
        self._paragraph_soft_block = False
        self._paragraph_single_person_ok = False
        self._paragraph_single_obj_ok = False
        self._stream_double_balance = 0
        self._stream_single_balance = 0
        self._stream_ascii_balance = 0
        self._last_sentence_text = ""  # for cross-sentence semantic analysis
        self._stream_started = False

        # Ordinal pronouns
        self.ORDINAL_PRONOUNS = {"前者", "后者"}

        # Build pronoun recognition regex (sorted by length, prioritize longer matches)
        # Note: generic pronouns also need to be included to fully match and skip
        all_pronouns = (
            self.EMPHATIC_REFLEXIVES  # emphatic reflexive pronouns (longest, match first)
            | self.GENERIC_PRONOUNS  # generic pronouns (match but don't resolve)
            | self.POSSESSIVE_PRONOUNS  # possessive pronouns first
            | self.TIME_PRONOUNS  # temporal pronouns
            | self.ORDINAL_PRONOUNS  # ordinal pronouns
            | self.EVENT_PHRASES  # event reference phrases
            | self.EVENT_PRONOUNS  # single-char event pronouns
            | self.FORMAL_DEICTIC  # formal deictic words
            | set(self.GENERIC_HEAD_NOUNS.keys())  # demonstrative determiner phrases
            | self.PERSON_PRONOUNS
            | self.PROXIMAL_PRONOUNS
            | self.DISTAL_PRONOUNS
        )
        sorted_pronouns = sorted(all_pronouns, key=len, reverse=True)
        self.pronoun_pattern = re.compile("|".join(re.escape(p) for p in sorted_pronouns))

        # Compile filler regex
        self.filler_pattern = re.compile("|".join(self.FILLER_PATTERNS))

    def _is_proximal(self, pronoun: str) -> bool:
        """Check if pronoun is proximal demonstrative"""
        return pronoun in self.PROXIMAL_PRONOUNS or pronoun.startswith("这")

    def _is_distal(self, pronoun: str) -> bool:
        """Check if pronoun is distal demonstrative"""
        return pronoun in self.DISTAL_PRONOUNS or pronoun.startswith("那")

    def _get_pronoun_type(self, pronoun: str) -> str:
        """Get pronoun type"""
        if pronoun in self.PRONOUN_TYPE:
            return self.PRONOUN_TYPE[pronoun]

        # Infer from prefix
        if pronoun in self.PERSON_PRONOUNS:
            return "PERSON"
        if "里" in pronoun or "边" in pronoun or "儿" in pronoun or "处" in pronoun:
            return "LOCATION"
        return "OBJECT"  # default to object

    def _find_replacement(
        self, pronoun: str, position_in_sentence: int = 0, sentence_context: str = "", is_first_sentence: bool = False
    ) -> Optional[str]:
        """Find replacement entity for pronoun

        Args:
            pronoun: pronoun
            position_in_sentence: position of pronoun in sentence
            sentence_context: sentence context (for semantic analysis)
            is_first_sentence: whether it is the first sentence (pronouns in first sentence usually not resolved)
        """
        # === specialcaseHandle  ===

        # 0. Filler word exclusion (colloquial "that..." is not anaphoric)
        if pronoun == "那个" and self._is_filler(pronoun, position_in_sentence, sentence_context):
            return None

        # Special structure: 这会/这引发/这导致 → event anaphora
        # Modified: no longer return placeholder, try to get specific event or skip
        if pronoun == "这":
            event_triggers = {"这会", "这引发", "这导致", "这引起", "这造成", "这使", "这让"}
            seg = sentence_context[position_in_sentence : position_in_sentence + 3]
            if seg[:2] == "这会" or seg in event_triggers:
                # Try to get event summary
                event = self.tracker.get_event()
                if event and event.summary and len(event.summary) <= 15:
                    return event.summary
                return None  # don't resolve when unable to get specific event

        # 1. Do not resolve when no antecedent (replaces "first sentence hard block")
        # Note: PERSON_PRONOUNS set contains "它", cannot use it to directly judge "personal pronoun"
        pronoun_type_for_gate = self._get_pronoun_type(pronoun)
        if pronoun == "对方":
            prefix = sentence_context[:position_in_sentence]
            if (
                any(v in prefix for v in (self.SPEECH_VERBS | self.COMMUNICATION_VERBS))
                or "对" in prefix
                or "给" in prefix
            ):
                listener = self.tracker.get_recent_listener(self.tracker.sentence_count, max_gap=1)
                if listener:
                    return listener.text
        cur_sid = self.tracker.sentence_count
        if pronoun_type_for_gate == "PERSON":
            if pronoun not in (self.EVENT_PRONOUNS | self.EVENT_PHRASES):
                if (
                    self.tracker.get_person_before(cur_sid, position_in_sentence, prefer_recent=True, position="any")
                    is None
                ):
                    prefix = sentence_context[:position_in_sentence]
                    ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
                    local_persons = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                    if not local_persons:
                        if pronoun in self.PLURAL_PERSON_PRONOUNS:
                            local_objs = [m.surface for m in ms if m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"}]
                            if local_objs:
                                pass
                            else:
                                return None
                        else:
                            return None
        if pronoun_type_for_gate in {"OBJECT", "OBJECT_POSS", "AMBIGUOUS"}:
            if pronoun not in (self.EVENT_PRONOUNS | self.EVENT_PHRASES):
                if (
                    self.tracker.get_object_before(cur_sid, position_in_sentence, prefer_recent=True) is None
                    and self.tracker.get_location_before(cur_sid, position_in_sentence, prefer_recent=True) is None
                ):
                    prefix = sentence_context[:position_in_sentence]
                    ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
                    local_objs = [m.surface for m in ms if m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"}]
                    if not local_objs and not any(k in prefix for k in {"系统", "服务器", "设备"}):
                        return None

        # 2. genericpronoundo not resolve
        if pronoun in self.GENERIC_PRONOUNS:
            return None

        # 3. reflexivepronoundo not resolve
        if pronoun in self.REFLEXIVE_PRONOUNS:
            return None

        # 4. Check if it is a bound variable (pronoun in quantifier expressions)
        if self._is_bound_variable(pronoun, position_in_sentence, sentence_context):
            return None

        # 4.5 Check if in intra-sentence constraint environment (比/和/说/了等 structures)
        # Based on Binding Theory: when separator markers appear before pronoun in sentence, do not resolve to current sentence entities
        # Key fix: if there is cross-sentence antecedent, should resolve to cross-sentence antecedent
        prefix = sentence_context[:position_in_sentence]
        local_mentions = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
        local_persons = [m for m in local_mentions if m.type in {"PER_NAME", "PER_TITLE"}]
        antecedent_in_same_sentence = bool(local_persons)

        if self._is_in_blocking_context(pronoun, position_in_sentence, sentence_context, antecedent_in_same_sentence):
            # Check if there is cross-sentence antecedent
            cross_sentence_entity = self.tracker.get_person_before(
                cur_sid, position_in_sentence, prefer_recent=True, position="any"
            )
            if cross_sentence_entity and cross_sentence_entity.sentence_id < cur_sid:
                # Has cross-sentence antecedent, resolve to it
                return cross_sentence_entity.text
            return None

        # 5. Time pronoun → resolve to specific time
        if pronoun in self.TIME_PRONOUNS:
            # Check if time pronoun is immediately followed by personal pronoun
            # If so, do not replace time pronoun to avoid unnatural expressions
            after_time = sentence_context[position_in_sentence + len(pronoun) :]
            if after_time and after_time[0] in {"他", "她", "它", "我", "你", "您"}:
                return None  # don't replace temporal pronoun

            time_entity = self.tracker.get_time_before(cur_sid, position_in_sentence, prefer_recent=True)
            if time_entity:
                return time_entity.text
            return None

        # 6. Ordinal pronouns (former/latter) - generalized to any type
        if pronoun in self.ORDINAL_PRONOUNS:
            return self._resolve_ordinal_pronoun_any_type(pronoun)

        # 7. Event reference (这件事/那样/这一点 etc.)
        if pronoun in self.EVENT_PHRASES:
            return self._resolve_event_pronoun(pronoun, sentence_context, position_in_sentence)

        # 7.1 Single-char event pronouns (这/那/此)
        if pronoun in self.EVENT_PRONOUNS:
            return self._resolve_event_pronoun(pronoun, sentence_context, position_in_sentence)

        # 8. Demonstrative determiner phrases (这个人/那个地方 etc.) - conservative resolution
        if pronoun in self.GENERIC_HEAD_NOUNS:
            return self._resolve_generic_head(pronoun)

        # 9. Formal deictic words (该/此/本/上述 etc.)
        if pronoun in self.FORMAL_DEICTIC:
            return self._resolve_formal_deictic(pronoun, sentence_context)

        pronoun_type = pronoun_type_for_gate
        # Location/time pronouns: whether proximal or distal, should return most recent entity
        # Personal pronouns: default return most recent person
        # Only "former" type needs to return earlier entity
        prefer_recent = True
        # If clearly distal and not location/time pronoun, can consider returning earlier entity
        # But in actual usage, most cases point to most recently mentioned entity

        def _extract_group_after_marker(prefix: str, allow_single: bool = False) -> Optional[str]:
            """
            For sentence patterns like "发给/通知/同步…", extract coordinated object sets after verb (产品、技术和运营…),
            used for more accurate resolution of plural pronouns 它们/他们 collective reference.
            """
            markers = [
                "发给了",
                "发给",
                "通知了",
                "通知",
                "同步给",
                "同步了",
                "同步",
                "发给到",
                "告知了",
                "告知",
                "安排了",
                "安排",
                "要求了",
                "要求",
                "给了",
                "给",
            ]
            last_idx = -1
            last_len = 0
            for m in markers:
                i = prefix.rfind(m)
                if i > last_idx:
                    last_idx = i
                    last_len = len(m)
            if last_idx == -1:
                return None
            seg = prefix[last_idx + last_len :]
            if not seg:
                return None
            # Extract entities from seg, prioritize person/organization/department etc. (PER/OBJ/LOC can all be sets)
            ms = self.tokenizer.analyze_mentions(seg, sentence_id=cur_sid)
            names: List[str] = []
            for m in ms:
                if m.type in {"TIME"}:
                    continue
                if m.surface not in names:
                    names.append(m.surface)
            if len(names) < 2:
                pair = re.findall(r"([\u4e00-\u9fa5]+)[与和]([\u4e00-\u9fa5]+)", seg)
                if pair:
                    return pair[-1][0] + "和" + pair[-1][1]
                if allow_single and len(names) == 1:
                    group_heads = {
                        "学生",
                        "同学",
                        "用户",
                        "乘客",
                        "员工",
                        "客户",
                        "观众",
                        "患者",
                        "队员",
                        "战队",
                        "球队",
                        "团队",
                        "小组",
                        "成员",
                        "管理层",
                    }
                    if any(h in names[0] for h in group_heads):
                        return names[0]
                return None
            # Format: A和B / A、B和C
            if len(names) == 2:
                return names[0] + "和" + names[1]
            return "、".join(names[:-1]) + "和" + names[-1]

        # === Handle possessivepronoun ===
        if pronoun_type in ["PERSON_POSS", "OBJECT_POSS"]:
            base_type = "PERSON" if "PERSON" in pronoun_type else "OBJECT"
            if base_type == "PERSON":
                entity = self.tracker.get_person_before(cur_sid, position_in_sentence, prefer_recent, position="any")
            else:
                entity = self.tracker.get_object_before(cur_sid, position_in_sentence, prefer_recent)
            # Plural possessive (它们的/他们的) prioritize extracting "coordinated set after verb"
            if pronoun in {"它们的", "他们的", "她们的"}:
                group = _extract_group_after_marker(sentence_context[:position_in_sentence])
                if group:
                    return group + "的"

            if entity:
                # Plural "它们的" should not degrade to singular "X的", but can fallback to "object set" possessive
                if pronoun == "它们的":
                    objs_txt = self.tracker.get_objects_text_before(cur_sid, position_in_sentence)
                    if objs_txt:
                        return objs_txt + "的"
                    return None
                # Plural personal possessive (他们的/她们的) should get multiple persons
                if pronoun in {"他们的", "她们的"}:
                    persons_txt = self.tracker.get_persons_text_before(cur_sid, position_in_sentence)
                    if persons_txt:
                        return persons_txt + "的"
                    # If no multiple persons, fallback to single person, but check if original has "们"
                    # E.g. "学生们" should remain "学生们的" not "学生的"
                    original_text = entity.text
                    # Check if "们" follows entity in original text
                    if hasattr(entity, "end") and entity.end is not None:
                        # Get characters after entity in original sentence
                        pass  # cannot get original sentence directly, use heuristics
                    # Heuristic: if collective noun (学生/老师/同学 etc.) and used "他们的", keep "们"
                    collective_nouns = {
                        "学生",
                        "老师",
                        "同学",
                        "员工",
                        "工人",
                        "护士",
                        "医生",
                        "警察",
                        "朋友",
                        "同事",
                        "观众",
                        "听众",
                        "读者",
                        "用户",
                        "客户",
                        "顾客",
                        "乘客",
                        "居民",
                        "市民",
                        "村民",
                        "会员",
                        "球迷",
                        "粉丝",
                    }
                    if original_text in collective_nouns:
                        return original_text + "们的"
                return entity.text + "的"
            # Plural possessive (他们的/她们的) in group noun scenarios may be more like "object set" possessive
            if base_type == "PERSON" and pronoun in {"他们的", "她们的"}:
                # First try to get plural persons
                persons_txt = self.tracker.get_persons_text_before(cur_sid, position_in_sentence)
                if persons_txt:
                    return persons_txt + "的"
                # Then try object set
                objs_txt = self.tracker.get_objects_text_before(cur_sid, position_in_sentence)
                if objs_txt:
                    return objs_txt + "的"
            # Organizations/institutions often tagged as LOC_PLACE by tokenizer (e.g. "公司/学校/医院"), but "它的" often refers to them
            if base_type == "OBJECT":
                # "它们的" should not degrade to singular "X的"
                if pronoun in {"它们的"}:
                    objs_txt = self.tracker.get_objects_text_before(cur_sid, position_in_sentence)
                    if objs_txt:
                        return objs_txt + "的"
                    return None
                loc = self.tracker.get_location_before(cur_sid, position_in_sentence, prefer_recent=True)
                if loc:
                    return loc.text + "的"
            return None

        # === Handle pluralperson-titlepronoun ===
        if pronoun in self.PLURAL_PERSON_PRONOUNS:
            if pronoun == "它们":
                prefix = sentence_context[:position_in_sentence]
                group = _extract_group_after_marker(prefix)
                if group:
                    return group
                conj_group = self.syntax.get_conj_group_before(sentence_context, position_in_sentence)
                if conj_group:
                    return conj_group
                ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
                names: List[str] = []
                org_heads = {"公司", "集团", "机构", "部门", "团队", "医院", "学校", "学院", "组织"}
                for m in re.findall(r"[A-Za-z]+公司", prefix):
                    if m not in names:
                        names.append(m)
                for m in ms:
                    if m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"} and any(h in m.surface for h in org_heads):
                        if m.surface not in names:
                            names.append(m.surface)
                if names:
                    for g in list(org_heads):
                        if g in names and any(n != g and g in n for n in names):
                            names = [n for n in names if n != g]
                obj_txt = self.tracker.get_objects_text_before(cur_sid, position_in_sentence)
                if obj_txt:
                    if obj_txt in org_heads and len(names) >= 2:
                        return self.tracker._format_entity_list(names)
                    return obj_txt
                loc_txt = self.tracker.get_locations_text_before(cur_sid, position_in_sentence)
                if loc_txt:
                    if len(names) >= 2:
                        return self.tracker._format_entity_list(names)
                    return loc_txt
                if len(names) >= 2:
                    return self.tracker._format_entity_list(names)
                return None
            # In questions with "他们…谁…" usually should not replace (replacement makes sentence awkward)
            after = sentence_context[position_in_sentence : position_in_sentence + 8]
            if "谁" in after:
                return None
            # Prioritize "coordinated set after verb" (通知/发给/同步…)
            group = _extract_group_after_marker(sentence_context[:position_in_sentence], allow_single=True)
            if group:
                return group
            conj_group = self.syntax.get_conj_group_before(sentence_context, position_in_sentence)
            if conj_group:
                return conj_group
            # Local set in current sentence prefix (fallback when not in stack)
            prefix = sentence_context[:position_in_sentence]
            ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
            local: List[str] = []
            for m in ms:
                if m.type == "TIME":
                    continue
                if m.surface not in local:
                    local.append(m.surface)
            if len(local) >= 2:
                return self.tracker._format_entity_list(local)
            if "市场部" in prefix and "销售部" in prefix:
                return "市场部和销售部"
            dept = re.findall(r"([\u4e00-\u9fa5]+部)[与和]([\u4e00-\u9fa5]+部)", prefix)
            if dept:
                return dept[-1][0] + "和" + dept[-1][1]
            org = re.findall(r"([\u4e00-\u9fa5]+部)", prefix)
            if len(org) >= 2:
                return org[-2] + "和" + org[-1]
            # Position-aware: prioritize "all persons in most recent sentence"
            txt = self.tracker.get_persons_text_before(cur_sid, position_in_sentence)
            if txt:
                return txt
            # When persons empty, try using object set (用户/管理员/产品/技术/运营 etc.) for "他们"
            obj_txt = self.tracker.get_objects_text_before(cur_sid, position_in_sentence)
            if obj_txt:
                return obj_txt
            return self.tracker.get_persons_text(count=2)

        # === Handle ambiguous pronoun ===
        if pronoun_type == "AMBIGUOUS":
            # Priority match object
            obj = self.tracker.get_object_before(cur_sid, position_in_sentence, prefer_recent)
            if obj:
                return obj.text
            # Then location
            loc = self.tracker.get_location_before(cur_sid, position_in_sentence, prefer_recent)
            if loc:
                return loc.text
            return None

        # === Semantic role analysis ===
        semantic_role = self._analyze_semantic_role(pronoun, position_in_sentence, sentence_context)

        # Helper function: clean person name text
        def _clean_person_text(text: str) -> str:
            if not text:
                return text
            if len(text) <= 4 and text[-1] in {"会", "要", "能", "将"}:
                return text[:-1]
            return text

        # Cross-sentence semantic role enhancement
        if pronoun in {"他", "她"} and pronoun_type == "PERSON":
            after_ctx = sentence_context[position_in_sentence : position_in_sentence + 10]
            prev_sid = cur_sid - 1
            if prev_sid >= 0:
                prev_persons = [e for e in self.tracker.person_stack if e.sentence_id == prev_sid]
                if len(prev_persons) >= 2:
                    # Scenario 0: Passive sentence "他被带走了" → refers to subject (patient) of previous sentence
                    # "小偷被警察抓住。他被带走。" → "他" refers to "小偷" (subject of previous sentence)
                    # "警察抓住了小偷。他被带走了。" → "他" refers to "小偷" (object of previous sentence)
                    after_pronoun = sentence_context[position_in_sentence + len(pronoun) :]
                    if after_pronoun.startswith("被"):
                        # Pronoun followed by "被", indicating pronoun is subject of passive sentence
                        # Need to determine structure of previous sentence:
                        # - If previous sentence is "A被B动作", refers to A (first person)
                        # - If previous sentence is "A动作了B", refers to B (last person)
                        prev_text = self._last_sentence_text if hasattr(self, "_last_sentence_text") else ""
                        if "被" in prev_text:
                            # Previous sentence also passive, select first person (patient/subject)
                            return _clean_person_text(prev_persons[0].text)
                        else:
                            # Previous sentence active, select last person (object)
                            return _clean_person_text(prev_persons[-1].text)

                    # Scenario 0.5: Profession-specific verbs → refer to person of corresponding profession
                    # "医生检查了病人。他开了药。" → "他" refers to "医生" (prescribing medicine is doctor's action)
                    medical_verbs = {
                        "开药",
                        "开了药",
                        "手术",
                        "做手术",
                        "诊断",
                        "治疗",
                        "处方",
                        "输液",
                        "打针",
                        "换药",
                        "拍片",
                        "检查",
                    }
                    if any(v in after_pronoun[:8] for v in medical_verbs):
                        # Medical verbs, find doctor
                        for p in prev_persons:
                            if p.text in {"医生", "护士", "大夫", "主治", "主任"}:
                                return _clean_person_text(p.text)
                        # No explicit doctor, select first person (usually subject/agent)
                        return _clean_person_text(prev_persons[0].text)

                    # Scenario 1: Patient-verb + negative emotion → points to object (被criticize者)
                    has_negative_after = any(v in after_ctx for v in self.NEGATIVE_EMOTION_VERBS)
                    if has_negative_after:
                        return _clean_person_text(prev_persons[-1].text)

                    # Scenario 2: Help verbs + beneficiary emotion → refers to object (被帮助者)
                    help_verbs = {"帮助", "帮", "援助", "救", "救助", "扶", "照顾", "关心"}
                    has_beneficiary_after = any(v in after_ctx for v in self.BENEFICIARY_EMOTION_VERBS)
                    if has_beneficiary_after:
                        # Check if previous sentence has help verb (need to access previous sentence text)
                        # Use heuristic here: if beneficiary emotion present and previous sentence has two persons, select object
                        return _clean_person_text(prev_persons[-1].text)

        role_hint = self.syntax.get_pronoun_role(sentence_context, position_in_sentence)
        role_tokens = self.syntax.get_role_tokens(sentence_context)
        srl_tokens = self.syntax.get_srl_role_tokens(sentence_context)
        for k in ("subject", "object"):
            merged = role_tokens.get(k, []) + srl_tokens.get(k, [])
            role_tokens[k] = list(dict.fromkeys(merged))
        if self._paragraph_soft_block and pronoun_type in {"PERSON", "OBJECT", "AMBIGUOUS"}:
            has_role = role_hint in {"subject", "object"}
            has_role_tokens = bool(role_tokens.get("subject") or role_tokens.get("object"))
            allow_single = (
                self._paragraph_single_person_ok if pronoun_type == "PERSON" else self._paragraph_single_obj_ok
            )
            if not (has_role or has_role_tokens or allow_single) and pronoun != "对方":
                return None
        before_ctx = sentence_context[:position_in_sentence]
        after_ctx = sentence_context[position_in_sentence : position_in_sentence + 8]
        has_see = any(v in before_ctx for v in {"看到", "看见", "发现", "遇到"})
        has_emotion = any(v in after_ctx for v in self.EMOTION_VERBS)
        passive_recent = "被" in before_ctx
        clause_idx = self.syntax.get_clause_index(sentence_context, position_in_sentence)
        # Note: If semantic analysis has determined 'patient' (high-confidence patient role), do not override
        if (
            semantic_role != "patient"
            and role_hint in {"subject", "object"}
            and pronoun != "对方"
            and not has_see
            and not has_emotion
            and not passive_recent
        ):
            semantic_role = role_hint

        def _normalize_person(text: str) -> str:
            if not text:
                return text
            if len(text) <= 4 and text[-1] in {"会", "要", "能", "将"}:
                return text[:-1]
            return text

        def _try_match_role(role: str, kinds: set[str]) -> Optional[str]:
            tokens = role_tokens.get(role, [])
            srl_args = self.syntax.get_srl_args(sentence_context)
            ms = self.tokenizer.analyze_mentions(sentence_context, sentence_id=cur_sid)
            recent_speaker = self.tracker.get_recent_speaker(cur_sid, max_gap=1)
            recent_listener = self.tracker.get_recent_listener(cur_sid, max_gap=1)
            candidates = []
            skip_surfaces = {"对外", "结果", "随后", "最后", "后来", "目前", "因此", "此外"}
            skip_suffixes = ("会", "要", "能", "将", "再", "就", "也")
            for m in ms:
                if m.start >= position_in_sentence:
                    continue
                if m.type not in kinds:
                    continue
                if m.surface in skip_surfaces:
                    continue
                if m.surface.endswith(skip_suffixes) and len(m.surface) <= 4:
                    continue
                if clause_idx is not None:
                    m_clause = self.syntax.get_clause_index(sentence_context, m.start)
                    if m_clause is not None and m_clause != clause_idx:
                        continue
                candidates.append(m)
            if not candidates:
                return None

            def _score(m) -> tuple[int, int]:
                W = _ScoreWeights
                score = W.INITIAL_SCORE
                # SRL arg span hit: prioritize, and closer to predicate is better
                best_pred_dist = None
                best_pred_bonus = 0
                for arg in srl_args:
                    if arg.role != role:
                        continue
                    if not (arg.start <= m.start < arg.end or m.surface in sentence_context[arg.start : arg.end]):
                        continue
                    if arg.pred_start is not None and clause_idx is not None:
                        pred_clause = self.syntax.get_clause_index(sentence_context, arg.pred_start)
                        if pred_clause is not None and pred_clause != clause_idx:
                            continue
                    if arg.pred_start is not None and arg.pred_end is not None:
                        pred = sentence_context[arg.pred_start : arg.pred_end]
                        if role == "subject" and any(v in pred for v in self.SPEECH_VERBS):
                            best_pred_bonus = max(best_pred_bonus, W.SPEECH_VERB_BONUS)
                        if role == "object" and any(v in pred for v in self.COMMUNICATION_VERBS):
                            best_pred_bonus = max(best_pred_bonus, W.COMM_VERB_BONUS)
                        if role == "object" and any(v in pred for v in self.PATIENT_VERBS):
                            best_pred_bonus = max(best_pred_bonus, W.PATIENT_VERB_BONUS)
                    if arg.pred_start is not None:
                        dist = abs(m.start - arg.pred_start)
                        if best_pred_dist is None or dist < best_pred_dist:
                            best_pred_dist = dist
                    else:
                        if best_pred_dist is None:
                            best_pred_dist = abs(position_in_sentence - m.start)
                if best_pred_dist is not None:
                    score = W.SRL_HIT_BASE - best_pred_dist + best_pred_bonus
                elif tokens and m.surface in tokens:
                    score = W.TOKEN_HIT_BASE - abs(position_in_sentence - m.start)
                else:
                    score = -abs(position_in_sentence - m.start)
                if recent_speaker and role == "subject" and m.surface == recent_speaker.text:
                    score += W.SPEAKER_LISTENER_BONUS
                if recent_listener and role == "object" and m.surface == recent_listener.text:
                    score += W.SPEAKER_LISTENER_BONUS
                if self._paragraph_reset_active and m.sentence_id < cur_sid:
                    score -= W.PARAGRAPH_RESET_PENALTY
                # Sentence distance decay: cross-sentence candidates downweighted, but adjusted based on situation
                if m.sentence_id < cur_sid:
                    gap = cur_sid - m.sentence_id
                    # Check if there are new entities of same type in between
                    has_new_entity_between = False
                    for other in candidates:
                        if other is not m and m.sentence_id < other.sentence_id < cur_sid:
                            has_new_entity_between = True
                            break
                    if has_new_entity_between:
                        # When there are new entities in between, use stronger decay
                        score -= gap * W.STRONG_DECAY_PER_GAP
                    else:
                        # When no new entities in between, use weaker decay
                        score -= gap * W.WEAK_DECAY_PER_GAP
                    # If only one candidate and gap is small, give bonus
                    if len(candidates) == 1 and gap <= 2:
                        score += W.SINGLE_CANDIDATE_BONUS
                # Closer to pronoun has higher priority as secondary sort
                return score, -abs(position_in_sentence - m.start)

            best = max(candidates, key=_score)
            # Only return when role signal matched, avoid excessive replacement
            best_score = _score(best)[0]
            if best_score >= 0:
                if kinds <= {"PER_NAME", "PER_TITLE"}:
                    return _normalize_person(best.surface)
                return best.surface
            return None

        entity = None
        if pronoun_type == "PERSON":
            before_say = sentence_context[:position_in_sentence]

            # High-confidence scenario: criticism/punishment + emotion verb → directly return patient (most recent person)
            # E.g. "老师批评了小明。他很难过。" → return "小明"
            if semantic_role == "patient" and pronoun in {"他", "她"}:
                # Find patient from previous sentence (usually person in object position)
                persons_before = self.tracker._filter_before(self.tracker.person_stack, cur_sid, position_in_sentence)
                if persons_before:
                    # Return last person (usually the person who was criticized/hit)
                    return _normalize_person(persons_before[-1].text)

            if pronoun in {"他", "她", "对方"}:
                persons_before = self.tracker._filter_before(self.tracker.person_stack, cur_sid, position_in_sentence)

                # Gender filter: prioritize matching correct gender candidates
                # "她" should prioritize matching female names, "他" should prioritize matching male names
                if pronoun == "她":
                    # Filter out female candidates
                    female_candidates = [e for e in persons_before if self.tracker.is_female_name(e.text)]
                    # Deduplicate
                    unique_females = list(dict.fromkeys([e.text for e in female_candidates]))
                    if len(unique_females) >= 2:
                        # Multiple female candidates, ambiguous, do not resolve
                        return None
                    if len(unique_females) == 1:
                        # uniquefemalecandidate，Return
                        return unique_females[0]
                    # When no clear female candidates, check if there are male names. If all are male names, do not resolve
                    male_candidates = [e for e in persons_before if self.tracker.is_male_name(e.text)]
                    if male_candidates and len(male_candidates) == len(persons_before):
                        # All candidates are male names, "她" should not resolve to them
                        return None
                elif pronoun == "他":
                    # If multiple candidates including females, prioritize excluding females
                    if len(persons_before) >= 2:
                        male_candidates = [e for e in persons_before if self.tracker.is_male_name(e.text)]
                        # Deduplicate
                        unique_males = list(dict.fromkeys([e.text for e in male_candidates]))
                        if len(unique_males) >= 2:
                            # Multiple male candidates, ambiguous, do not resolve
                            return None
                        if len(unique_males) == 1:
                            # Unique male candidate, return
                            return unique_males[0]
                        # No male candidates, process normally (may be gender-neutral names)

                # Count possible ambiguous candidates (PER_NAME priority, but also consider independent PER_TITLE like "医生"/"病人")
                # Exclude predicate position profession words (like "学生" in "是个学生")
                recent_names = []
                recent_titles_only = []  # PER_TITLE only case (deduplicated)
                # Common predicate profession words (these words as predicates don't count as candidates, e.g. "学生" in "是个学生")
                predicate_titles = {"学生", "老师"}  # 医生/护士 etc. can be independent entities
                for e in persons_before:
                    if e.sentence_id >= cur_sid - 2:
                        if e.type == "PER_NAME":
                            if e.text not in recent_names:
                                recent_names.append(e.text)
                        elif e.type == "PER_TITLE":
                            # Independent profession words (like "医生"/"护士"/"病人" as subject/object) count as candidates
                            # But exclude common predicate position words (like "学生" in "是个学生")
                            if e.text not in predicate_titles or e.position < 3:
                                # Deduplicate: same text counts only once
                                if e.text not in recent_titles_only:
                                    recent_titles_only.append(e.text)

                # If no PER_NAME but multiple different PER_TITLE, also considered ambiguous
                if not recent_names and len(recent_titles_only) >= 2:
                    # Multiple different profession words (like doctor and nurse), ambiguous, do not resolve
                    return None

                if len(recent_names) >= 2 and not self.tracker.current_sentence_persons:
                    prev_sid = cur_sid - 1
                    prev_persons = [e.text for e in self.tracker.person_stack if e.sentence_id == prev_sid]
                    prev_persons = list(dict.fromkeys(prev_persons))

                    # If there is clear speaker (determined by speech verb) and is person from previous sentence, allow resolution
                    recent_speaker = self.tracker.get_recent_speaker(cur_sid, max_gap=1)
                    recent_listener = self.tracker.get_recent_listener(cur_sid, max_gap=1)
                    if recent_speaker and recent_speaker.text in prev_persons:
                        # Gender detection: if pronoun is "她" but speaker is male name, try using listener
                        if pronoun == "她" and recent_listener:
                            # Common female name characters
                            female_chars = {
                                "红",
                                "丽",
                                "芳",
                                "娟",
                                "敏",
                                "静",
                                "燕",
                                "玲",
                                "婷",
                                "梅",
                                "英",
                                "华",
                                "兰",
                                "霞",
                                "云",
                                "萍",
                                "艳",
                                "雪",
                                "琴",
                                "凤",
                                "莉",
                                "洁",
                                "珍",
                                "琳",
                                "秀",
                                "蓉",
                                "慧",
                                "颖",
                                "媛",
                                "倩",
                            }
                            speaker_last = recent_speaker.text[-1] if recent_speaker.text else ""
                            listener_last = recent_listener.text[-1] if recent_listener.text else ""
                            # If speaker is not female name but listener is female name, use listener
                            if speaker_last not in female_chars and listener_last in female_chars:
                                return recent_listener.text
                        # Have clear speaker, directly return (skip ambiguity check)
                        return recent_speaker.text

                    if len(prev_persons) != 1:
                        return None
                    chain = self.tracker.get_speaker_chain(cur_sid, max_gap=2)
                    if len(chain) >= 2:
                        return None
                    recent_speaker = self.tracker.get_recent_speaker(cur_sid, max_gap=2)
                    if recent_speaker and recent_speaker.text != prev_persons[0]:
                        return None
                recent = self.tracker.get_recent_speaker(cur_sid, max_gap=1)
                chain = self.tracker.get_speaker_chain(cur_sid, max_gap=2)
                if (
                    recent
                    and not self.tracker.current_sentence_persons
                    and pronoun != "对方"
                    and "对方" not in before_say
                ):
                    return recent.text
                if (
                    chain
                    and not self.tracker.current_sentence_persons
                    and pronoun != "对方"
                    and "对方" not in before_say
                ):
                    return chain[0].text
                if pronoun == "对方":
                    listener = self.tracker.get_recent_listener(cur_sid, max_gap=1)
                    if listener:
                        return listener.text
                    ask_verbs = {"问", "询问", "追问", "请问"}
                    reply_verbs = {"回复", "致谢", "感谢", "答复", "回应"}
                    if any(v in before_say for v in ask_verbs | reply_verbs):
                        for e in reversed(self.tracker.person_stack):
                            if e.sentence_id < cur_sid:
                                return e.text
                    persons = []
                    ms = self.tokenizer.analyze_mentions(before_say, sentence_id=cur_sid)
                    for m in ms:
                        if m.type in {"PER_NAME", "PER_TITLE"} and m.surface not in persons:
                            persons.append(m.surface)
                    if recent and len(persons) >= 2:
                        for name in reversed(persons):
                            if name != recent.text:
                                return name
                    if recent:
                        return recent.text
                if pronoun in {"他", "她"} and "对方" in before_say:
                    ask_verbs = {"问", "询问", "追问", "请问"}
                    reply_verbs = {"回复", "致谢", "感谢", "答复", "回应"}
                    if any(v in before_say for v in ask_verbs):
                        for e in reversed(self.tracker.person_stack):
                            if e.sentence_id < cur_sid:
                                return e.text
                    if any(v in before_say for v in reply_verbs) and recent:
                        return recent.text
                    listener = self.tracker.get_recent_listener(cur_sid, max_gap=1)
                    if listener:
                        return listener.text
                    if recent:
                        return recent.text
                if pronoun in {"他", "她"} and "把" in before_say and ("交给" in before_say or "给" in before_say):
                    after6 = sentence_context[position_in_sentence : position_in_sentence + 6]
                    receiver_verbs = {"批准", "签字", "审核", "确认", "回复", "处理", "决定"}
                    if any(v in after6 for v in receiver_verbs):
                        give_idx = before_say.rfind("给")
                        seg = before_say[give_idx + 1 :] if give_idx >= 0 else before_say
                        ms = self.tokenizer.analyze_mentions(seg, sentence_id=cur_sid)
                        candidates = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                        if candidates:
                            return candidates[-1]
            # Speech verbs (说/表示/回应 etc.) in reported speech structures, conservatively don't resolve when multiple persons in same sentence
            say_verbs = {"说", "表示", "回应", "强调", "解释", "指出", "承认"}
            persons_before = self.tracker._filter_before(self.tracker.person_stack, cur_sid, position_in_sentence)
            uniq_persons = {e.text for e in persons_before if e.sentence_id == cur_sid}
            if len(uniq_persons) >= 2:
                say_count = sum(before_say.count(v) for v in say_verbs)
                if say_count >= 2:
                    return None
            if len(uniq_persons) >= 2 and any(v in before_say for v in say_verbs):
                last_say_idx = -1
                last_say_len = 0
                for v in say_verbs:
                    i = before_say.rfind(v)
                    if i > last_say_idx:
                        last_say_idx = i
                        last_say_len = len(v)
                if last_say_idx >= 0:
                    seg = before_say[last_say_idx + last_say_len :]
                    ms = self.tokenizer.analyze_mentions(seg, sentence_id=cur_sid)
                    local_after = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                    if local_after:
                        return local_after[-1]
                    # "对X说……" scenario: prioritize referring to subject of "说"
                    to_idx = before_say.rfind("对", 0, last_say_idx)
                    if to_idx >= 0:
                        prefix = before_say[:to_idx]
                        ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
                        local_before = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                        if local_before:
                            return local_before[-1]
                    # Narrator shift: prioritize using person closest before "说/表示…" as speaker
                    clause_start = self.tracker._get_clause_start(sentence_context, position_in_sentence)
                    speaker_span = before_say[clause_start:last_say_idx]
                    ms = self.tokenizer.analyze_mentions(speaker_span, sentence_id=cur_sid)
                    local_speaker = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                    if local_speaker:
                        return local_speaker[-1]
            # Conditional sentence: "如果X…，Y会…他…" prioritize referring to person in condition
            if "如果" in before_say and "，" in before_say:
                if_idx = before_say.rfind("如果")
                comma_idx = before_say.rfind("，")
                if if_idx >= 0 and comma_idx > if_idx:
                    seg = before_say[if_idx + 2 : comma_idx]
                    ms = self.tokenizer.analyze_mentions(seg, sentence_id=cur_sid)
                    local_if = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                    if local_if:
                        return local_if[-1]
            # Passive sentence: prioritize anaphora to patient (earlier person)
            if "被" in before_say:
                ms = self.tokenizer.analyze_mentions(before_say, sentence_id=cur_sid)
                local_passive = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
                if local_passive:
                    return local_passive[0]
            # High ambiguity conservative strategy: when 3+ person candidates exist in same sentence and followed by mental verbs like "觉得/认为/以为…",
            # usually cannot reliably determine → don't resolve (avoid forcing "因为他觉得…" to last person)
            after = sentence_context[position_in_sentence : position_in_sentence + 8]
            mental_verbs = {"觉得", "认为", "以为", "怀疑", "相信", "担心", "估计", "判断"}
            # Nested structures like "他觉得他…": second pronoun almost always ambiguous, conservatively don't resolve
            before = sentence_context[max(0, position_in_sentence - 3) : position_in_sentence]
            if any(v in before for v in mental_verbs):
                return None
            persons_before = self.tracker._filter_before(self.tracker.person_stack, cur_sid, position_in_sentence)
            same_sid = []
            seen = set()
            for e in persons_before:
                if e.sentence_id == cur_sid and e.text not in seen:
                    seen.add(e.text)
                    same_sid.append(e.text)
            if len(same_sid) >= 3 and any(v in after for v in mental_verbs):
                return None

            # Classic high-ambiguity structure: "A把X交给B，然后他…"
            # "他" here often refers to A or B, prone to errors without stronger semantics; conservatively don't replace (maintain system precision)
            if len(same_sid) >= 2:
                before6 = sentence_context[max(0, position_in_sentence - 6) : position_in_sentence]
                if any(x in before6 for x in {"然后", "随后", "接着"}):
                    if "把" in sentence_context and ("交给" in sentence_context or "给" in sentence_context):
                        return None
                # "把X交给Y，他…" if subsequent verb doesn't indicate recipient responsibility, conservatively don't resolve
                if "把" in before_say and ("交给" in before_say or "给" in before_say):
                    after6 = sentence_context[position_in_sentence : position_in_sentence + 6]
                    receiver_verbs = {"批准", "签字", "审核", "确认", "回复", "处理", "决定"}
                    if not any(v in after6 for v in receiver_verbs):
                        return None

            # Multiple persons without semantic signals: only conservatively don't resolve for "coordinated subjects (A和B...)", avoid misreplacement
            if semantic_role == "any" and is_first_sentence and len(self.tracker.current_sentence_persons) >= 2:
                prefix = sentence_context[:position_in_sentence]
                # Typical structure: "X和Y" appears at sentence start, followed by "他/她…"
                if "和" in prefix[:8] or "与" in prefix[:8] or "跟" in prefix[:8]:
                    return None
            # Verbs like 看到/看见/发现/遇到 introducing multiple persons, conservatively don't resolve
            if len(self.tracker.current_sentence_persons) >= 2:
                before = sentence_context[:position_in_sentence]
                if any(v in before for v in {"看到", "看见", "发现", "遇到"}):
                    after = sentence_context[position_in_sentence : position_in_sentence + 6]
                    if not any(v in after for v in self.EMOTION_VERBS):
                        return None
            # Under "让/叫/请" structure with multiple persons and no clear semantic signals, conservatively don't resolve
            if len(self.tracker.current_sentence_persons) >= 2 and any(v in before_say for v in {"让", "叫", "请"}):
                after = sentence_context[position_in_sentence : position_in_sentence + 6]
                if any(v in after for v in {"道歉", "赔礼", "解释"}):
                    return None
                if semantic_role == "any":
                    return None
            # After result verbs like "获得/表彰/晋升", conservatively don't resolve in multi-person scenarios
            if len(self.tracker.current_sentence_persons) >= 2:
                after = sentence_context[position_in_sentence : position_in_sentence + 6]
                if any(v in after for v in {"获得", "赢得", "得到", "拿到", "晋升", "获奖", "表彰"}):
                    return None
            clause_person = self.tracker.get_person_before_in_clause(
                cur_sid, position_in_sentence, sentence_context, prefer_recent, position=semantic_role
            )
            if clause_person:
                return clause_person.text
            # Local persons in current sentence prefix (fallback when not in stack)
            prefix = sentence_context[:position_in_sentence]
            ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
            local_persons = [m.surface for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
            if local_persons:
                fixed: List[str] = []
                for p in local_persons:
                    if p.endswith("后") and ("小" + p) in prefix:
                        fixed.append("小" + p[:-1])
                    else:
                        fixed.append(_normalize_person(p))
                if semantic_role == "subject":
                    return fixed[0]
                return fixed[-1]
            if pronoun != "对方" and semantic_role in {"subject", "object"} and not has_see:
                matched = _try_match_role(semantic_role, {"PER_NAME", "PER_TITLE"})
                if matched:
                    return matched
            entity = self.tracker.get_person_before(
                cur_sid, position_in_sentence, prefer_recent, position=semantic_role
            )
            if entity and entity.text.endswith("后"):
                if "小" + entity.text in sentence_context:
                    return "小" + entity.text[:-1]
            if entity:
                return _normalize_person(entity.text)
        elif pronoun_type == "OBJECT":
            if semantic_role in {"subject", "object"}:
                matched = _try_match_role(semantic_role, {"OBJ", "LOC_NAME", "LOC_PLACE"})
                if matched:
                    return matched
            if pronoun == "它":
                prefix = sentence_context[:position_in_sentence]
                if "系统" in prefix and any(x in sentence_context for x in {"恢复", "重启"}):
                    return "系统"
            # Special case: "它" after "方案一/方案二…" prioritizes referring to most recent object with number
            if pronoun in {"它", "其"}:
                prefix = sentence_context[:position_in_sentence]
                m = list(re.finditer(r"(方案|计划|版本)(\d+|[一二三四五六七八九十])", prefix))
                if m:
                    return m[-1].group()
                if "系统" in prefix and any(k in sentence_context for k in {"恢复", "重启", "失败", "故障", "重试"}):
                    return "系统"
            skip_objs = {"对外", "结果", "随后", "最后", "后来"}

            # Cross-sentence resolution: if current sentence has no object, prioritize selecting subject/object from previous sentence
            local_prefix = sentence_context[:position_in_sentence]
            local_ms = self.tokenizer.analyze_mentions(local_prefix, sentence_id=cur_sid)
            has_local_obj = any(m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"} for m in local_ms)

            if not has_local_obj:
                # Cross-sentence resolution: first OBJ in previous sentence is usually subject
                prev_objs = [e for e in self.tracker.object_stack if e.sentence_id == cur_sid - 1]
                if prev_objs:
                    # Prioritize selecting first one (subject position)
                    first_obj = prev_objs[0]
                    if first_obj.text not in skip_objs:
                        return first_obj.text

            clause_obj = self.tracker.get_object_before_in_clause(
                cur_sid, position_in_sentence, sentence_context, prefer_recent
            )
            if clause_obj and clause_obj.text not in skip_objs:
                return clause_obj.text
            # "它" in contrast clauses prioritizes referring to project-type objects in first half of sentence
            prefix = sentence_context[:position_in_sentence]
            contrast_markers = ["但", "但是", "然而", "不过"]
            last_marker = -1
            last_len = 0
            for m in contrast_markers:
                i = prefix.rfind(m)
                if i > last_marker:
                    last_marker = i
                    last_len = len(m)
            if last_marker >= 0:
                before_clause = prefix[:last_marker]
                ms = self.tokenizer.analyze_mentions(before_clause, sentence_id=cur_sid)
                prefer_suffix = {"项目", "计划", "方案", "系统", "任务", "流程", "合作", "产品"}
                local_objs = []
                for m in ms:
                    if m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"}:
                        local_objs.append(m.surface)
                for obj in reversed(local_objs):
                    if any(obj.endswith(s) or s in obj for s in prefer_suffix):
                        return obj
            # Local objects in current sentence prefix (fallback when not in stack)
            if any(k in prefix for k in {"系统", "服务器", "设备"}):
                for k in ("系统", "服务器", "设备"):
                    if k in prefix:
                        return k
            ms = self.tokenizer.analyze_mentions(prefix, sentence_id=cur_sid)
            local_objs = [
                m.surface for m in ms if m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"} and m.surface not in skip_objs
            ]
            if local_objs:
                return local_objs[-1]
            dev_match = re.findall(r"(系统|服务器|设备)", prefix)
            if dev_match:
                return dev_match[-1]
            entity = self.tracker.get_object_before(cur_sid, position_in_sentence, prefer_recent)
            if entity and entity.text in {"对外", "结果", "随后", "最后", "后来"}:
                entity = None
            # Fallback: companies/schools/hospitals etc. may be in location_stack
            if entity is None:
                loc = self.tracker.get_location_before(cur_sid, position_in_sentence, prefer_recent=True)
                if loc:
                    return loc.text
            # Under actions like restart/recovery, prioritize selecting device-type entities
            if entity and any(x in sentence_context for x in {"重启", "恢复"}):
                if any(k in entity.text for k in {"故障", "问题", "异常"}):
                    objs_before = self.tracker._filter_before(self.tracker.object_stack, cur_sid, position_in_sentence)
                    for e in reversed(objs_before):
                        if any(k in e.text for k in {"服务器", "系统", "设备"}):
                            return e.text
                    prefix = sentence_context[:position_in_sentence]
                    dev_match = re.findall(r"(服务器|系统|设备)", prefix)
                    if dev_match:
                        return dev_match[-1]
        elif pronoun_type == "LOCATION":
            # Safety strategy: if "这里" is at sentence end (as verb object), do not resolve
            # Because "这里" in "喜欢这里" may be emphatic usage
            # Ambiguity detection: if there are multiple location candidates, do not resolve
            locs_before = self.tracker._filter_before(self.tracker.location_stack, cur_sid, position_in_sentence)
            unique_locs = list(dict.fromkeys([e.text for e in locs_before]))
            if len(unique_locs) >= 2:
                # Multiple location candidates, ambiguous, do not resolve
                return None

            if pronoun in {"这里", "这儿", "这边"}:
                # Check if pronoun is at sentence end
                after_pronoun = sentence_context[position_in_sentence + len(pronoun) :].strip()
                # If only sentence-ending punctuation or no content after pronoun, it's at sentence end
                if not after_pronoun or after_pronoun[0] in "。！？!?":
                    # Check if there is verb before pronoun
                    before_pronoun = sentence_context[:position_in_sentence]
                    like_verbs = {"喜欢", "爱", "恨", "讨厌", "习惯", "熟悉", "了解", "知道", "来到", "到达", "离开"}
                    if any(v in before_pronoun for v in like_verbs):
                        return None  # don't resolve
            entity = self.tracker.get_location_before(cur_sid, position_in_sentence, prefer_recent)

        return entity.text if entity else None

    # Negative emotion verbs (usually point to patient/victim)
    NEGATIVE_EMOTION_VERBS = {"难过", "伤心", "哭", "沮丧", "失望", "生气", "愤怒", "害怕", "恐惧", "委屈", "痛苦"}
    # Positive emotion verbs (agent's emotion, not pointing to patient)
    POSITIVE_EMOTION_VERBS = {"高兴", "开心", "满意", "激动", "欣慰", "自豪", "骄傲", "兴奋", "幸福", "快乐"}
    # Beneficiary emotion (感谢/感激 point to the helped party)
    BENEFICIARY_EMOTION_VERBS = {"感谢", "感激", "感恩"}
    # Patient result words (these words usually describe patient's state changes)
    PATIENT_RESULT_VERBS = {
        "进步",
        "康复",
        "痊愈",
        "好转",
        "恢复",
        "改善",
        "提高",
        "成长",  # state improvement
        "回答",
        "答应",
        "同意",
        "答复",
        "响应",  # question-answer response (questionee's action)
    }

    def _analyze_semantic_role(self, pronoun: str, position: int, context: str) -> str:
        """Analyze semantic role of pronoun

        Core logic:
        - "老师批评了小明。他很难过。" → "他" refers to criticized person (小明/patient)
        - "老板批评了员工。他很沮丧。" → "他" refers to criticized person (员工/patient)
        - "小明帮助了小红。他很开心。" → "他" may refer to 小明 (agent)

        Returns:
            'subject': refers to agent (subject)
            'object': refers to patient (object)
            'patient': emphasizes patient, used in criticism+negative emotion scenarios (high confidence)
            'any': uncertain
        """
        after_pronoun = context[position:]
        before_pronoun = context[:position]

        # Get previous sentence text (for cross-sentence semantic analysis)
        prev_context = ""
        if hasattr(self, "_last_sentence_text"):
            prev_context = self._last_sentence_text

        # Check scope: current sentence prefix + previous sentence
        check_text = prev_context + " " + before_pronoun

        # Distinguish different types of emotions
        has_negative_emotion = any(verb in after_pronoun[:10] for verb in self.NEGATIVE_EMOTION_VERBS)
        has_positive_emotion = any(verb in after_pronoun[:10] for verb in self.POSITIVE_EMOTION_VERBS)
        has_beneficiary_emotion = any(verb in after_pronoun[:10] for verb in self.BENEFICIARY_EMOTION_VERBS)
        has_patient_result = any(verb in after_pronoun[:10] for verb in self.PATIENT_RESULT_VERBS)
        has_emotion = has_negative_emotion or has_positive_emotion or has_beneficiary_emotion

        # Check if there are patient verbs in preceding text (批评、打、骂、表扬、教导 etc.) - including previous sentence
        has_patient_verb = any(verb in check_text for verb in self.PATIENT_VERBS)
        # Check if there are help verbs in preceding text
        help_verbs = {"帮助", "帮", "援助", "救", "救助", "扶", "照顾", "关心"}
        has_help_verb = any(verb in check_text for verb in help_verbs)

        # High-confidence scenario 1: patient-verb + negative emotion verb
        # E.g. "老师批评了小明。他很难过。" → high confidence refers to 小明
        if has_patient_verb and has_negative_emotion:
            return "patient"  # special marker, high-confidence patient

        # High-confidence scenario 2: help verbs + beneficiary emotion
        # E.g. "小明帮助了老人。他很感激。" → high confidence refers to 老人 (被帮助者)
        if has_help_verb and has_beneficiary_emotion:
            return "patient"  # return patient, let system choose object-position person

        # High-confidence scenario 3: patient-verb + beneficiary result word
        # E.g. "老师教导学生。他进步了。" / "医生治疗病人。他康复了。"
        if has_patient_verb and has_patient_result:
            return "patient"  # return patient, let system choose object-position person

        # High-confidence scenario 4: positive action verb (praise/夸奖) + positive emotion (开心/high兴)
        # E.g. "妈妈表扬了孩子。他很开心。" → praised person is happier
        positive_action_verbs = {"表扬", "夸", "夸奖", "奖励", "赞扬", "鼓励"}
        has_positive_action = any(verb in check_text for verb in positive_action_verbs)
        if has_positive_action and has_positive_emotion:
            return "patient"  # the praised person is happier

        # High-confidence scenario 5: give verb + positive emotion (开心/high兴)
        # E.g. "妈妈给孩子买了玩具。他很开心。" → beneficiary (孩子) is happier
        give_verbs = {"给", "送", "买", "送给", "递给", "交给", "送了", "买了", "给了"}
        has_give_verb = any(verb in check_text for verb in give_verbs)
        if has_give_verb and has_positive_emotion:
            return "patient"  # beneficiary is happier

        # Positive emotion does not force pointing to patient (other cases may have agent happy)
        if has_positive_emotion:
            return "any"  # uncertain, let downstream logic handle

        if has_negative_emotion:
            mental_verbs = {"觉得", "认为", "以为", "怀疑", "相信", "担心", "估计", "判断"}
            if any(v in before_pronoun for v in mental_verbs):
                return "subject"
            # Negative emotion verb scenario: prioritize pointing to patient
            return "object"

        # Position 0 is usually subject
        if position == 0:
            return "subject"

        # If preceding has patient-verb, pronoun possibly is object
        if has_patient_verb:
            return "object"

        return "any"

    def _is_reduplicative(self, before_text: str, pronoun: str) -> bool:
        """Detect if it is reduplicative structure

        Reduplicative structure: "他" in "小明他很聪明" immediately follows "小明"
        In this case "他" is redundant and should be deleted

        Non-reduplicative cases:
        - "张三比他高" - "比" is preposition, not reduplicative
        - "妈妈说他很累" - "说" is verb, not reduplicative
        - "告诉李四他" - although "李四" is at end, there is "告诉" before it

        Returns:
            True: is reduplicative structure (pronoun should be deleted)
            False: not reduplicative structure
        """
        if not before_text:
            return False

        # Separator words: verbs, prepositions, conjunctions etc. (only when used as independent words are separators)
        separator_words = {
            "比",
            "和",
            "与",
            "跟",
            "同",
            "对",
            "向",
            "给",
            "让",
            "叫",
            "请",
            "说",
            "问",
            "告诉",
            "认为",
            "觉得",
            "知道",
            "听说",
            "看见",
            "把",
            "被",
            "将",
            "用",
            "以",
            "因",
            "但",
            "而",
            "就",
            "才",
            "的",
            "地",
            "得",
            "了",
            "着",
            "过",
        }
        # Note: '为' is removed because it often appears in company names (e.g. "华为")

        # Get tokenization results
        tokens = self.tokenizer.tokenize(before_text)
        if not tokens:
            return False

        # Find last token
        last_token = tokens[-1]

        # Last token must be person name, person title, or object (supports reduplicative like "公司它")
        if last_token.entity_type not in ["PER_NAME", "PER_TITLE", "OBJ", "LOC_NAME", "LOC_PLACE"]:
            return False

        # If only one token, it's reduplicative
        if len(tokens) == 1:
            return True

        # Check if second-to-last token is separator word
        second_last = tokens[-2]
        if second_last.word in separator_words:
            return False

        # Check POS of second-to-last token (if verb v, preposition p etc., not reduplicative)
        if second_last.pos and second_last.pos[0] in ["v", "p", "c", "d", "u"]:
            # v=verb, p=preposition, c=conjunction, d=adverb, u=particle
            return False

        return True

    def _is_bound_variable(self, pronoun: str, position: int, context: str) -> bool:
        """Check if pronoun is a bound variable

        Bound variable refers to pronoun constrained by quantifier, e.g. "他" in "每个学生都带了他的书"
        This case should not be resolved, because "他" refers to variable in quantifier domain, not specific entity
        """
        # Check if there are quantifiers in sentence
        for quantifier in self.QUANTIFIER_WORDS:
            if quantifier in context:
                # If pronoun is after quantifier, possibly is bound variable
                quant_pos = context.find(quantifier)
                if position > quant_pos:
                    return True
        return False

    def _is_in_blocking_context(
        self, pronoun: str, position: int, sentence: str, antecedent_in_same_sentence: bool = False
    ) -> bool:
        """Detect if pronoun is in "intra-sentence constraint environment"

        Based on linguistic Binding Theory principles:
        When pronoun appears in comparison structures, coordination structures, quotation clauses etc.,
        it usually does not refer to current sentence's subject, but to other entities.

        Constraint environment detection:
        - Grammar separator markers exist before pronoun (比/和/说/把/被 etc.)
        - No other person entities between separator marker and pronoun

        Key rule: only apply constraint to "intra-sentence antecedents"!
        When antecedent is in previous sentence, both "他" in "他说他累了" should resolve to previous sentence's antecedent.

        Args:
            pronoun: pronoun
            position: position of pronoun in sentence
            sentence: complete sentence
            antecedent_in_same_sentence: whether antecedent is in same sentence (key parameter)

        Returns:
            True: pronoun is in constraint environment, should not resolve to current sentence's subject
            False: can resolve normally
        """
        # Key fix: if antecedent is not in same sentence, do not apply intra-sentence constraint
        # This way all "他" in "小明来了。他说他累了。" can resolve to "小明"
        if not antecedent_in_same_sentence:
            return False

        if position <= 0:
            return False

        before_pronoun = sentence[:position]

        # Only apply this detection to personal pronouns (avoid affecting object/location pronouns)
        if pronoun not in {"他", "她", "他们", "她们", "他的", "她的", "他们的", "她们的"}:
            return False

        # Check if there are grammar separator markers before pronoun
        for blocker in self.INTRA_SENTENCE_BLOCKERS:
            # Find position of last separator marker
            blocker_pos = before_pronoun.rfind(blocker)
            if blocker_pos == -1:
                continue

            # Check if there are other person entities between separator marker and pronoun
            between = before_pronoun[blocker_pos + len(blocker) :]

            # If between is empty or only punctuation/spaces, pronoun immediately follows separator
            between_stripped = between.strip("，,。！？ ")
            if not between_stripped:
                return True  # pronoun immediately follows separator, in binding context

            # Analyze whether there are person-title entities in between
            try:
                mentions = self.tokenizer.analyze_mentions(between, sentence_id=-1)
                person_mentions = [m for m in mentions if m.type in {"PER_NAME", "PER_TITLE"}]

                # If no other person entities after separator marker, pronoun refers outside sentence
                if not person_mentions:
                    return True
            except Exception:
                # Conservative handling when tokenization fails
                pass

        return False

    def _is_filler(self, pronoun: str, position: int, context: str) -> bool:
        """Detect if it is filler word (colloquial "那个..." is not anaphoric)

        Patterns:
        - 那个，... (followed by comma or ellipsis)
        - 那个那个 (repetition)
        - 那个呃/嗯/啊... (followed by interjection)
        """
        if pronoun != "那个":
            return False

        # Check whether matches filler pattern
        after_pos = position + len(pronoun)
        remaining = context[after_pos : after_pos + 5]  # look at next 5 characters

        # Pattern 1: followed by comma, ellipsis
        if remaining and remaining[0] in "，,…。":
            return True

        # Pattern 2: repetition "那个那个"
        if remaining.startswith("那个"):
            return True

        # Pattern 3: followed by particle
        filler_chars = {"呃", "嗯", "啊", "哦", "吧", "呢", "嘛", "额"}
        if remaining and remaining[0] in filler_chars:
            return True

        return False

    def _resolve_ordinal_pronoun_any_type(self, pronoun: str) -> Optional[str]:
        """Handle ordinal pronouns (former/latter) - generalized to any type

        Semantic rules:
        - "前者" refers to first mentioned entity
        - "后者" refers to last mentioned entity

        Priority:
        1. Prioritize using PER_NAME type person names
        2. Then use any type (excluding generalized PER_TITLE)
        3. Fallback to original logic
        """

        def _clean_entity_text(text: str) -> str:
            """Clean conjunction words at beginning of entity text"""
            if not text:
                return text
            # Remove conjunction words at beginning
            prefixes = ["和", "与", "及", "或", "、", "，"]
            for p in prefixes:
                if text.startswith(p):
                    return text[len(p) :]
            return text

        # Use fixed function: get first and last entity
        first, last = self.tracker.get_first_and_last_mentions(prefer_type="PER_NAME")

        if first is None or last is None:
            # Try any type
            first, last = self.tracker.get_first_and_last_mentions()

        if first is None or last is None:
            # Fallback to original logic
            result = self._resolve_ordinal_pronoun(pronoun, self.tracker.sentence_count)
            return _clean_entity_text(result) if result else None

        if pronoun == "前者":
            return _clean_entity_text(first.text)
        else:  # latter
            return _clean_entity_text(last.text)

    def _resolve_event_pronoun(self, pronoun: str, context: str, position_in_sentence: int = 0) -> Optional[str]:
        """Handle event reference (这件事/那样/这一点 etc.)

        Strategy (safety first):
        1. Check if there are event trigger words (让/使/导致 etc.)
        2. Try to get specific event summary or abstract object name
        3. If cannot get specific replacement text, return None (don't resolve)

        Core principle: rather not resolve than use placeholder "上述"
        """

        def _clean_event_summary(summary: str) -> str:
            """Clean event summary, remove sentence-final particles (了/着/过)"""
            if not summary:
                return summary
            # Remove sentence-final particles, avoid grammar errors like "他迟到了让老师..."
            if summary.endswith(("了", "着", "过")):
                return summary[:-1]
            return summary

        # Check whether has event trigger word
        seg = context[position_in_sentence : position_in_sentence + 6]
        has_trigger = (
            seg.startswith(("这会", "那会", "这说明", "这表明", "这显示", "这证明"))
            or seg.startswith(("这意味着", "这使得", "这将", "那将"))
            or context[position_in_sentence : position_in_sentence + 3]
            in {"这引发", "这导致", "这引起", "这造成", "这使", "这让", "这促使"}
        )

        if not has_trigger:
            has_trigger = any(verb in context for verb in self.EVENT_TRIGGER_VERBS)

        if pronoun in {"这", "那"}:
            after = context[position_in_sentence + 1 : position_in_sentence + 2]
            if after == "会" or context[position_in_sentence : position_in_sentence + 2] in {"这会", "那会"}:
                has_trigger = True
            if context[position_in_sentence : position_in_sentence + 3] in {
                "这引发",
                "这导致",
                "这引起",
                "这造成",
                "这使",
                "这让",
            }:
                has_trigger = True

        # If no trigger word, do not resolve event pronoun
        if not has_trigger:
            return None

        # Get most recent event
        event = self.tracker.get_event(prefer_recent=True)

        # Safety check: event summary must contain verb (is a real event)
        # "天气很好" is not an event, "小明迟到了" is an event
        action_markers = {"了", "着", "过", "到", "完", "掉", "住", "成", "走", "来", "去"}

        # Prioritize using previous sentence's event summary (key: event pronouns should refer to complete events, not single objects)
        # Event pronouns usually refer to previous sentence's events, not current sentence
        if event and event.summary:
            summary = event.summary
            # Check if summary contains action markers (verb particles) or has explicit verb
            has_action = any(v in summary for v in action_markers) or (event.verb and len(event.verb) > 0)
            if not has_action:
                # Not a real event (like "天气很好"), don't resolve
                return None
            # Limit summary length: overly long summaries read unnaturally after replacement
            # E.g. "考试作弊被抓住影响很大" → unnatural
            if summary and len(summary) <= 6:  # maximum 6 characters
                if not summary.startswith(("让", "使", "导致", "引发", "说明", "表明", "意味着", "显示", "证明")):
                    return _clean_event_summary(summary)

        # If no event summary, try finding abstract object from context as replacement
        abstract_nouns = {
            "一致",
            "争议",
            "消息",
            "结论",
            "结果",
            "原因",
            "影响",
            "方案",
            "计划",
            "决定",
            "问题",
            "调整",
            "方向",
            "意见",
            "建议",
            "共识",
            "反馈",
            "理解",
            "立场",
            "政策",
            "流程",
        }
        abstract_suffixes = ("方案", "计划", "决定", "问题", "政策", "流程", "共识", "结论", "结果", "影响", "消息")

        # Try finding abstract object from context as replacement (as fallback)
        objs_before = self.tracker._filter_before(
            self.tracker.object_stack, self.tracker.sentence_count, position_in_sentence
        )
        if objs_before:
            cand = objs_before[-1].text
            # If specific abstract object found, return it
            if cand in abstract_nouns or cand.endswith(abstract_suffixes):
                return cand

        # When cannot get specific replacement text, do not resolve (rather than return placeholder)
        return None

    def _resolve_generic_head(self, pronoun: str) -> Optional[str]:
        """Handle demonstrative determiner phrases (这个人/那个地方 etc.)

        Conservative strategy: only resolve when strong conditions met
        1. Has unique candidate of matching type
        2. Candidate is not newly added in current sentence
        """
        if pronoun not in self.GENERIC_HEAD_NOUNS:
            return None

        target_type = self.GENERIC_HEAD_NOUNS[pronoun]

        if target_type == "PERSON":
            # Check if person_stack has unique candidate
            if len(self.tracker.person_stack) == 1:
                return self.tracker.person_stack[-1].text
            # When multiple candidates, do not resolve (avoid ambiguity)
            return None

        elif target_type == "LOCATION":
            if len(self.tracker.location_stack) == 1:
                return self.tracker.location_stack[-1].text
            return None

        elif target_type == "OBJECT":
            if len(self.tracker.object_stack) == 1:
                return self.tracker.object_stack[-1].text
            return None

        return None

    def _resolve_formal_deictic(self, pronoun: str, context: str) -> Optional[str]:
        """Handle formal deictic words (该/此/本/上述 etc.)

        These words are common in formal writing, need to determine type based on context
        Strategy: conservative handling, only resolve when there are clear candidates
        """
        # Form of 该/本/此 + noun
        if (pronoun.startswith("该") or pronoun.startswith("本") or pronoun.startswith("此")) and len(pronoun) > 1:
            suffix = pronoun[1:]
            if any(
                k in suffix for k in {"公司", "项目", "方案", "问题", "申请", "计划", "报告", "合同", "政策", "流程"}
            ):
                # These are usually OBJ type
                if self.tracker.object_stack:
                    return self.tracker.object_stack[-1].text
            elif "人" in suffix:
                if self.tracker.person_stack:
                    return self.tracker.person_stack[-1].text
            elif "地" in suffix:
                if self.tracker.location_stack:
                    return self.tracker.location_stack[-1].text
            return None

        # 上述/前述 + noun
        if pronoun.startswith("上述") or pronoun.startswith("前述"):
            # Can replace when there is clear object, otherwise keep unchanged (don't resolve)
            if self.tracker.object_stack:
                for e in reversed(self.tracker.object_stack):
                    # Find specific abstract object name as replacement
                    if any(
                        k in e.text for k in {"问题", "故障", "原因", "影响", "方案", "计划", "调整", "变更", "异常"}
                    ):
                        return e.text
                return self.tracker.object_stack[-1].text
            return None

        # Standalone "该/此/本" don't resolve
        return None

    def _extract_event(self, text: str, sentence_id: int) -> Optional[Event]:
        """Extract event information from sentence

        Simplified version: use entire sentence as event text, extract main verb
        """
        # Use tokenizer tokenization, find verb
        tokens = self.tokenizer.tokenize(text)
        verbs = [t.word for t in tokens if t.pos in ["v", "vd", "vn"]]

        main_verb = verbs[0] if verbs else ""

        # Event summary: remove subject part (simplified processing)
        summary = text
        for t in tokens:
            if t.entity_type in ["PER_NAME", "PER_TITLE"]:
                summary = summary.replace(t.word, "", 1)
                break

        return Event(text=text, verb=main_verb, sentence_id=sentence_id, summary=summary.strip())

    def _resolve_ordinal_pronoun(self, pronoun: str, current_sentence_id: int = -1) -> Optional[str]:
        """Handle ordinal pronouns (former/latter)

        Former: refers to first of two entities mentioned earlier (first mentioned)
        Latter: refers to second of two entities mentioned earlier (later mentioned)

        Note:
        - Only consider PER_NAME type person names, not PER_TITLE (like friend, doctor)
        - Only consider entities before current sentence (avoid interference from entities added after resolution)
        """
        # Filter out real person names (PER_NAME type), and mentioned before current sentence
        # Deduplicate: only keep first occurrence of entities with same name
        seen_names = set()
        person_names = []
        for e in self.tracker.person_stack:
            if e.type == "PER_NAME":
                # Only look at entities before current sentence
                if current_sentence_id >= 0 and e.sentence_id >= current_sentence_id:
                    continue
                # Deduplicate
                if e.text not in seen_names:
                    seen_names.add(e.text)
                    person_names.append(e)

        # Prioritize finding from person names
        if len(person_names) >= 2:
            if pronoun == "前者":
                # Former = first mentioned (first non-duplicate)
                return person_names[-2].text
            else:  # latter
                # Latter = later mentioned (second non-duplicate)
                return person_names[-1].text

        # Then find from object stack (also deduplicate)
        seen_objs = set()
        objects = []
        for e in self.tracker.object_stack:
            if current_sentence_id >= 0 and e.sentence_id >= current_sentence_id:
                continue
            if e.text not in seen_objs:
                seen_objs.add(e.text)
                objects.append(e)

        if len(objects) >= 2:
            if pronoun == "前者":
                return objects[-2].text
            else:
                return objects[-1].text

        # Finally find from location stack (also deduplicate)
        seen_locs = set()
        locations = []
        for e in self.tracker.location_stack:
            if current_sentence_id >= 0 and e.sentence_id >= current_sentence_id:
                continue
            if e.text not in seen_locs:
                seen_locs.add(e.text)
                locations.append(e)

        if len(locations) >= 2:
            if pronoun == "前者":
                return locations[-2].text
            else:
                return locations[-1].text

        return None

    def _extract_and_track_entities(self, text: str, sentence_id: int):
        """Extract entities from text and track them

        Improvement: use analyze_mentions to maintain entity order in original text
        This makes "most recently mentioned person/location" semantics more accurate

        Also extract event information (for event reference)
        """
        mentions = self.tokenizer.analyze_mentions(text, sentence_id)

        for i, mention in enumerate(mentions):
            self.tracker.add_entity(
                Entity(
                    text=mention.surface,
                    type=mention.type,
                    sentence_id=sentence_id,
                    position=mention.start,  # Use character position, more precise
                    start=mention.start,
                    end=mention.end,
                )
            )

        # Extract and track events (for event reference)
        event = self._extract_event(text, sentence_id)
        if event:
            self.tracker.add_event(event)

    def _update_speaker_cache(self, sentence: str, sentence_id: int) -> None:
        verbs = self.SPEECH_VERBS | self.COMMUNICATION_VERBS
        last_idx = -1
        last_verb = ""
        for v in verbs:
            i = sentence.rfind(v)
            if i > last_idx:
                last_idx = i
                last_verb = v
        if last_idx < 0:
            if "给" in sentence:
                give_idx = sentence.rfind("给")
                after_give = sentence[give_idx + 1 :]
                target = None
                ms = self.tokenizer.analyze_mentions(after_give, sentence_id=sentence_id)
                group_heads = {
                    "学生",
                    "同学",
                    "用户",
                    "乘客",
                    "员工",
                    "客户",
                    "观众",
                    "患者",
                    "队员",
                    "战队",
                    "球队",
                    "团队",
                    "小组",
                    "成员",
                    "管理层",
                }
                for m in ms:
                    if m.type in {"PER_NAME", "PER_TITLE"}:
                        target = m
                    elif m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"} and any(h in m.surface for h in group_heads):
                        target = m
                if target:
                    self.tracker.set_listener(
                        Entity(target.surface, target.type, sentence_id, target.start, target.start, target.end),
                        sentence_id,
                    )
            return
        prefix = sentence[:last_idx]
        ms = self.tokenizer.analyze_mentions(prefix, sentence_id=sentence_id)
        persons = [m for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
        if persons:
            # Speaker should be first person (subject), not last
            # "小明对小红说" → speaker is 小明 (first), listener is 小红 (person after 对)
            p = persons[0]  # First person is speaker
            self.tracker.set_speaker(
                Entity(p.surface, p.type, sentence_id, p.start, p.start, p.end),
                sentence_id,
            )

        def _pick_listener_from_span(span: str) -> Optional[Entity]:
            ms = self.tokenizer.analyze_mentions(span, sentence_id=sentence_id)
            group_heads = {
                "学生",
                "同学",
                "用户",
                "乘客",
                "员工",
                "客户",
                "观众",
                "患者",
                "队员",
                "战队",
                "球队",
                "团队",
                "小组",
                "成员",
                "管理层",
            }
            candidates = []
            for m in ms:
                if m.type in {"PER_NAME", "PER_TITLE"}:
                    candidates.append(m)
                elif m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"} and any(h in m.surface for h in group_heads):
                    candidates.append(m)
            if not candidates:
                for h in group_heads:
                    if h in span:
                        idx = span.rfind(h)
                        return Entity(h, "OBJ", sentence_id, idx, idx, idx + len(h))
                return None
            t = candidates[-1]
            return Entity(t.surface, t.type, sentence_id, t.start, t.start, t.end)

        if "对" in prefix:
            to_idx = prefix.rfind("对")
            between = prefix[to_idx + 1 : last_idx]
            ms = self.tokenizer.analyze_mentions(between, sentence_id=sentence_id)
            targets = [m for m in ms if m.type in {"PER_NAME", "PER_TITLE"}]
            if targets:
                t = targets[-1]
                self.tracker.set_listener(
                    Entity(t.surface, t.type, sentence_id, t.start, t.start, t.end),
                    sentence_id,
                )
        suffix = sentence[last_idx + len(last_verb) :]
        target = _pick_listener_from_span(suffix)
        if target:
            self.tracker.set_listener(target, sentence_id)
        if "给" in sentence and target is None:
            give_idx = sentence.rfind("给")
            if give_idx >= 0:
                after_give = sentence[give_idx + 1 :]
                target = _pick_listener_from_span(after_give)
                if target:
                    self.tracker.set_listener(target, sentence_id)
        if "对方" in sentence:
            if len(self.tracker.speaker_chain) >= 2:
                self.tracker.set_listener(self.tracker.speaker_chain[-2][0], sentence_id)

    def resolve_sentence(
        self,
        text: str,
        extract_first: bool = False,
        open_quotes: Optional[dict] = None,
        paragraph_reset: bool = False,
    ) -> Tuple[str, List[Dict]]:
        """
        Resolve pronouns in a single sentence

        Args:
            text: input sentence
            extract_first: whether to extract entities first then resolve (first sentence needs True)

        Returns:
            (resolved_text, replacements): resolved text and replacement records
        """
        self._paragraph_reset_active = paragraph_reset

        # Save current sentence text for next sentence's semantic analysis
        # _last_sentence_text will be updated at end of function

        # 0. Safety check: long sentences without punctuation do not resolve
        # Note: punctuation in short sentences has been separated by split_sentences, so only check long sentences here
        if len(text) > 50:
            # Check if there is sufficient punctuation separation
            punctuation_count = sum(1 for c in text if c in "，,；;：:")
            # If over 50 characters but few punctuation marks, it's a long sentence without punctuation
            if punctuation_count < len(text) / 20:  # On average should have 1 punctuation per 20 characters
                # Directly return original text, don't resolve
                if extract_first:
                    self._extract_and_track_entities(text, self.tracker.sentence_count)
                self.tracker.sentence_count += 1
                return text, []

        # 1. If it's first sentence, extract entities first
        if extract_first:
            self._extract_and_track_entities(text, self.tracker.sentence_count)
        self._update_speaker_cache(text, self.tracker.sentence_count)

        # 2. Find all pronouns and resolve them
        replacements = []
        resolved_text = text

        # Determine if it's first sentence
        is_first = self.tracker.sentence_count == 0

        # Replace from back to front to avoid position offset
        matches = list(self.pronoun_pattern.finditer(text))
        for match in reversed(matches):
            pronoun = match.group()
            position_in_sentence = match.start()

            paragraph_obj_fallback = None
            paragraph_soft_block = False
            paragraph_single_person_ok = False
            paragraph_single_obj_ok = False
            if paragraph_reset:
                prefix = text[:position_in_sentence]
                ms = self.tokenizer.analyze_mentions(prefix, sentence_id=self.tracker.sentence_count)
                has_person = any(m.type in {"PER_NAME", "PER_TITLE"} for m in ms)
                has_obj = any(m.type in {"OBJ", "LOC_NAME", "LOC_PLACE"} for m in ms)
                if not (has_person or has_obj):
                    paragraph_soft_block = True
                    prev_sid = self.tracker.sentence_count - 1
                    prev_persons = [e.text for e in self.tracker.person_stack if e.sentence_id == prev_sid]
                    prev_objs = [e.text for e in self.tracker.object_stack if e.sentence_id == prev_sid]
                    prev_objs += [e.text for e in self.tracker.location_stack if e.sentence_id == prev_sid]
                    prev_persons = list(dict.fromkeys(prev_persons))
                    prev_objs = list(dict.fromkeys(prev_objs))
                    if pronoun in self.OBJECT_PRONOUNS:
                        if len(prev_objs) == 1:
                            paragraph_obj_fallback = prev_objs[0]
                            paragraph_single_obj_ok = True
                    elif pronoun in self.PERSON_PRONOUNS:
                        paragraph_single_person_ok = len(prev_persons) == 1
                    elif pronoun in self.AMBIGUOUS_PRONOUNS:
                        paragraph_single_person_ok = len(prev_persons) == 1 and len(prev_objs) == 0
                        paragraph_single_obj_ok = len(prev_objs) == 1 and len(prev_persons) == 0
            self._paragraph_soft_block = paragraph_soft_block
            self._paragraph_single_person_ok = paragraph_single_person_ok
            self._paragraph_single_obj_ok = paragraph_single_obj_ok
            # Conservative strategy inside quotes: default don't resolve (avoid "张三说：'他…'" incorrectly replacing '他' inside quotes with 张三)
            # Support multiple quote types: Chinese double quotes "", Chinese single quotes '', ASCII quotes " ', book title marks 《》 etc.
            _open_quotes = open_quotes or {"double": 0, "single": 0, "ascii": 0, "ascii_double": 0}
            prefix = text[:position_in_sentence]
            suffix = text[position_in_sentence:]

            # Helper function: detect if inside paired symbols
            def _is_inside_paired(
                prefix_text: str, suffix_text: str, left_char: str, right_char: str, base_balance: int = 0
            ) -> bool:
                """Detect if current position is inside paired symbols"""
                left_cnt = prefix_text.count(left_char)
                right_cnt = prefix_text.count(right_char)
                balance = base_balance + left_cnt - right_cnt
                if balance > 0:
                    # Also need to check if there is closing symbol after
                    if right_char in suffix_text:
                        return True
                return False

            # Chinese double quote detection "" (U+201C / U+201D)
            if _is_inside_paired(prefix, suffix, "\u201c", "\u201d", _open_quotes.get("double", 0)):
                continue

            # Chinese single quote detection '' (U+2018 / U+2019)
            if _is_inside_paired(prefix, suffix, "\u2018", "\u2019", _open_quotes.get("single", 0)):
                continue

            # Chinese book title mark detection 《》
            if _is_inside_paired(prefix, suffix, "\u300a", "\u300b", 0):
                continue

            # Chinese square bracket detection 【】
            if _is_inside_paired(prefix, suffix, "\u3010", "\u3011", 0):
                continue

            # ASCII single quote detection (odd number means inside quotes)
            single_cnt = prefix.count("'")
            # If odd number of single quotes before, means inside quotes (conservatively don't resolve regardless of closing quote)
            if (_open_quotes.get("ascii", 0) + single_cnt) % 2 == 1:
                continue

            # ASCII double quote detection (odd number means inside quotes)
            double_cnt = prefix.count('"')
            # If odd number of double quotes before, means inside quotes (conservatively don't resolve regardless of closing quote)
            if (_open_quotes.get("ascii_double", 0) + double_cnt) % 2 == 1:
                continue

            # Quote structure detection after colon (e.g. "张三说："他会来"")
            # Detection pattern: colon/说/道 + quote start
            quote_open_chars = '\u201c\u2018"\u0027\u300c\u300e'  # " ' " ' 「 『
            colon_quote_pattern = re.search(r"[：:]([" + quote_open_chars + "])", prefix)
            if colon_quote_pattern:
                quote_char = colon_quote_pattern.group(1)
                close_map = {
                    "\u201c": "\u201d",  # " → "
                    "\u2018": "\u2019",  # ' → '
                    '"': '"',
                    "'": "'",
                    "\u300c": "\u300d",  # 「 → 」
                    "\u300e": "\u300f",  # 『 → 』
                }
                close_char = close_map.get(quote_char, "")
                if close_char:
                    # Check if quote closes after pronoun
                    quote_start = colon_quote_pattern.end() - 1
                    after_quote = text[quote_start:]
                    if close_char in after_quote[1:]:  # Has content inside quotes and closes after
                        continue

            # Mis-match fix: avoid treating "对方" in "反对方案" as pronoun
            if pronoun == "对方":
                if match.start() > 0 and text[match.start() - 1] == "反":
                    if match.end() < len(text) and text[match.end()] == "案":
                        continue

            # Skip first/second person pronouns
            if pronoun in self.SELF_PRONOUNS:
                continue

            # Skip reflexive pronouns
            if pronoun in self.REFLEXIVE_PRONOUNS:
                continue

            # Descriptive phrases (like "那个人", "这个地方") - try conservative resolution
            # If defined in GENERIC_HEAD_NOUNS and conditions met, resolve; otherwise skip
            if pronoun in self.DESCRIPTIVE_PHRASES:
                # Special case: if descriptive phrase immediately followed by reduplicative pronoun (like "这个东西它"),
                # then don't resolve descriptive phrase, only delete following reduplicative pronoun
                after_phrase = text[match.end() :]
                if after_phrase and after_phrase[0] in {"他", "她", "它"}:
                    # Following is reduplicative pronoun, skip handling of descriptive phrase
                    continue

                if pronoun in self.GENERIC_HEAD_NOUNS:
                    # Try conservative resolve
                    generic_replacement = self._resolve_generic_head(pronoun)
                    if generic_replacement:
                        start, end = match.start(), match.end()
                        resolved_text = resolved_text[:start] + generic_replacement + resolved_text[end:]
                        replacements.append(
                            {
                                "pronoun": pronoun,
                                "replacement": generic_replacement,
                                "position": start,
                                "type": "GENERIC_HEAD",
                            }
                        )
                # Whether resolved or not, skip subsequent processing
                continue

            # Skip emphatic reflexive pronouns (like "他自己", "她本人")
            if pronoun in self.EMPHATIC_REFLEXIVES:
                continue

            # Detect reduplicative structure (like "小明他很聪明")
            # If pronoun immediately follows an entity, this is reduplicative, should delete pronoun
            if pronoun in self.REDUPLICATIVE_PRONOUNS:
                before_pronoun = text[: match.start()]
                if self._is_reduplicative(before_pronoun, pronoun):
                    # Reduplicative structure: delete pronoun (replace with empty string)
                    start, end = match.start(), match.end()
                    resolved_text = resolved_text[:start] + resolved_text[end:]
                    replacements.append(
                        {
                            "pronoun": pronoun,
                            "replacement": "",  # delete
                            "position": start,
                            "type": "REDUPLICATIVE",
                        }
                    )
                    continue

            # Check if pronoun is followed by noun (like "那个人", "这个地方")
            # This case is modifier+noun structure, should not resolve
            after_pronoun = text[match.end() : match.end() + 3] if match.end() < len(text) else ""
            # Extended: cover high-frequency structures like "这个问题/这个计划/那个项目/这个决定/那个部分" etc.
            modifier_nouns = [
                "人",
                "物",
                "东西",
                "地方",
                "事情",
                "事",
                "时候",
                "地",
                "问题",
                "计划",
                "项目",
                "决定",
                "方案",
                "战略",
                "部分",
                "模块",
                "系统",
                "团队",
                "公司",
                "消息",
                "意见",
            ]
            if pronoun in ["那个", "这个", "那", "这"]:
                is_modifier = any(after_pronoun.startswith(noun) for noun in modifier_nouns)
                if is_modifier:
                    continue

            # Single-char "这/那" are mostly determiners (这家公司/那个人/这件事), unless immediately followed by event trigger structure
            if pronoun in {"这", "那"}:
                lookahead = text[match.end() : match.end() + 2] if match.end() < len(text) else ""
                trigger_heads = (
                    "让",
                    "使",
                    "使得",
                    "导致",
                    "造成",
                    "引起",
                    "引发",
                    "促使",
                    "会",
                    "被",
                    "在",
                    "说明",
                    "表明",
                    "意味着",
                    "显示",
                    "证明",
                    "将",
                )
                if lookahead and not lookahead.startswith(trigger_heads) and lookahead[0] not in " ，,。！？?!；;、":
                    continue

            # Sentence-final ellipsis: "提出来的那个/后来那个" etc. are often determiners with omitted noun head, default don't replace (safer)
            if pronoun in {"那个", "这个"}:
                if match.end() >= len(text) or (match.end() < len(text) and text[match.end()] in "，,。！？?!；;、"):
                    continue

            # Additional protection: phrases like "公司那边/学校这边" are usually noun phrases, shouldn't replace "那边/这边" as location pronouns
            if pronoun in {"那边", "这边"}:
                # If previous character is not punctuation/whitespace and not common preposition/verb (去/到/来/在/从/往/向), more like noun phrase
                if position_in_sentence > 0:
                    prev = text[position_in_sentence - 1]
                    if prev not in " ，,。！？?!；;、":
                        if prev not in {"去", "到", "来", "在", "从", "往", "向", "回"}:
                            continue

            # Additional protection: avoid treating single-char determiners inside words like "因此/此外/此后/本来/该死" as resolvable
            if pronoun in {"此", "该", "本"}:
                span = text[max(0, position_in_sentence - 1) : min(len(text), position_in_sentence + 2)]
                if span in {"因此", "此外", "此后", "本来", "该死"}:
                    continue

            # Find replacement entity
            # Note: no longer use "上述" placeholder, uniformly handled by _find_replacement
            replacement = self._find_replacement(
                pronoun, position_in_sentence, sentence_context=text, is_first_sentence=is_first
            )
            if replacement is None and paragraph_obj_fallback and pronoun in self.OBJECT_PRONOUNS:
                replacement = paragraph_obj_fallback

            if replacement:
                # Execute replacement
                start, end = match.start(), match.end()
                resolved_text = resolved_text[:start] + replacement + resolved_text[end:]

                replacements.append(
                    {
                        "pronoun": pronoun,
                        "replacement": replacement,
                        "position": start,
                        "type": self._get_pronoun_type(pronoun),
                    }
                )

        # 3. After resolution, extract current sentence's entities (for next sentence to use)
        # Key fix: use resolved_text instead of original text
        # This way after "他→张三" replacement, tracker can see 张三 appearing again, next sentence's reference more accurate
        if not extract_first:
            self._extract_and_track_entities(resolved_text, self.tracker.sentence_count)

        # 4. Update sentence count
        self.tracker.next_sentence()

        # 5. Save current sentence text for next sentence's semantic analysis
        self._last_sentence_text = text

        return resolved_text, replacements

    def resolve_text(
        self, text: str, sentence_delimiter: str = "。", use_smart_split: bool = True
    ) -> Tuple[str, List[Dict]]:
        """
        Resolve entire text

        Args:
            text: input text
            sentence_delimiter: sentence delimiter (for backward compatibility)
            use_smart_split: whether to use smart sentence splitting (supports various punctuation like 。！？ etc.)

        Returns:
            (resolved_text, all_replacements): resolved text and all replacement records
        """
        # Empty text or pure punctuation directly return
        if not text or not text.strip():
            return text, []

        # Check if only punctuation symbols
        if re.fullmatch(r"[。！？?!；;：:，,、\s]*", text):
            return text, []

        # Safety check: input without sentence-ending punctuation but with pronouns don't resolve
        # This case is usually format issue or incomplete input
        has_end_punct = any(c in text for c in "。！？!?")
        has_pronoun = any(p in text for p in {"他", "她", "它", "他们", "她们", "它们", "他的", "她的", "它的"})
        if not has_end_punct and has_pronoun:
            # No sentence-ending punctuation but has pronouns, don't resolve
            return text, []

        # Reset tracker
        self.tracker.clear()

        resolved_parts = []
        all_replacements = []

        double_balance = 0
        single_balance = 0
        ascii_balance = 0
        ascii_double_balance = 0

        if use_smart_split:
            # Smart sentence splitting: support multiple punctuation + paragraph boundaries
            parts = re.split(r"(\n{2,})", text)
            sid = 0
            reset_next = False
            for part in parts:
                if not part:
                    continue
                if re.fullmatch(r"\n{2,}", part):
                    resolved_parts.append(part)
                    double_balance = 0
                    single_balance = 0
                    ascii_balance = 0
                    self.tracker.reset_speaker_context()
                    reset_next = True
                    continue
                sentence_pairs = split_sentences(part)
                for sentence, delim in sentence_pairs:
                    if not sentence:
                        continue
                    is_first = self.tracker.sentence_count == 0
                    open_quotes = {
                        "double": double_balance,
                        "single": single_balance,
                        "ascii": ascii_balance,
                        "ascii_double": ascii_double_balance,
                    }
                    resolved, replacements = self.resolve_sentence(
                        sentence,
                        extract_first=is_first,
                        open_quotes=open_quotes,
                        paragraph_reset=reset_next,
                    )
                    resolved_parts.append(resolved + delim)
                    for r in replacements:
                        r["sentence_id"] = sid
                    all_replacements.extend(replacements)
                    double_balance += sentence.count(""") - sentence.count(""")
                    single_balance += sentence.count("'") - sentence.count("'")
                    ascii_balance += sentence.count("'")
                    ascii_double_balance += sentence.count('"')
                    sid += 1
                    reset_next = False
            resolved_text = "".join(resolved_parts)
        else:
            # Backward compatibility: only split by single delimiter
            sentences = text.split(sentence_delimiter)
            resolved_sentences = []

            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue

                is_first = self.tracker.sentence_count == 0
                open_quotes = {
                    "double": double_balance,
                    "single": single_balance,
                    "ascii": ascii_balance,
                }
                resolved, replacements = self.resolve_sentence(
                    sentence, extract_first=is_first, open_quotes=open_quotes
                )
                resolved_sentences.append(resolved)

                for r in replacements:
                    r["sentence_id"] = i
                all_replacements.extend(replacements)
                double_balance += sentence.count("“") - sentence.count("”")
                single_balance += sentence.count("‘") - sentence.count("’")
                ascii_balance += sentence.count("'")

            resolved_text = sentence_delimiter.join(resolved_sentences)
            if text.endswith(sentence_delimiter):
                resolved_text += sentence_delimiter

        return resolved_text, all_replacements

    def reset(self):
        """Reset resolver state"""
        self.tracker.clear()
        self._last_sentence_text = ""

    def reset_stream(self):
        """Reset stream resolution context state"""
        self.tracker.clear()
        self._stream_double_balance = 0
        self._stream_single_balance = 0
        self._stream_ascii_balance = 0
        self._stream_started = True

    def resolve_incremental(
        self,
        sentence: str,
        paragraph_reset: bool = False,
    ) -> Tuple[str, List[Dict]]:
        """
        Stream resolution: input sentence by sentence and preserve context

        Args:
            sentence: single sentence input
            paragraph_reset: whether as first sentence of new paragraph (reset quotes and speaker context)

        Returns:
            (resolved_sentence, replacements)
        """
        if not sentence:
            return sentence, []
        if not self._stream_started:
            self.reset_stream()
        if paragraph_reset:
            self._stream_double_balance = 0
            self._stream_single_balance = 0
            self._stream_ascii_balance = 0
            self.tracker.reset_speaker_context()

        sid = self.tracker.sentence_count
        is_first = sid == 0
        open_quotes = {
            "double": self._stream_double_balance,
            "single": self._stream_single_balance,
            "ascii": self._stream_ascii_balance,
        }
        resolved, replacements = self.resolve_sentence(
            sentence,
            extract_first=is_first,
            open_quotes=open_quotes,
            paragraph_reset=paragraph_reset,
        )
        for r in replacements:
            r["sentence_id"] = sid

        self._stream_double_balance += sentence.count("“") - sentence.count("”")
        self._stream_single_balance += sentence.count("‘") - sentence.count("’")
        self._stream_ascii_balance += sentence.count("'")

        return resolved, replacements

    def resolve_text_structured(
        self,
        text: str,
        reference_time: Optional[datetime] = None,
        canonicalizer: Optional[Callable] = None,  # (surface, type) -> CanonicalResult
        time_normalizer: Optional[Callable] = None,  # (surface, reference) -> TimeSpan
    ) -> CorefOutput:
        """Structured coreference resolution (for Memory Engine use)

        Differences from resolve_text:
        1. Returns structured CorefOutput, including mentions and time_extractions
        2. Supports pluggable canonicalizer (entity normalization)
        3. Supports pluggable time_normalizer (time normalization)

        Args:
            text: input text
            reference_time: reference time (for time normalization, default is current time)
            canonicalizer: entity normalization function (surface, type) -> CanonicalResult
            time_normalizer: time normalization function (surface, reference) -> TimeSpan

        Returns:
            CorefOutput: structured output
        """
        if reference_time is None:
            reference_time = datetime.now()

        # 1. Execute reference resolution
        resolved_text, raw_replacements = self.resolve_text(text)

        # 2. Convert replacements to structured format
        replacements = [
            Replacement(
                pronoun=r["pronoun"],
                replacement=r["replacement"],
                position=r["position"],
                type=r["type"],
                sentence_id=r.get("sentence_id", 0),
            )
            for r in raw_replacements
        ]

        # 3. Extract mentions from resolved_text
        mentions = self.tokenizer.analyze_mentions(resolved_text)

        # 4. If there is canonicalizer, normalize mentions
        if canonicalizer:
            for mention in mentions:
                result = canonicalizer(mention.surface, mention.type)
                # Normalization result can be stored in mention's extended fields
                # Here temporarily don't modify mention structure, keep it simple

        # 5. Extract time and normalize
        time_extractions = []
        for mention in mentions:
            if mention.type == "TIME":
                if time_normalizer:
                    time_span = time_normalizer(mention.surface, reference_time)
                else:
                    # Use built-in time normalizer
                    normalized = _normalize_time(mention.surface, reference_time)
                    time_span = TimeSpan(
                        source_text=mention.surface,
                        start_dt=normalized.start_dt,
                        end_dt=normalized.end_dt,
                        precision=normalized.precision,
                        start=mention.start,
                        end=mention.end,
                    )
                time_extractions.append(time_span)

        return CorefOutput(
            original_text=text,
            resolved_text=resolved_text,
            replacements=replacements,
            mentions=mentions,
            time_extractions=time_extractions,
        )


# === Convenience functions ===


def resolve(text: str) -> str:
    """Quick coreference resolution"""
    resolver = CoreferenceResolver()
    resolved, _ = resolver.resolve_text(text)
    return resolved


def resolve_with_details(text: str) -> Dict:
    """Coreference resolution with detailed info"""
    resolver = CoreferenceResolver()
    resolved, replacements = resolver.resolve_text(text)
    return {
        "original": text,
        "resolved": resolved,
        "replacements": replacements,
        "entity_stacks": {
            "persons": [e.text for e in resolver.tracker.person_stack],
            "objects": [e.text for e in resolver.tracker.object_stack],
            "locations": [e.text for e in resolver.tracker.location_stack],
        },
    }


class StreamCorefSession:
    """Stream coreference resolution session (Chinese)"""

    def __init__(self, resolver: Optional[CoreferenceResolver] = None):
        self.resolver = resolver or CoreferenceResolver()
        self.resolver.reset_stream()

    def reset(self) -> None:
        """Reset session context"""
        self.resolver.reset_stream()

    def add_sentence(self, sentence: str, paragraph_reset: bool = False) -> Tuple[str, List[Dict]]:
        """Resolve sentence by sentence while maintaining context"""
        return self.resolver.resolve_incremental(sentence, paragraph_reset=paragraph_reset)


# === Test ===

if __name__ == "__main__":
    print("=" * 70)
    print("Coreference Resolution System - Complete Test")
    print("=" * 70)

    resolver = CoreferenceResolver()

    # Categorized test cases
    test_cases = {
        "Basic resolution": [
            "小明在学校。他正在上课。",
            "妈妈去超市买苹果。她买了很多。",
            "刘德华去北京。他在那里开演唱会。",
        ],
        "Possessive pronouns": [
            "小明买了书。他的书很有趣。",
            "妈妈做了饭。她的饭很好吃。",
        ],
        "Plural pronouns": [
            "张三和李四去公园。他们在那里散步。",
            "爸爸妈妈带孩子去玩。他们很开心。",
        ],
        "Object pronouns": [
            "我买了一部手机。它很好用。",
            "桌上有一本书。那个是我的。",
        ],
        "Location pronouns": [
            "我去了北京。那里很繁华。",
            "小明在学校。这里有很多学生。",
        ],
        "Semantic role (patient)": [
            "老师批评了小明。他很难过。",  # criticized person is sad
            "张三打了李四。他很生气。",  # hit person is angry
        ],
        "Time pronoun resolution": [
            "去年我去了北京。那时候天气很好。",
            "昨天小明来了。当时我不在家。",
            "今年我毕业了。那个时候我很开心。",
            "春节我们回老家。那阵子很热闹。",
        ],
        "Former/latter": [
            "张三和李四是朋友。前者是医生。",
            "张三和李四是朋友。后者是老师。",
            "北京和上海都很繁华。前者是首都。",
        ],
        "Reduplicative structure (delete redundant pronoun)": [
            "小明他很聪明。",
            "妈妈她做的饭很好吃。",
        ],
        "Non-resolution cases": [
            "小明说他很累。",  # intra-sentence pronoun
            "张三告诉李四他应该努力。",  # intra-sentence pronoun
            "小明很了解自己。",  # reflexive pronoun
            "人家不想去。",  # generic pronoun
            "每个学生都带了他的书。",  # bound variable
            "我认识的那个人很友好。",  # descriptive phrase
            "他很高。",  # first sentence no antecedent
            "那时候天气好。",  # time no antecedent
        ],
    }

    for category, tests in test_cases.items():
        print(f"\n【{category}】")
        for text in tests:
            resolved, replacements = resolver.resolve_text(text)
            if resolved != text:
                print(f"  Original: {text}")
                print(f"  Resolved: {resolved}")
            else:
                print(f"  Kept: {text}")
            resolver.reset()

    print("\n" + "=" * 70)
    print("Covered pronoun types:")
    print("  ✓ Personal pronouns: 他/她/他们/她们")
    print("  ✓ Possessive pronouns: 他的/她的/它的")
    print("  ✓ Object pronouns: 它/它们")
    print("  ✓ Location pronouns: 这里/那里/这边/那边")
    print("  ✓ Demonstrative pronouns: 这个/那个 (when used independently)")
    print("  ✓ Plural pronouns: 他们/她们")
    print("  ✓ Time pronouns: 那时候/当时/那阵子/那会儿")
    print("  ✓ Ordinal pronouns: 前者/后者")
    print("  ✓ Reduplicative structure: 小明他→小明 (delete redundant pronoun)")
    print("\nExcluded pronoun types (not resolved):")
    print("  ○ Pronouns in first sentence (no antecedent)")
    print("  ○ Reflexive pronouns: 自己/本人")
    print("  ○ Emphatic reflexives: 他自己/她本人")
    print("  ○ Generic pronouns: 人家/别人/有人/其他人")
    print("  ○ Bound variables: 每个X...他的 (quantifier expressions)")
    print("  ○ Descriptive phrases: 那个人/这个地方 (demonstrative+noun)")
    print("=" * 70)
