#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NER result normalization: align entity types with Chinese implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .tokenizer import Mention


@dataclass
class Entity:
    text: str
    type: str
    start: int
    end: int
    sentence_id: int
    norm: str = ""
    role: str = ""
    gender: str = ""


class EnglishNerAdapter:
    ABSTRACT_OBJECT_WORDS = {
        "plan",
        "decision",
        "issue",
        "message",
        "agreement",
        "result",
        "impact",
        "policy",
        "process",
        "proposal",
        "strategy",
        "schedule",
        "delay",
        "change",
        "adjustment",
        "problem",
        "solution",
        "idea",
        "feedback",
        "risk",
        "priority",
        "constraint",
        "goal",
        "assumption",
        "conclusion",
    }
    PERSON_TITLES = {
        "mr",
        "mrs",
        "ms",
        "dr",
        "prof",
        "ceo",
        "cfo",
        "cto",
        "manager",
        "lead",
        "director",
        "president",
        "chairman",
        "founder",
        "investor",
        "mentor",
        "client",
        "auditor",
        "lawyer",
        "editor",
        "author",
        "coach",
        "player",
        "journalist",
        "mayor",
        "minister",
        "delegate",
        "doctor",
        "patient",
        "engineer",
        "engineers",
        "designer",
        "designers",
        "analyst",
        "analysts",
        "trader",
        "traders",
        "professor",
        "student",
        "auditor",
        "teacher",
        "analyst",
        "buyer",
        "nurse",
        "vendor",
        "surgeon",
        "witness",
        "witnesses",
        "judge",
        "advisor",
    }
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
    ORG_HEADS = {
        "company",
        "team",
        "group",
        "department",
        "committee",
        "board",
        "firm",
        "organization",
        "org",
        "corp",
        "startup",
        "agency",
        "clinic",
    }
    GROUP_HEADS = {"team", "group", "department", "committee", "board"}

    def normalize(self, mentions: List[Mention], sentence_id: int) -> List[Entity]:
        entities: List[Entity] = []
        for m in mentions:
            etype = self._map_type(m)
            norm = self._normalize_text(m.text, etype)
            gender = m.gender if m.gender else (self._gender_from_text(m.text) if etype in {"PER", "PER_TITLE"} else "")
            entities.append(
                Entity(
                    text=m.text,
                    type=etype,
                    start=m.start,
                    end=m.end,
                    sentence_id=sentence_id,
                    norm=norm,
                    role=m.role,
                    gender=gender,
                )
            )
        return entities

    def _gender_from_text(self, text: str) -> str:
        t = text.strip().lower()

        # Conjunction (X and Y) may contain different genders, return empty gender
        if " and " in t or ", " in t:
            return ""

        if t.startswith("mr ") or t.startswith("mr.") or t == "mr":
            return "M"
        if t.startswith("mrs ") or t.startswith("mrs.") or t == "mrs":
            return "F"
        if t.startswith("ms ") or t.startswith("ms.") or t == "ms":
            return "F"
        if t.startswith("miss ") or t == "miss":
            return "F"
        # Lightweight guess based on common English names
        last = t.replace(".", "").split()[-1] if t.replace(".", "").split() else ""
        if last in self.COMMON_MALE_NAMES:
            return "M"
        if last in self.COMMON_FEMALE_NAMES:
            return "F"
        return ""

    def _normalize_text(self, text: str, etype: str) -> str:
        t = text.strip()
        low = t.lower()
        if etype in {"PER", "PER_TITLE"}:
            # Remove title, keep surname/last word
            parts = low.replace(".", "").split()
            if parts and parts[0] in self.PERSON_TITLES and len(parts) >= 2:
                return parts[-1]
            return parts[-1] if parts else low
        if etype in {"LOC_ORG", "GROUP"}:
            # Remove articles (the) and common company suffixes
            for p in ("the ",):
                if low.startswith(p):
                    low = low[len(p) :]
            for suf in (" inc", " ltd", " corp", " corporation", " llc"):
                if low.endswith(suf):
                    low = low[: -len(suf)]
            return low
        if etype == "OBJ":
            for art in ("the ", "a ", "an "):
                if low.startswith(art):
                    low = low[len(art) :]
            parts = [p for p in low.replace(".", "").split() if p]
            if parts:
                return parts[-1]
        return low

    def _map_type(self, m: Mention) -> str:
        label = m.type.upper()
        text = m.text.strip().lower()

        # NP handling: check org/group first, then check for person name
        if label == "NP":
            raw = m.text.strip()
            low_raw = raw.lower()
            tokens = [t.strip(",") for t in low_raw.split() if t.strip(",")]
            for h in self.GROUP_HEADS:
                if low_raw.endswith(" " + h) or low_raw == h or low_raw.startswith(("the " + h, "a " + h, "an " + h)):
                    return "GROUP"
            for h in self.ORG_HEADS:
                if low_raw.endswith(" " + h) or low_raw == h or low_raw.startswith(("the " + h, "a " + h, "an " + h)):
                    return "LOC_ORG"
            for t in self.PERSON_TITLES:
                if low_raw == t or low_raw.startswith(("the " + t, "a " + t, "an " + t, t + " ")):
                    return "PER_TITLE"
            for t in self.PERSON_TITLES:
                if t in tokens:
                    return "PER_TITLE"
            # NP starting with article is more likely a common noun
            if low_raw.startswith(("the ", "a ", "an ")):
                return "OBJ"
            # Capitalized word -> likely person name
            if raw and any(w and w[0].isupper() for w in raw.split()):
                return "PER"

        if label == "PERSON":
            return "PER"
        if label in {"ORG", "GPE", "LOC", "FAC"}:
            if text in self.COMMON_MALE_NAMES or text in self.COMMON_FEMALE_NAMES:
                return "PER"
            for t in self.PERSON_TITLES:
                if text == t or text.startswith(t + " ") or text.startswith("the " + t):
                    return "PER_TITLE"
            for h in self.GROUP_HEADS:
                if text.endswith(" " + h) or text == h:
                    return "GROUP"
            return "LOC_ORG"
        if label in {"DATE", "TIME"}:
            return "TIME"

        # NP fallback: prefer abstract objects
        for w in self.ABSTRACT_OBJECT_WORDS:
            if w in text:
                return "OBJ"
        for t in self.PERSON_TITLES:
            if (
                text.startswith(t + " ")
                or text == t
                or text.startswith("the " + t)
                or text.startswith("a " + t)
                or text.startswith("an " + t)
            ):
                return "PER_TITLE"
        for h in self.ORG_HEADS:
            if text.endswith(" " + h) or text == h:
                if h in self.GROUP_HEADS:
                    return "GROUP"
                return "LOC_ORG"
        return "OBJ"
