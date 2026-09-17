#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
English coreference resolution: rule-first, conservative replacement.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .ner_adapter import Entity, EnglishNerAdapter
from .tokenizer import EnglishTokenizer


@dataclass
class Replacement:
    sentence_id: int
    position: int
    pronoun: str
    replacement: str
    start: int
    end: int


class EntityTracker:
    def __init__(self, max_history: int = 10) -> None:
        """
        Initialize EntityTracker with bounded history.

        Args:
            max_history: Maximum number of entities to keep in each stack.
                        Higher values improve resolution accuracy but use more memory.
        """
        self.max_history = max_history
        self.person_stack: deque = deque(maxlen=max_history)
        self.object_stack: deque = deque(maxlen=max_history)
        self.location_stack: deque = deque(maxlen=max_history)
        self.group_stack: deque = deque(maxlen=max_history)
        self.time_stack: deque = deque(maxlen=max_history)
        self.event_stack: deque = deque(maxlen=max_history)
        self.sentence_count = 0
        self.sentence_texts: List[str] = []

    def clear(self) -> None:
        self.person_stack.clear()
        self.object_stack.clear()
        self.location_stack.clear()
        self.group_stack.clear()
        self.time_stack.clear()
        self.event_stack.clear()
        self.sentence_count = 0
        self.sentence_texts.clear()

    def next_sentence(self) -> None:
        self.sentence_count += 1

    def set_sentence_text(self, sentence_id: int, text: str) -> None:
        if sentence_id == len(self.sentence_texts):
            self.sentence_texts.append(text)
        elif 0 <= sentence_id < len(self.sentence_texts):
            self.sentence_texts[sentence_id] = text

    def get_prev_sentence_text(self, sentence_id: int) -> Optional[str]:
        if sentence_id <= 0:
            return None
        if sentence_id - 1 < len(self.sentence_texts):
            return self.sentence_texts[sentence_id - 1]
        return None

    def add(self, entity: Entity) -> None:
        if entity.type in {"PER", "PER_TITLE"}:
            self.person_stack.append(entity)
        elif entity.type in {"GROUP"}:
            self.group_stack.append(entity)
        elif entity.type in {"LOC_ORG"}:
            self.location_stack.append(entity)
        elif entity.type == "TIME":
            self.time_stack.append(entity)
        elif entity.type == "EVENT":
            self.event_stack.append(entity)
        else:
            self.object_stack.append(entity)

    def _filter_before(self, items: List[Entity], sentence_id: int, pos: int) -> List[Entity]:
        out: List[Entity] = []
        for e in items:
            if e.sentence_id < sentence_id:
                out.append(e)
            elif e.sentence_id == sentence_id and e.start < pos:
                out.append(e)
        return out

    def get_person_before(
        self,
        sentence_id: int,
        pos: int,
        role: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> Optional[Entity]:
        items = self._filter_before(self.person_stack, sentence_id, pos)
        if not items:
            return None
        candidates = items
        # Filter by gender first (if available), then by role; fallback if empty after filtering
        if gender:
            gender_items = [e for e in candidates if e.gender == gender]
            if gender_items:
                candidates = gender_items
        if role:
            role_items = [e for e in candidates if e.role == role]
            if role_items:
                candidates = role_items
        return candidates[-1]

    def get_object_before(self, sentence_id: int, pos: int) -> Optional[Entity]:
        items = self._filter_before(self.object_stack, sentence_id, pos)
        return items[-1] if items else None

    def get_location_before(self, sentence_id: int, pos: int) -> Optional[Entity]:
        items = self._filter_before(self.location_stack, sentence_id, pos)
        return items[-1] if items else None

    def get_group_before(self, sentence_id: int, pos: int) -> Optional[Entity]:
        items = self._filter_before(self.group_stack, sentence_id, pos)
        return items[-1] if items else None

    def get_event_before(self, sentence_id: int, pos: int) -> Optional[Entity]:
        items = self._filter_before(self.event_stack, sentence_id, pos)
        return items[-1] if items else None

    def get_objects_text_before(self, sentence_id: int, pos: int) -> Optional[str]:
        objs = self._filter_before(self.object_stack, sentence_id, pos)
        if len(objs) < 2:
            return None
        # Use most recent sentence only
        last_sid = max(e.sentence_id for e in objs)
        same = [e for e in objs if e.sentence_id == last_sid]
        # If subject role exists, prefer subject set
        subj = [e for e in same if e.role == "SUBJ"]
        if len(subj) >= 2:
            # Merge other OBJs in same sentence (deduplicate keeping order)
            merged: List[Entity] = []
            for e in same:
                if e in subj or e.role == "SUBJ":
                    merged.append(e)
            for e in same:
                if e not in merged:
                    merged.append(e)
            same = merged
        names: List[str] = []
        for e in same:
            if e.text not in names:
                names.append(e.text)
        if len(names) < 2:
            return None
        if len(names) == 2:
            return names[0] + " and " + names[1]
        return ", ".join(names[:-1]) + " and " + names[-1]

    def get_objects_text_before_obj_only(self, sentence_id: int, pos: int) -> Optional[str]:
        objs = self._filter_before(self.object_stack, sentence_id, pos)
        if not objs:
            return None
        last_sid = max(e.sentence_id for e in objs)
        same = [e for e in objs if e.sentence_id == last_sid and e.role != "SUBJ"]
        if not same:
            return None
        names: List[str] = []
        for e in same:
            if e.text not in names:
                names.append(e.text)
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return names[0] + " and " + names[1]
        return ", ".join(names[:-1]) + " and " + names[-1]

    def get_objects_subjects_text_before(self, sentence_id: int, pos: int) -> Optional[str]:
        objs = self._filter_before(self.object_stack, sentence_id, pos)
        if len(objs) < 2:
            return None
        last_sid = max(e.sentence_id for e in objs)
        same = [e for e in objs if e.sentence_id == last_sid and e.role == "SUBJ"]
        names: List[str] = []
        for e in same:
            if e.text not in names:
                names.append(e.text)
        if len(names) < 2:
            return None
        if len(names) == 2:
            return names[0] + " and " + names[1]
        return ", ".join(names[:-1]) + " and " + names[-1]

    def get_persons_text_before(self, sentence_id: int, pos: int) -> Optional[str]:
        persons = self._filter_before(self.person_stack, sentence_id, pos)
        if len(persons) < 2:
            return None
        last_sid = max(e.sentence_id for e in persons)
        same = [e for e in persons if e.sentence_id == last_sid]
        names: List[str] = []
        for e in same:
            if e.text not in names:
                names.append(e.text)
        if len(names) < 2:
            return None
        if len(names) == 2:
            return names[0] + " and " + names[1]
        return ", ".join(names[:-1]) + " and " + names[-1]

    def get_groups_text_before(self, sentence_id: int, pos: int) -> Optional[str]:
        groups = self._filter_before(self.group_stack, sentence_id, pos)
        if len(groups) < 2:
            return None
        last_sid = max(e.sentence_id for e in groups)
        same = [e for e in groups if e.sentence_id == last_sid]
        names: List[str] = []
        for e in same:
            if e.text not in names and e.norm not in names:
                names.append(e.text)
        if len(names) < 2:
            return None
        if len(names) == 2:
            return names[0] + " and " + names[1]
        return ", ".join(names[:-1]) + " and " + names[-1]

    def get_locations_text_before(self, sentence_id: int, pos: int) -> Optional[str]:
        locs = self._filter_before(self.location_stack, sentence_id, pos)
        if len(locs) < 2:
            return None
        last_sid = max(e.sentence_id for e in locs)
        same = [e for e in locs if e.sentence_id == last_sid]
        names: List[str] = []
        for e in same:
            if e.text not in names and e.norm not in names:
                names.append(e.text)
        if len(names) < 2:
            return None
        if len(names) == 2:
            return names[0] + " and " + names[1]
        return ", ".join(names[:-1]) + " and " + names[-1]

    def has_multiple_persons_before(self, sentence_id: int, pos: int) -> bool:
        # Only consider multi-person ambiguity within current sentence
        persons = [e for e in self.person_stack if e.sentence_id == sentence_id and e.start < pos]
        uniq = []
        for e in persons:
            key = e.norm or e.text
            if key not in uniq:
                uniq.append(key)
        return len(uniq) >= 2

    def has_multiple_subjects_in_prev_sentence(self, sentence_id: int) -> bool:
        prev = [e for e in self.person_stack if e.sentence_id == sentence_id - 1 and e.role == "SUBJ"]
        uniq = []
        for e in prev:
            key = e.norm or e.text
            if key not in uniq:
                uniq.append(key)
        if len(uniq) >= 2:
            return True
        # If single SUBJ entity is itself a conjunction (Alice and Bob), also treat as ambiguous
        for e in prev:
            if " and " in e.text.lower() or "," in e.text:
                return True
        return False

    def has_multiple_persons_in_prev_sentence(self, sentence_id: int) -> bool:
        prev = [e for e in self.person_stack if e.sentence_id == sentence_id - 1]
        uniq = []
        for e in prev:
            key = e.norm or e.text
            if key not in uniq:
                uniq.append(key)
        return len(uniq) >= 2

    def has_gender_in_prev_sentence(self, sentence_id: int, gender: str) -> bool:
        if not gender:
            return False
        prev = [e for e in self.person_stack if e.sentence_id == sentence_id - 1 and e.gender == gender]
        return len(prev) > 0

    def count_gender_in_prev_sentence(self, sentence_id: int, gender: str) -> int:
        if not gender:
            return 0
        prev = [e for e in self.person_stack if e.sentence_id == sentence_id - 1 and e.gender == gender]
        uniq = []
        for e in prev:
            key = e.norm or e.text
            if key not in uniq:
                uniq.append(key)
        return len(uniq)

    def has_duplicate_person_norms_in_prev_sentence(self, sentence_id: int) -> bool:
        prev = [e for e in self.person_stack if e.sentence_id == sentence_id - 1]
        norms = [e.norm or e.text for e in prev]
        return len(norms) != len(set(norms))


class CoreferenceResolver:
    PERSON_PRONOUNS = {"he", "she", "him", "her"}
    PLURAL_PERSON_PRONOUNS = {"they", "them"}
    OBJECT_PRONOUNS = {"it"}
    POSSESSIVE_PRONOUNS = {"his", "her", "its", "their"}
    DEICTIC = {"this", "that", "these", "those"}
    GENERIC = {"someone", "anyone", "people", "others"}

    EVENT_TRIGGERS = {
        "cause",
        "caused",
        "lead",
        "led",
        "result",
        "resulted",
        "mean",
        "meant",
        "make",
        "made",
        "makes",
        "trigger",
        "triggered",
        "spark",
        "sparked",
        "improve",
        "improved",
        "increase",
        "increased",
        "create",
        "created",
        "affect",
        "affected",
        "boost",
        "boosted",
        "reduce",
        "reduced",
        "reassure",
        "reassured",
        "frustrate",
        "frustrated",
        "hurt",
        "hurts",
        "harmed",
        "harm",
        "annoy",
        "annoyed",
        "upset",
        "force",
        "forced",
        "delay",
        "delayed",
        "surprise",
        "surprised",
        "strengthen",
        "strengthened",
        "embarrass",
        "embarrassed",
        "extend",
        "extended",
        "align",
        "aligned",
        "restore",
        "restored",
        "shock",
        "shocked",
        "prompt",
        "prompted",
        "ignore",
        "ignored",
        "end",
        "ended",
        "alarm",
        "alarmed",
        "confuse",
        "confused",
    }
    COMMUNICATION_VERBS = {
        "called",
        "call",
        "emailed",
        "email",
        "texted",
        "text",
        "messaged",
        "message",
        "contacted",
        "contact",
        "phoned",
        "phone",
        "asked",
        "ask",
    }
    EVENT_REPORT_VERBS = {
        "announce",
        "announced",
        "decide",
        "decided",
        "reject",
        "rejected",
        "approve",
        "approved",
        "agree",
        "agreed",
        "delay",
        "delayed",
        "postpone",
        "postponed",
        "confirm",
        "confirmed",
        "reach",
        "reached",
        "deny",
        "denied",
        "warn",
        "warned",
        "state",
        "stated",
        "note",
        "noted",
        "dismiss",
        "dismissed",
        "resign",
        "resigned",
        "close",
        "closed",
        "issue",
        "issued",
    }
    COMM_VERBS = {"email", "emailed", "forward", "forwarded", "send", "sent", "message", "messaged"}
    HARD_EVENT_VERBS = {"crash", "crashed", "fail", "break", "collapse", "fall", "reopen", "reopened"}
    SPEECH_VERBS = {"said", "told", "thought", "believed", "argued", "claimed", "noted", "reported", "stated"}
    GENERIC_ORG_NOUNS = {
        "company",
        "firm",
        "organization",
        "org",
        "team",
        "group",
        "department",
        "committee",
        "board",
        "agency",
        "startup",
    }

    def __init__(self, max_history: int = 10) -> None:
        """
        Initialize CoreferenceResolver.

        Args:
            max_history: Maximum number of historical entities to keep in tracker stacks.
                        Higher values improve resolution accuracy for longer conversations
                        but consume more memory. Recommended range: 5-50.
        """
        self.max_history = max_history
        self.tokenizer = EnglishTokenizer()
        self.ner_adapter = EnglishNerAdapter()
        self.tracker = EntityTracker(max_history=max_history)
        self._stream_started = False

    def _pronoun_type(self, p: str) -> str:
        if p in self.GENERIC:
            return "GENERIC"
        if p in self.PERSON_PRONOUNS:
            return "PERSON"
        if p in self.PLURAL_PERSON_PRONOUNS:
            return "PLURAL_PERSON"
        if p in self.OBJECT_PRONOUNS:
            return "OBJECT"
        if p in self.POSSESSIVE_PRONOUNS:
            return "POSS"
        if p in self.DEICTIC:
            return "DEICTIC"
        return "OTHER"

    def _is_inside_quotes(self, text: str, pos: int) -> bool:
        # Conservatively do not resolve within quotes (supports English and Chinese quotes)
        left_en = text[:pos].count('"')
        left_cn = text[:pos].count("“")
        right_cn = text[:pos].count("”")
        in_en = left_en % 2 == 1
        in_cn = left_cn > right_cn
        return in_en or in_cn

    def resolve_text(self, text: str) -> Tuple[str, List[Replacement]]:
        self.tracker.clear()
        doc = self.tokenizer.parse(text)
        replacements: List[Replacement] = []

        for sid, sent in enumerate(doc.sents):
            # mention -> entities
            sent_text = sent.text
            self.tracker.set_sentence_text(sid, sent_text)
            mentions = self.tokenizer.analyze_mentions(sent_text)
            entities = self.ner_adapter.normalize(mentions, sentence_id=sid)
            self._apply_weak_alias_link(entities)
            for e in entities:
                self.tracker.add(e)
            self._maybe_add_event(sent_text, sid, entities)

            # pronoun scan (token-based with global positions)
            repls = self._resolve_sentence(sent, sid)
            replacements.extend(repls)

            self.tracker.next_sentence()

        # Apply replacements on original text in reverse order by global start
        out_text = text
        for r in sorted(replacements, key=lambda x: x.start, reverse=True):
            if r.replacement.strip().lower() == r.pronoun:
                continue
            out_text = out_text[: r.start] + r.replacement + out_text[r.end :]

        return out_text, replacements

    def reset_stream(self) -> None:
        """Reset streaming coreference context state"""
        self.tracker.clear()
        self._stream_started = True

    def resolve_incremental(self, sentence: str, paragraph_reset: bool = False) -> Tuple[str, List[Replacement]]:
        """
        Stream resolution: input sentence by sentence and preserve context
        """
        if not sentence:
            return sentence, []
        if not self._stream_started:
            self.reset_stream()
        if paragraph_reset:
            self.reset_stream()

        doc = self.tokenizer.parse(sentence)
        sents = list(doc.sents)
        if not sents:
            return sentence, []
        sent = sents[0]
        sid = self.tracker.sentence_count
        sent_text = sent.text
        self.tracker.set_sentence_text(sid, sent_text)

        mentions = self.tokenizer.analyze_mentions(sent_text)
        entities = self.ner_adapter.normalize(mentions, sentence_id=sid)
        self._apply_weak_alias_link(entities)
        for e in entities:
            self.tracker.add(e)
        self._maybe_add_event(sent_text, sid, entities)

        replacements = self._resolve_sentence(sent, sid)
        self.tracker.next_sentence()

        out_text = sent_text
        for r in sorted(replacements, key=lambda x: x.start, reverse=True):
            if r.replacement.strip().lower() == r.pronoun:
                continue
            out_text = out_text[: r.start] + r.replacement + out_text[r.end :]

        return out_text, replacements

    def _resolve_sentence(self, sent, sid: int) -> List[Replacement]:
        repls: List[Replacement] = []
        sent_text = sent.text
        quote_spans = self._quote_spans(sent_text)

        # Reverse replacement to avoid position drift
        for tok in reversed(list(sent)):
            if tok.is_space:
                continue
            p = tok.text.lower()
            if not p or p not in (
                self.PERSON_PRONOUNS
                | self.PLURAL_PERSON_PRONOUNS
                | self.OBJECT_PRONOUNS
                | self.POSSESSIVE_PRONOUNS
                | self.DEICTIC
                | self.GENERIC
            ):
                continue
            if p == "that":
                if tok.dep_ in {"nsubj", "nsubjpass", "obj", "dobj"} and tok.head.dep_ in {"relcl", "acl", "ccomp"}:
                    continue
            # Filter out "that" used as conjunction/complementizer
            if p == "that" and tok.dep_ == "mark":
                continue
            gpos = tok.idx
            if p in {"he", "she"} and sid > 0:
                prev_text = self.tracker.get_prev_sentence_text(sid)
                prev_text = prev_text.strip().lower() if prev_text else ""
                cur_text = sent_text.strip().lower()
                if prev_text and prev_text.startswith("who ") and cur_text.startswith(("he did", "she did")):
                    continue
            if self._is_inside_quotes(sent.doc.text, gpos):
                # Within quotes: if explicit entity found inside, allow local resolution
                local_rep = self._resolve_inside_quote(p, tok.idx - sent.start_char, sent_text, sid, quote_spans)
                if local_rep and local_rep.strip().lower() != p:
                    repls.append(
                        Replacement(
                            sentence_id=sid,
                            position=tok.idx - sent.start_char,
                            pronoun=p,
                            replacement=local_rep,
                            start=gpos,
                            end=gpos + len(tok.text),
                        )
                    )
                continue

            if p in self.GENERIC:
                continue

            is_possessive = tok.dep_ == "poss" or tok.tag_ == "PRP$"
            role_hint = None
            gender_hint = None
            if p in {"he", "she"}:
                role_hint = "SUBJ"
                gender_hint = "M" if p == "he" else "F"
            elif p in {"him", "her"} and not is_possessive:
                role_hint = "OBJ"
                gender_hint = "M" if p == "him" else "F"
            elif p in {"they", "them"}:
                if tok.dep_ in {"nsubj", "nsubjpass"}:
                    role_hint = "SUBJ"
                elif tok.dep_ in {"dobj", "pobj"}:
                    role_hint = "OBJ"
            elif p == "it" and tok.dep_ in {"nsubj", "nsubjpass"}:
                role_hint = "SUBJ"
            replacement = self._find_replacement(
                p,
                sid,
                tok.idx - sent.start_char,
                sent_text,
                role_hint=role_hint,
                force_possessive=is_possessive,
                gender_hint=gender_hint,
            )
            if replacement and replacement.strip().lower() != p:
                repls.append(
                    Replacement(
                        sentence_id=sid,
                        position=tok.idx - sent.start_char,
                        pronoun=p,
                        replacement=replacement,
                        start=gpos,
                        end=gpos + len(tok.text),
                    )
                )

        return repls

    def _apply_weak_alias_link(self, entities: List[Entity]) -> None:
        """
        Weak alias linking: bind generic organization names like "the company/team/organization"
        to the most recently appeared specific organization norm (without changing original text).
        """
        # Find most recent specific organization
        last_specific = None
        for e in reversed(self.tracker.location_stack):
            if e.norm and e.norm not in self.GENERIC_ORG_NOUNS:
                last_specific = e
                break
        if not last_specific:
            return
        for e in entities:
            if e.type == "LOC_ORG" and e.norm in self.GENERIC_ORG_NOUNS:
                e.norm = last_specific.norm

    def _quote_spans(self, sent: str) -> List[Tuple[int, int]]:
        spans: List[Tuple[int, int]] = []
        idx = 0
        while idx < len(sent):
            start = sent.find('"', idx)
            if start == -1:
                break
            end = sent.find('"', start + 1)
            if end == -1:
                break
            spans.append((start + 1, end))
            idx = end + 1
        return spans

    def _resolve_inside_quote(
        self,
        pronoun: str,
        pos: int,
        sent: str,
        sid: int,
        quote_spans: List[Tuple[int, int]],
    ) -> Optional[str]:
        # Find the quote range containing current pronoun
        span = None
        for s, e in quote_spans:
            if s <= pos <= e:
                span = (s, e)
                break
        if span is None:
            return None
        left = sent[span[0] : pos]
        if not left.strip():
            return None
        # Build local entity stack from left side within quotes
        mentions = self.tokenizer.analyze_mentions(left)
        entities = self.ner_adapter.normalize(mentions, sentence_id=sid)
        if not entities:
            return None
        local_tracker = EntityTracker()
        for e in entities:
            local_tracker.add(e)
        return self._find_replacement(pronoun, sid, pos, sent, tracker=local_tracker)

    def _maybe_add_event(self, sent: str, sid: int, entities: List[Entity]) -> None:
        """
        Coarse-grained event tracking: when sentence contains action verbs like decide/veto/announce/postpone/agree,
        push most recent abstract object as event summary onto stack.
        """
        lower = sent.lower()
        obj_text = self.tokenizer.extract_event_summary(sent, self.EVENT_REPORT_VERBS)
        if "warned" in lower:
            obj_text = "warning"
        # Communication verbs prefer supplementing with "message"
        if not obj_text and any(v in lower for v in self.COMM_VERBS):
            obj_text = "message"
        if not obj_text:
            # fallback: prefer abstract objects (OBJ)
            obj_text = None
            for e in reversed(entities):
                if e.type == "OBJ":
                    obj_text = e.text
                    break
        if obj_text:
            pronoun_like = (
                self.PERSON_PRONOUNS
                | self.PLURAL_PERSON_PRONOUNS
                | self.OBJECT_PRONOUNS
                | self.POSSESSIVE_PRONOUNS
                | self.DEICTIC
                | self.GENERIC
            )
            if obj_text.strip().lower() in pronoun_like:
                obj_text = None
        if not obj_text:
            # Non-report sentence event: use ROOT verb summary
            root = self.tokenizer.extract_root_verb(sent)
            if root and root in self.HARD_EVENT_VERBS:
                obj_text = root
        if not obj_text:
            return
        ev = Entity(text=obj_text, type="EVENT", start=0, end=0, sentence_id=sid)
        self.tracker.event_stack.append(ev)

    COMMON_MALE_NAMES = {"john", "bob", "tom", "jerry", "mike", "smith", "daniel", "mark", "noah", "liam", "alex"}
    COMMON_FEMALE_NAMES = {
        "mary",
        "alice",
        "sarah",
        "lee",
        "ms",
        "mrs",
        "miss",
        "emily",
        "lena",
        "mia",
        "emma",
        "ava",
        "zoe",
        "iris",
        "olivia",
        "nina",
    }

    def _extract_gendered_person(self, compound_text: str, gender: str) -> Optional[str]:
        """Extract person of specified gender from conjoined persons

        e.g.: "Alice and Bob" + gender="F" -> "Alice"
              "Alice and Bob" + gender="M" -> "Bob"
        """
        # Split conjoined persons
        text = compound_text.strip()
        parts = []
        if " and " in text.lower():
            # Handle "X and Y" form
            parts = [p.strip() for p in text.split(" and ") if p.strip()]
            # Handle "X, Y and Z" form
            if len(parts) == 2:
                if ", " in parts[0]:
                    sub_parts = [p.strip() for p in parts[0].split(", ") if p.strip()]
                    parts = sub_parts + [parts[1]]

        if not parts:
            return None

        # Find person matching gender
        for part in parts:
            name = part.lower().strip()
            if gender == "F" and name in self.COMMON_FEMALE_NAMES:
                return part
            if gender == "M" and name in self.COMMON_MALE_NAMES:
                return part

        return None

    def _prefer_specific_org(self, sid: int, pos: int) -> Optional[Entity]:
        # Prefer non-generic organization names from recent entities
        items = self.tracker._filter_before(self.tracker.location_stack, sid, pos)
        for e in reversed(items):
            if e.norm and e.norm not in self.GENERIC_ORG_NOUNS:
                return e
        return items[-1] if items else None

    def _obj_text(self, obj: Entity) -> str:
        if obj.norm:
            return obj.norm
        text = obj.text
        low = text.lower()
        for p in ("its ", "their ", "his ", "her ", "my ", "our ", "your "):
            if low.startswith(p):
                return text[len(p) :]
        return text

    def _find_replacement(
        self,
        p: str,
        sid: int,
        pos: int,
        sent: str,
        tracker: Optional[EntityTracker] = None,
        role_hint: Optional[str] = None,
        force_possessive: bool = False,
        gender_hint: Optional[str] = None,
    ) -> Optional[str]:
        tracker = tracker or self.tracker
        # Event trigger: this/that + verb
        if p in {"this", "that"}:
            right = sent[pos : pos + 50].lower()
            if any(t in right for t in self.EVENT_TRIGGERS):
                ev = tracker.get_event_before(sid, pos)
                if ev:
                    if " " not in ev.text and ev.text.lower().endswith("ed"):
                        return "the above"
                    return ev.text
                obj = tracker.get_object_before(sid, pos)
                if obj:
                    if " during " in sent.lower():
                        return "the above"
                    return obj.text
                return "the above"

        # possessive
        if p in {"his", "her"} and force_possessive:
            # Ambiguity protection: do not replace when multiple persons in same sentence
            if tracker.has_multiple_persons_before(sid, pos):
                if gender_hint:
                    cand = [
                        e
                        for e in tracker.person_stack
                        if e.sentence_id == sid and e.start < pos and e.gender == gender_hint
                    ]
                    if len({c.norm or c.text for c in cand}) != 1:
                        return None
                else:
                    return None
            ent = tracker.get_person_before(sid, pos, role=role_hint, gender=gender_hint)
            return ent.text + "'s" if ent else None
        if p in {"its", "their"} and force_possessive:
            if p == "its":
                if (" this " in sent.lower() or " that " in sent.lower()) and any(
                    t in sent.lower() for t in self.EVENT_TRIGGERS
                ):
                    return None
            if p == "their":
                persons = tracker.get_persons_text_before(sid, pos)
                if persons:
                    return persons + "'s"
                groups = tracker.get_groups_text_before(sid, pos)
                if groups:
                    return groups + "'s"
                subj_objs = tracker.get_objects_subjects_text_before(sid, pos)
                if subj_objs:
                    return subj_objs + "'s"
                objs = tracker.get_objects_text_before(sid, pos)
                if objs:
                    return objs + "'s"
            obj = tracker.get_object_before(sid, pos)
            if obj:
                return self._obj_text(obj) + "'s"
            loc = self._prefer_specific_org(sid, pos)
            return loc.text + "'s" if loc else None

        # person
        if p in self.PERSON_PRONOUNS:
            before = sent[:pos].lower()
            if sent.lower().startswith("who ") and role_hint == "SUBJ":
                return None
            if ('"' not in sent) and any(
                v in before for v in {" said ", " told ", " wrote ", " reported ", " claimed ", " stated ", " noted "}
            ):
                return None
            if role_hint == "SUBJ" and "questioned" in sent.lower() and "witness" in sent.lower():
                return None
            if gender_hint:
                gender_items = [
                    e
                    for e in tracker.person_stack
                    if e.sentence_id == sid and e.start < pos and e.gender == gender_hint
                ]
                if len({g.norm or g.text for g in gender_items}) == 1:
                    return gender_items[-1].text
            if ";" in sent:
                same = [e for e in tracker.person_stack if e.sentence_id == sid and e.start < pos]
                if len({e.norm or e.text for e in same}) >= 2:
                    return None
            if role_hint == "SUBJ":
                same = [e for e in tracker.person_stack if e.sentence_id == sid and e.start < pos]
                if len({e.norm or e.text for e in same}) >= 2 and (
                    ", and " in before or "; " in before or " and " in before
                ):
                    return None
            if tracker.has_multiple_persons_before(sid, pos):
                if " and " in before and not gender_hint:
                    return None
                if role_hint == "SUBJ":
                    subj = [
                        e for e in tracker.person_stack if e.sentence_id == sid and e.start < pos and e.role == "SUBJ"
                    ]
                    if len({s.norm or s.text for s in subj}) == 1:
                        pass
                    else:
                        return None
                if gender_hint:
                    same_sent = [
                        e
                        for e in tracker.person_stack
                        if e.sentence_id == sid and e.start < pos and e.gender == gender_hint
                    ]
                    if same_sent:
                        if len({c.norm or c.text for c in same_sent}) != 1:
                            return None
                else:
                    return None
            # "told" structure: X told Y that he... usually ambiguous, conservatively do not replace
            if (
                role_hint == "SUBJ"
                and " told " in before
                and len({e.norm or e.text for e in tracker.person_stack if e.sentence_id == sid and e.start < pos}) >= 2
            ):
                return None
            # Conservatively do not replace when multiple persons in because-clause
            if (
                " because " in before
                and len({e.norm or e.text for e in tracker.person_stack if e.sentence_id == sid and e.start < pos}) >= 2
            ):
                return None
            if (
                " briefed " in before
                and len({e.norm or e.text for e in tracker.person_stack if e.sentence_id == sid and e.start < pos}) >= 2
            ):
                return None
            if role_hint == "OBJ" and "thanked" in sent.lower():
                if len({e.norm or e.text for e in tracker.person_stack if e.sentence_id == sid and e.start < pos}) >= 2:
                    return None
            # If previous sentence has multiple subjects, avoid cross-sentence hard binding
            if role_hint == "SUBJ" and tracker.has_multiple_subjects_in_prev_sentence(sid):
                return None
            # If previous sentence has multiple persons with unique gender match, prefer by gender
            if gender_hint and tracker.has_multiple_persons_in_prev_sentence(sid):
                if tracker.count_gender_in_prev_sentence(sid, gender_hint) == 1:
                    ent = tracker.get_person_before(sid, pos, gender=gender_hint)
                    return ent.text if ent else None
                prev_text = tracker.get_prev_sentence_text(sid)
                if prev_text and any(v in prev_text.lower() for v in self.SPEECH_VERBS):
                    prev_subj = [e for e in tracker.person_stack if e.sentence_id == sid - 1 and e.role == "SUBJ"]
                    if len({e.norm or e.text for e in prev_subj}) == 1:
                        ent = prev_subj[-1]
                        if ent.gender == gender_hint or not ent.gender:
                            return ent.text
                return None
            # If same-name person in previous sentence, avoid cross-sentence misreference
            if tracker.has_duplicate_person_norms_in_prev_sentence(sid):
                return None
            # If previous sentence is a quote/speech, prefer anaphora to speaker (SUBJ)
            prev_text = tracker.get_prev_sentence_text(sid)
            if prev_text and any(v in prev_text.lower() for v in self.SPEECH_VERBS):
                prev_subj = [e for e in tracker.person_stack if e.sentence_id == sid - 1 and e.role == "SUBJ"]
                if len({e.norm or e.text for e in prev_subj}) == 1:
                    ent = prev_subj[-1]
                    if gender_hint and ent.gender and ent.gender != gender_hint:
                        pass
                    else:
                        return ent.text
            # "he said he..." nested structure: latter pronoun is more likely ambiguous
            if any(v in before for v in self.SPEECH_VERBS) and before.count(p) >= 1:
                return None
            ent = tracker.get_person_before(sid, pos, role=role_hint, gender=gender_hint)
            if ent:
                # If conjoined entity with singular pronoun (he/she), try extracting matching gender individual
                if gender_hint and (" and " in ent.text.lower() or ", " in ent.text):
                    extracted = self._extract_gendered_person(ent.text, gender_hint)
                    if extracted:
                        return extracted
                    # If cannot extract, return None to avoid ambiguous replacement
                    return None
                return ent.text
            return None

        # plural person
        if p in self.PLURAL_PERSON_PRONOUNS:
            if role_hint == "OBJ":
                objs = [e for e in tracker.person_stack if e.sentence_id == sid and e.start < pos and e.role == "OBJ"]
                if len({o.norm or o.text for o in objs}) == 1:
                    return objs[-1].text
            if role_hint == "SUBJ" and sid > 0:
                prev_objs = [e for e in tracker.person_stack if e.sentence_id == sid - 1 and e.role == "OBJ"]
                if len({o.norm or o.text for o in prev_objs}) == 1:
                    return prev_objs[-1].text
            persons = tracker.get_persons_text_before(sid, pos)
            if persons:
                return persons
            # Allow anaphora when single merged person entity contains conjunction
            same_sent_persons = [e for e in tracker.person_stack if e.sentence_id == sid and e.start < pos]
            if same_sent_persons:
                last_person = same_sent_persons[-1]
                lp_text = last_person.text.lower()
                if " and " in lp_text or "," in lp_text:
                    return last_person.text
            # Allow anaphora when previous sentence has only one conjoined/group entity
            if sid > 0:
                prev_persons = [e for e in tracker.person_stack if e.sentence_id == sid - 1]
                if len(prev_persons) == 1:
                    p_text = prev_persons[0].text.lower()
                    if " and " in p_text or "," in p_text or any(ch.isdigit() for ch in p_text):
                        return prev_persons[0].text
                prev = tracker.get_prev_sentence_text(sid)
                if prev:
                    try:
                        doc = self.tokenizer.parse(prev)
                        subj = None
                        for tok in doc:
                            if tok.dep_ in {"nsubj", "nsubjpass"}:
                                subj = tok
                                break
                        if subj is not None:
                            span = doc[subj.left_edge.i : subj.right_edge.i + 1]
                            span_text = span.text
                            low_span = span_text.lower()
                            tokens = {t.text.lower().strip(",") for t in span}
                            if (" and " in low_span or "," in low_span) and any(
                                t in self.ner_adapter.PERSON_TITLES for t in tokens
                            ):
                                return span_text
                    except Exception:
                        pass
            groups = tracker.get_groups_text_before(sid, pos)
            if groups:
                return groups
            obj_single = tracker.get_object_before(sid, pos)
            before = sent[:pos].lower()
            generic_hit = None
            for g in self.GENERIC:
                idx = before.rfind(g)
                if idx != -1:
                    generic_hit = g
            if generic_hit in {"people", "others"}:
                return generic_hit
            if generic_hit in {"someone", "anyone"} and not obj_single:
                return generic_hit
            single_group = tracker.get_group_before(sid, pos)
            if p == "they" and single_group:
                return single_group.text
            objs_only = tracker.get_objects_text_before_obj_only(sid, pos)
            if objs_only:
                return objs_only
            objs = tracker.get_objects_text_before(sid, pos)
            if objs:
                return objs
            if obj_single and obj_single.text.lower().endswith("s") and p in {"they", "them", "their"}:
                return obj_single.text
            if p == "them" and obj_single:
                return obj_single.text
            if obj_single and obj_single.text.lower().endswith("s") and p in {"they", "them", "their"}:
                return obj_single.text
            if obj_single and obj_single.text.lower().endswith("s"):
                return obj_single.text
            locs = tracker.get_locations_text_before(sid, pos)
            if locs:
                return locs
            ent = tracker.get_person_before(sid, pos)
            return ent.text if ent else None

        # object
        if p in self.OBJECT_PRONOUNS:
            # Conservatively do not replace "it" after report/speech verbs
            before = sent[:pos].lower()
            pronoun_like = (
                self.PERSON_PRONOUNS
                | self.PLURAL_PERSON_PRONOUNS
                | self.OBJECT_PRONOUNS
                | self.POSSESSIVE_PRONOUNS
                | self.DEICTIC
                | self.GENERIC
            )
            if any(v in before for v in self.SPEECH_VERBS | self.COMM_VERBS):
                if before.count('"') % 2 == 0 and '"' in before:
                    return "the above"
                if "“" in before and "”" in before and before.rfind("”") > before.rfind("“"):
                    return "the above"
            if sent.lower().lstrip().startswith("if "):
                obj = tracker.get_object_before(sid, pos)
                if obj:
                    return self._obj_text(obj)
                grp = tracker.get_group_before(sid, pos)
                if grp:
                    return grp.text
                loc = self._prefer_specific_org(sid, pos)
                if loc:
                    return loc.text
                ent = tracker.get_person_before(sid, pos)
                return ent.text if ent else None
            lower_sent = sent.lower().lstrip()
            if lower_sent.startswith(("it was ", "it seems ", "it is ")) and " that " in lower_sent:
                return None
            if not self._is_inside_quotes(sent, pos):
                if ('"' in before or "“" in before or "”" in before) and any(
                    v in before for v in self.SPEECH_VERBS | self.COMM_VERBS
                ):
                    return "the above"
            prev = tracker.get_prev_sentence_text(sid)
            if prev and ('"' in prev or "“" in prev or "”" in prev):
                if any(v in prev.lower() for v in self.SPEECH_VERBS | self.COMM_VERBS):
                    return "the above"
            if any(v in sent.lower() for v in ("reopen", "reboot", "rebooted", "restart", "reset")):
                grp = tracker.get_group_before(sid, pos)
                if grp:
                    return grp.text
                loc = self._prefer_specific_org(sid, pos)
                if loc:
                    return loc.text
                # Device-type priority
                keywords = {"server", "system", "device", "machine", "host"}
                objs_before = tracker._filter_before(tracker.object_stack, sid, pos)
                for e in reversed(objs_before):
                    if any(k in e.text.lower() for k in keywords):
                        return self._obj_text(e)
            if role_hint == "SUBJ":
                if "ignored" in sent.lower():
                    ev = tracker.get_event_before(sid, pos)
                    if ev:
                        return ev.text
                    objs_before = tracker._filter_before(tracker.object_stack, sid, pos)
                    for e in reversed(objs_before):
                        if "warning" in e.text.lower():
                            return self._obj_text(e)
                objs_before = tracker._filter_before(tracker.object_stack, sid, pos)
                obj_role = [e for e in objs_before if e.role == "OBJ"]
                if obj_role:
                    abstract = {"debate", "discussion", "meeting", "talks", "conversation", "hearing"}
                    last_obj = obj_role[-1]
                    last_tokens = set(last_obj.text.lower().replace(".", "").split())
                    if abstract.intersection(last_tokens):
                        for e in reversed(obj_role[:-1]):
                            tokens = set(e.text.lower().replace(".", "").split())
                            if not abstract.intersection(tokens):
                                return self._obj_text(e)
                    return self._obj_text(last_obj)
                subj_objs = [e for e in objs_before if e.role == "SUBJ"]
                if subj_objs:
                    return self._obj_text(subj_objs[-1])
                if any(
                    v in sent.lower()
                    for v in ("revised", "revise", "amended", "amend", "updated", "update", "reviewed", "review")
                ):
                    ev = tracker.get_event_before(sid, pos)
                    if ev:
                        return ev.text
                obj = tracker.get_object_before(sid, pos)
                if obj and obj.text.lower() not in pronoun_like:
                    ev = tracker.get_event_before(sid, pos)
                    if ev and obj.text.lower() in {"debate", "discussion", "meeting", "talks", "conversation"}:
                        return ev.text
                    if any(
                        v in sent.lower()
                        for v in ("revised", "revise", "amended", "amend", "updated", "update", "reviewed", "review")
                    ):
                        objs_before = tracker._filter_before(tracker.object_stack, sid, pos)
                        for e in reversed(objs_before):
                            if e.text.lower() not in {
                                "debate",
                                "discussion",
                                "meeting",
                                "talks",
                                "conversation",
                                "hearing",
                            }:
                                return self._obj_text(e)
                    return self._obj_text(obj)
                subj_objs = [e for e in tracker.object_stack if e.sentence_id <= sid and e.role == "SUBJ"]
                if subj_objs:
                    return self._obj_text(subj_objs[-1])
                if any(
                    v in sent.lower()
                    for v in ("revised", "revise", "amended", "amend", "updated", "update", "reviewed", "review")
                ):
                    ev = tracker.get_event_before(sid, pos)
                    if ev:
                        return ev.text
                prev = tracker.get_prev_sentence_text(sid)
                if prev and ('"' in prev or "“" in prev or "”" in prev):
                    if any(v in prev.lower() for v in self.SPEECH_VERBS | self.COMM_VERBS):
                        return "the above"
                grp = tracker.get_group_before(sid, pos)
                if grp:
                    return grp.text
                loc = self._prefer_specific_org(sid, pos)
                if loc:
                    return loc.text
            if any(v in before for v in self.SPEECH_VERBS):
                obj = tracker.get_object_before(sid, pos)
                if obj:
                    return self._obj_text(obj)
                return None
            # Conservatively do not replace when multiple objects before "but"
            if " but " in before:
                objs_before = tracker._filter_before(tracker.object_stack, sid, pos)
                if len({o.norm or o.text for o in objs_before}) >= 2:
                    return None
            # Conservatively do not replace for same-sentence this/that event + its/it combo
            if " this " in sent.lower() or " that " in sent.lower():
                if any(t in sent.lower() for t in self.EVENT_TRIGGERS):
                    return None
            ev = tracker.get_event_before(sid, pos)
            if ev and ev.text.lower() == "warning":
                return ev.text
            if "ignored" in sent.lower():
                if ev:
                    return ev.text
                objs_before = tracker._filter_before(tracker.object_stack, sid, pos)
                for e in reversed(objs_before):
                    if "warning" in e.text.lower():
                        return self._obj_text(e)
            if any(v in sent.lower() for v in ("reverse", "reversed")):
                ev = tracker.get_event_before(sid, pos)
                if ev:
                    return ev.text
            obj = tracker.get_object_before(sid, pos)
            if obj and obj.text.lower() not in pronoun_like:
                return self._obj_text(obj)
            if ev:
                return ev.text
            grp = tracker.get_group_before(sid, pos)
            if grp:
                return grp.text
            loc = self._prefer_specific_org(sid, pos)
            return loc.text if loc else None

        # deictic with noun: "this plan" => keep
        if p in self.DEICTIC:
            if p in {"this", "that"}:
                left = sent[:pos].lower().lstrip()
                if left == "" and tracker.has_multiple_subjects_in_prev_sentence(sid):
                    return "the above"
            if p in {"these", "those"}:
                objs = tracker.get_objects_text_before(sid, pos)
                if objs:
                    return objs
                groups = tracker.get_groups_text_before(sid, pos)
                if groups:
                    return groups
                locs = tracker.get_locations_text_before(sid, pos)
                if locs:
                    return locs
                obj_single = tracker.get_object_before(sid, pos)
                if obj_single and obj_single.text.lower().endswith("s"):
                    return obj_single.text
                if obj_single and (" and " in obj_single.text.lower() or "," in obj_single.text):
                    return obj_single.text
            right = sent[pos + len(p) :].lstrip()
            if right:
                # If immediately followed by noun/article, usually a determiner structure, skip replacement
                first = right.split(" ", 1)[0].strip(".,;:!?()[]{}").lower()
                if first in {"a", "an", "the"}:
                    return None
                if first.isalpha():
                    if p in {"these", "those"} and first in {
                        "changes",
                        "updates",
                        "revisions",
                        "actions",
                        "steps",
                        "measures",
                    }:
                        if sid == 0:
                            return None
                        objs = tracker.get_objects_text_before(sid, pos)
                        if objs:
                            return objs
                        groups = tracker.get_groups_text_before(sid, pos)
                        if groups:
                            return groups
                        locs = tracker.get_locations_text_before(sid, pos)
                        if locs:
                            return locs
                        return "the above"
                    if p in {"this", "that"} and (
                        first.endswith("ed")
                        or first
                        in {
                            "cause",
                            "causes",
                            "caused",
                            "trigger",
                            "triggers",
                            "triggered",
                            "prompt",
                            "prompted",
                            "clarify",
                            "clarified",
                            "reduce",
                            "reduced",
                            "extend",
                            "extended",
                            "align",
                            "aligned",
                            "shock",
                            "shocked",
                            "embarrass",
                            "embarrassed",
                            "confuse",
                            "confused",
                            "alarm",
                            "alarmed",
                            "annoy",
                            "annoyed",
                            "hurt",
                            "reassure",
                            "reassured",
                        }
                    ):
                        ev = tracker.get_event_before(sid, pos)
                        if ev:
                            return ev.text
                        obj = tracker.get_object_before(sid, pos)
                        if obj:
                            return self._obj_text(obj)
                        return "the above"
                    return None

        return None


class StreamCorefSession:
    """Streaming coreference resolution session (English)"""

    def __init__(self, resolver: Optional[CoreferenceResolver] = None) -> None:
        self.resolver = resolver or CoreferenceResolver()
        self.resolver.reset_stream()

    def reset(self) -> None:
        """Reset session context"""
        self.resolver.reset_stream()

    def add_sentence(self, sentence: str, paragraph_reset: bool = False) -> Tuple[str, List[Replacement]]:
        """Resolve sentence by sentence while preserving context"""
        return self.resolver.resolve_incremental(sentence, paragraph_reset=paragraph_reset)
