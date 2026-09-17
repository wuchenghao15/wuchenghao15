#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
English tokenization and mention extraction (based on spaCy, conservative NP+NER extraction).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Mention:
    text: str
    type: str
    start: int
    end: int
    role: str = ""
    gender: str = ""


class EnglishTokenizer:
    def __init__(self, spacy_model: str = "en_core_web_sm") -> None:
        self._nlp = None
        self._model_name = spacy_model

    def _load(self) -> None:
        if self._nlp is not None:
            return
        try:
            import spacy
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("spaCy not installed. Please run: pip install spacy") from exc
        try:
            self._nlp = spacy.load(self._model_name)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                f"spaCy model '{self._model_name}' not found. Run: python -m spacy download en_core_web_sm"
            ) from exc

    def sentence_split(self, text: str) -> List[str]:
        self._load()
        doc = self._nlp(text)
        return [sent.text for sent in doc.sents]

    def parse(self, text: str):
        self._load()
        return self._nlp(text)

    def analyze_mentions(self, text: str) -> List[Mention]:
        """
        Extract mentions: prioritize NER entities, then NP.
        """
        self._load()
        doc = self._nlp(text)
        mentions: List[Mention] = []

        # 1) NER entities
        for ent in doc.ents:
            mentions.append(
                Mention(
                    text=ent.text,
                    type=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    role="",
                    gender="",
                )
            )

        # 2) NP chunks (exclude NER overlaps, but can backfill roles)
        def _overlap(a_start: int, a_end: int) -> bool:
            for m in mentions:
                if not (a_end <= m.start or a_start >= m.end):
                    return True
            return False

        def _fill_role(a_start: int, a_end: int, role: str, gender: str) -> None:
            if not role:
                role = ""
            for m in mentions:
                if not (a_end <= m.start or a_start >= m.end):
                    if role:
                        m.role = role
                    if gender:
                        m.gender = gender

        for np in doc.noun_chunks:
            # Filter out NPs consisting only of pronouns/determiners
            pos_tags = {t.pos_ for t in np}
            if pos_tags.issubset({"PRON", "DET"}):
                continue
            role = ""
            if np.root.dep_ in {"nsubj", "nsubjpass"}:
                role = "SUBJ"
            elif np.root.dep_ in {"dobj", "obj", "pobj"}:
                role = "OBJ"
            elif np.root.dep_ == "conj":
                head = np.root.head
                while head.dep_ == "conj" and head.head is not None:
                    head = head.head
                head_dep = head.dep_
                if head_dep in {"nsubj", "nsubjpass"}:
                    role = "SUBJ"
                elif head_dep in {"dobj", "obj", "pobj"}:
                    role = "OBJ"
            gender = ""
            low_np = np.text.lower()
            if low_np.startswith("mr ") or low_np.startswith("mr."):
                gender = "M"
            elif (
                low_np.startswith("ms ")
                or low_np.startswith("ms.")
                or low_np.startswith("mrs ")
                or low_np.startswith("mrs.")
                or low_np.startswith("miss ")
            ):
                gender = "F"
            if _overlap(np.start_char, np.end_char):
                _fill_role(np.start_char, np.end_char, role, gender)
                continue
            mentions.append(
                Mention(
                    text=np.text,
                    type="NP",
                    start=np.start_char,
                    end=np.end_char,
                    role=role,
                    gender=gender,
                )
            )

        # sort by position
        mentions.sort(key=lambda m: (m.start, m.end))
        return mentions

    def pos_at(self, text: str, char_index: int) -> Optional[str]:
        """
        Return POS tag (coarse) for a given character position, used for auxiliary rules.
        """
        self._load()
        doc = self._nlp(text)
        for tok in doc:
            if tok.idx <= char_index < tok.idx + len(tok):
                return tok.pos_
        return None

    def extract_event_summary(self, text: str, report_verbs: set[str]) -> Optional[str]:
        """
        Extract coarse-grained event summary: prioritize object/complement noun phrases of report verbs.
        """
        self._load()
        doc = self._nlp(text)
        verb_idx = None
        verb_token = None
        for tok in doc:
            if tok.lemma_.lower() in report_verbs or tok.text.lower() in report_verbs:
                verb_idx = tok.idx
                verb_token = tok
                break
        if verb_token is None or verb_idx is None:
            return None

        # 1) Dependency relation priority: dobj/obj/attr/pobj
        targets = []
        for child in verb_token.children:
            if child.dep_ in {"dobj", "obj", "attr", "pobj"}:
                targets.append(child)
        if targets:
            # Find the NP containing this token
            for np in doc.noun_chunks:
                for t in targets:
                    if np.start <= t.i < np.end:
                        return np.text
            return targets[0].text

        # 2) fallback: first NP after the verb
        for np in doc.noun_chunks:
            if np.start_char > verb_idx:
                return np.text
        return None

    def extract_root_verb(self, text: str) -> Optional[str]:
        self._load()
        doc = self._nlp(text)
        root = None
        for tok in doc:
            if tok.dep_ == "ROOT":
                root = tok
                break
        if root is None:
            return None
        if root.pos_ == "VERB":
            return root.lemma_.lower()
        return None
