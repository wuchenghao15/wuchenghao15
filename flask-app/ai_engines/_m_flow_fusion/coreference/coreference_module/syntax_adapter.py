#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lightweight syntax / role adapter layer: prefers available parsers, falls back to heuristic rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)
import importlib.util


@dataclass
class RoleHint:
    start: int
    end: int
    role: str  # "subject" | "object"


@dataclass
class SRLArg:
    start: int
    end: int
    role: str  # "subject" | "object"
    pred_start: Optional[int] = None
    pred_end: Optional[int] = None


class SyntaxAdapter:
    def __init__(self, tokenizer, prefer_backend: str = "ltp", max_tokens: int = 40) -> None:
        self.tokenizer = tokenizer
        self.backend = None
        self.prefer_backend = prefer_backend
        self.max_tokens = max_tokens
        self._hanlp_dep = None
        self._ltp = None
        self._cache_sentence: Optional[str] = None
        self._cache_tokens: Optional[List[str]] = None
        self._cache_offsets: Optional[List[tuple[int, int]]] = None
        self._cache_roles: Optional[List[Optional[str]]] = None
        self._cache_heads: Optional[List[int]] = None
        self._cache_rels: Optional[List[str]] = None
        self._cache_srl_hints: Optional[List[RoleHint]] = None
        self._cache_srl_subject: Optional[List[str]] = None
        self._cache_srl_object: Optional[List[str]] = None
        self._cache_srl_args: Optional[List[SRLArg]] = None
        self._hanlp_srl = None
        self._try_load_backend()

    def _try_load_backend(self) -> None:
        order = ("ltp", "hanlp") if self.prefer_backend == "ltp" else ("hanlp", "ltp")
        for name in order:
            if importlib.util.find_spec(name) is not None:
                self.backend = name
                break

    def get_pronoun_role(self, sentence: str, position: int) -> Optional[str]:
        srl_hint = self.get_srl_role_hint(sentence, position)
        if srl_hint:
            return srl_hint
        if self._cache_sentence == sentence and self._cache_offsets and self._cache_roles:
            idx = self._find_token_index(position, self._cache_offsets)
            if idx is not None and idx < len(self._cache_roles):
                return self._cache_roles[idx]
        if self.backend == "hanlp":
            role = self._hanlp_role(sentence, position)
            if role:
                return role
        if self.backend == "ltp":
            role = self._ltp_role(sentence, position)
            if role:
                return role
        # Currently only lightweight heuristics; can be enhanced when backend is available
        return self._heuristic_pronoun_role(sentence, position)

    def get_role_tokens(self, sentence: str) -> dict:
        tokens, roles, _offsets = self._ensure_parsed(sentence)
        if not tokens or not roles:
            return {"subject": [], "object": []}
        sub = [t for t, r in zip(tokens, roles) if r == "subject"]
        obj = [t for t, r in zip(tokens, roles) if r == "object"]
        return {"subject": sub, "object": obj}

    def get_srl_role_hint(self, sentence: str, position: int) -> Optional[str]:
        hints, _sub, _obj = self._ensure_srl(sentence)
        if not hints:
            return None
        for hint in hints:
            if hint.start <= position < hint.end:
                return hint.role
        return None

    def get_srl_role_tokens(self, sentence: str) -> dict:
        _hints, sub, obj = self._ensure_srl(sentence)
        if not sub and not obj:
            return {"subject": [], "object": []}
        return {"subject": sub or [], "object": obj or []}

    def get_srl_args(self, sentence: str) -> List[SRLArg]:
        _hints, _sub, _obj = self._ensure_srl(sentence)
        if self._cache_srl_args is None:
            return []
        return self._cache_srl_args

    def get_event_summary(self, sentence: str) -> Optional[str]:
        if self.backend == "ltp":
            return self._ltp_event_summary(sentence)
        if self.backend == "hanlp":
            return self._hanlp_event_summary(sentence)
        return None

    def get_conj_group_before(self, sentence: str, position: int) -> Optional[str]:
        tokens, offsets, heads, rels = self._ensure_dep(sentence)
        if not tokens or not offsets or not heads or not rels:
            return None
        conj_rels = {"COO", "conj"}
        n = len(tokens)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for i, rel in enumerate(rels):
            if rel in conj_rels:
                h = heads[i] - 1
                if 0 <= h < n:
                    union(i, h)

        groups: dict[int, List[int]] = {}
        for i in range(n):
            if offsets[i][1] > position:
                continue
            r = find(i)
            groups.setdefault(r, []).append(i)

        candidates = [g for g in groups.values() if len(g) >= 2]
        if not candidates:
            return None
        group = max(candidates, key=lambda g: max(offsets[i][1] for i in g))
        group = sorted(group, key=lambda i: offsets[i][0])

        # Filter out conjunctions and punctuation to avoid errors like duplicate conjunctions
        conjunctions = {"和", "与", "及", "或", "跟", "同", "、", "，", ","}
        names = [tokens[i] for i in group if tokens[i] not in conjunctions]

        # Deduplicate
        unique_names = []
        for n in names:
            if n not in unique_names:
                unique_names.append(n)
        names = unique_names

        if len(names) < 2:
            return None
        if all(n in {"公司", "机构", "部门", "团队"} for n in names):
            return None
        if len(names) == 2:
            return names[0] + "和" + names[1]
        return "、".join(names[:-1]) + "和" + names[-1]

    def get_clause_bounds(self, sentence: str) -> List[tuple[int, int]]:
        tokens, offsets, heads, rels = self._ensure_dep(sentence)
        if not tokens or not offsets or not heads or not rels:
            return []
        clause_rels = {"ADV", "CMP", "COO", "SBV", "VOB", "FOB", "POB", "COO", "DBL", "IC", "HED", "RAD", "WP", "MT"}
        clause_dep_rels = {"advcl", "acl", "rcmod", "conj", "ccomp", "xcomp"}
        boundaries = set()
        for i, rel in enumerate(rels):
            if rel in clause_dep_rels:
                boundaries.add(offsets[i][0])
        for i, tok in enumerate(tokens):
            if tok in {"，", ",", "；", ";", "。"}:
                boundaries.add(offsets[i][1])
        points = sorted(b for b in boundaries if 0 < b < len(sentence))
        if not points:
            return [(0, len(sentence))]
        bounds = []
        start = 0
        for b in points:
            bounds.append((start, b))
            start = b
        bounds.append((start, len(sentence)))
        return bounds

    def get_clause_index(self, sentence: str, position: int) -> Optional[int]:
        bounds = self.get_clause_bounds(sentence)
        if not bounds:
            return None
        for i, (s, e) in enumerate(bounds):
            if s <= position < e:
                return i
        return None

    def _heuristic_pronoun_role(self, sentence: str, position: int) -> Optional[str]:
        before = sentence[:position]
        after = sentence[position:]
        # Passive voice: X bei Y..., X is typically the patient
        if "被" in before[-4:]:
            return "object"
        # Ba-construction: X ba Y...
        if "把" in before[-4:]:
            return "object"
        # Prepositional structure: after dui/xiang/gei/gen/he, typically patient or object
        if any(p in before[-3:] for p in ("对", "向", "给", "跟", "和")):
            return "object"
        # If followed immediately by a verb, likely subject
        tokens = self.tokenizer.tokenize(after[:4])
        for t in tokens:
            if t.pos in {"v", "vd", "vn"}:
                return "subject"
            break
        return None

    def _ensure_hanlp(self) -> None:
        if self._hanlp_dep is not None:
            return
        import hanlp

        self._hanlp_dep = hanlp.load(hanlp.pretrained.dep.CTB9_DEP_ELECTRA_SMALL)

    def _ensure_hanlp_srl(self) -> None:
        if self._hanlp_srl is not None:
            return
        import hanlp

        self._hanlp_srl = hanlp.load(hanlp.pretrained.srl.CPB3_SRL_ELECTRA_SMALL)

    def _ensure_ltp(self) -> None:
        if self._ltp is not None:
            return
        from ltp import LTP

        self._ltp = LTP()

    def _get_offsets(self, tokens: List[str], sentence: str) -> List[tuple[int, int]]:
        offsets: List[tuple[int, int]] = []
        cursor = 0
        for tok in tokens:
            idx = sentence.find(tok, cursor)
            if idx < 0:
                idx = cursor
            start = idx
            end = idx + len(tok)
            offsets.append((start, end))
            cursor = end
        return offsets

    def _find_token_index(self, position: int, offsets: List[tuple[int, int]]) -> Optional[int]:
        for i, (s, e) in enumerate(offsets):
            if s <= position < e:
                return i
        return None

    def _ensure_parsed(
        self, sentence: str
    ) -> tuple[Optional[List[str]], Optional[List[Optional[str]]], Optional[List[tuple[int, int]]]]:
        if self._cache_sentence == sentence and self._cache_tokens and self._cache_offsets and self._cache_roles:
            return self._cache_tokens, self._cache_roles, self._cache_offsets
        if self.backend == "hanlp":
            _ = self._hanlp_role(sentence, 0)
        elif self.backend == "ltp":
            _ = self._ltp_role(sentence, 0)
        if self._cache_sentence == sentence and self._cache_tokens and self._cache_offsets and self._cache_roles:
            return self._cache_tokens, self._cache_roles, self._cache_offsets
        return None, None, None

    def _ensure_dep(
        self, sentence: str
    ) -> tuple[Optional[List[str]], Optional[List[tuple[int, int]]], Optional[List[int]], Optional[List[str]]]:
        if (
            self._cache_sentence == sentence
            and self._cache_tokens
            and self._cache_offsets
            and self._cache_heads
            and self._cache_rels
        ):
            return self._cache_tokens, self._cache_offsets, self._cache_heads, self._cache_rels
        if self.backend == "hanlp":
            _ = self._hanlp_role(sentence, 0)
        elif self.backend == "ltp":
            _ = self._ltp_role(sentence, 0)
        if (
            self._cache_sentence == sentence
            and self._cache_tokens
            and self._cache_offsets
            and self._cache_heads
            and self._cache_rels
        ):
            return self._cache_tokens, self._cache_offsets, self._cache_heads, self._cache_rels
        return None, None, None, None

    def _ensure_srl(self, sentence: str) -> tuple[Optional[List[RoleHint]], Optional[List[str]], Optional[List[str]]]:
        if self._cache_sentence == sentence and self._cache_srl_hints is not None:
            return self._cache_srl_hints, self._cache_srl_subject, self._cache_srl_object
        if self.backend == "ltp":
            _ = self._ltp_srl(sentence)
        elif self.backend == "hanlp":
            _ = self._hanlp_srl_parse(sentence)
        if self._cache_sentence == sentence and self._cache_srl_hints is not None:
            return self._cache_srl_hints, self._cache_srl_subject, self._cache_srl_object
        return None, None, None

    def _hanlp_role(self, sentence: str, position: int) -> Optional[str]:
        try:
            self._ensure_hanlp()
            dep = self._hanlp_dep(sentence)
        except Exception as e:
            logger.debug("hanlp dep parse failed: %s", e)
            return None
        tokens: List[str] = []
        heads: List[int] = []
        rels: List[str] = []
        for tok in dep:
            form = getattr(tok, "form", None)
            if form is None:
                try:
                    form = tok[1]
                except (IndexError, KeyError, TypeError, ValueError):
                    form = str(tok)
            tokens.append(form)
            try:
                heads.append(int(tok[6]))
                rels.append(str(tok[7]))
            except (IndexError, KeyError, TypeError, ValueError):
                heads.append(0)
                rels.append("")
        if len(tokens) > self.max_tokens:
            return None
        offsets = self._get_offsets(tokens, sentence)
        roles = []
        for rel in rels:
            if rel in {"nsubj", "csubj", "top"}:
                roles.append("subject")
            elif rel in {"dobj", "iobj", "obj", "pobj", "nsubj:pass", "obl"}:
                roles.append("object")
            else:
                roles.append(None)
        self._cache_sentence = sentence
        self._cache_tokens = tokens
        self._cache_offsets = offsets
        self._cache_roles = roles
        self._cache_heads = heads
        self._cache_rels = rels
        idx = self._find_token_index(position, offsets)
        if idx is None or idx >= len(roles):
            return None
        return roles[idx]

    def _ltp_srl(self, sentence: str) -> Optional[List[RoleHint]]:
        try:
            self._ensure_ltp()
            out = self._ltp.pipeline([sentence], tasks=["cws", "srl"])
        except Exception as e:
            logger.debug("ltp srl pipeline failed: %s", e)
            return None
        tokens = out.cws[0] if hasattr(out, "cws") else []
        srl = out.srl[0] if hasattr(out, "srl") and out.srl else []
        if len(tokens) > self.max_tokens:
            return None
        offsets = self._get_offsets(tokens, sentence)
        hints: List[RoleHint] = []
        sub_tokens: List[str] = []
        obj_tokens: List[str] = []
        args_out: List[SRLArg] = []
        for frame in srl:
            pred_idx = None
            args = None
            if isinstance(frame, dict):
                args = frame.get("arguments") or frame.get("args")
                pred_idx = frame.get("predicate") or frame.get("pred")
            elif isinstance(frame, (list, tuple)) and len(frame) >= 2:
                pred_idx = frame[0]
                args = frame[1]
            if not args:
                continue
            pred_start = None
            pred_end = None
            if isinstance(pred_idx, int) and 0 <= pred_idx < len(offsets):
                pred_start = offsets[pred_idx][0]
                pred_end = offsets[pred_idx][1]
            for arg in args:
                text = None
                role = None
                start = None
                end = None
                if isinstance(arg, dict):
                    role = arg.get("type") or arg.get("role") or arg.get("label")
                    start = arg.get("start")
                    end = arg.get("end")
                    text = arg.get("text") if isinstance(arg.get("text"), str) else None
                elif isinstance(arg, (list, tuple)) and len(arg) >= 3:
                    role = arg[0]
                    start = arg[1]
                    end = arg[2]
                    text = arg[3] if len(arg) >= 4 and isinstance(arg[3], str) else None
                if role is None or start is None or end is None:
                    if role is not None and text:
                        mapped = (
                            "subject"
                            if str(role) in {"A0", "ARG0"}
                            else "object"
                            if str(role) in {"A1", "A2", "ARG1", "ARG2"}
                            else None
                        )
                        if mapped == "subject" and text not in sub_tokens:
                            sub_tokens.append(text)
                        if mapped == "object" and text not in obj_tokens:
                            obj_tokens.append(text)
                    continue
                role = str(role)
                if role in {"A0", "ARG0"}:
                    mapped = "subject"
                elif role in {"A1", "A2", "ARG1", "ARG2"}:
                    mapped = "object"
                else:
                    continue
                if isinstance(start, str) or isinstance(end, str):
                    text = text or (start if isinstance(start, str) else end if isinstance(end, str) else None)
                    if text:
                        if mapped == "subject" and text not in sub_tokens:
                            sub_tokens.append(text)
                        if mapped == "object" and text not in obj_tokens:
                            obj_tokens.append(text)
                    continue
                s = int(start)
                e = int(end)
                if s < 0 or e < 0 or s >= len(tokens):
                    continue
                if e < s:
                    e = s
                if e >= len(tokens):
                    e = len(tokens) - 1
                text = "".join(tokens[s : e + 1])
                if mapped == "subject" and text not in sub_tokens:
                    sub_tokens.append(text)
                if mapped == "object" and text not in obj_tokens:
                    obj_tokens.append(text)
                h_start = offsets[s][0]
                h_end = offsets[e][1]
                hints.append(RoleHint(h_start, h_end, mapped))
                args_out.append(SRLArg(h_start, h_end, mapped, pred_start, pred_end))
        self._cache_sentence = sentence
        self._cache_tokens = tokens
        self._cache_offsets = offsets
        self._cache_srl_hints = hints
        self._cache_srl_subject = sub_tokens
        self._cache_srl_object = obj_tokens
        self._cache_srl_args = args_out
        return hints

    def _hanlp_srl_parse(self, sentence: str) -> Optional[List[RoleHint]]:
        try:
            self._ensure_hanlp_srl()
            srl = self._hanlp_srl(sentence)
        except Exception as e:
            logger.debug("hanlp srl failed: %s", e)
            return None
        tokens = self.tokenizer.tokenize(sentence)
        token_texts = [t.text for t in tokens]
        if len(token_texts) > self.max_tokens:
            return None
        offsets = self._get_offsets(token_texts, sentence)
        hints: List[RoleHint] = []
        sub_tokens: List[str] = []
        obj_tokens: List[str] = []
        args_out: List[SRLArg] = []
        frames = srl or []
        for frame in frames:
            pred_start = None
            pred_end = None
            if isinstance(frame, dict):
                pred = frame.get("predicate") or frame.get("pred")
                if isinstance(pred, dict):
                    ps = pred.get("start")
                    pe = pred.get("end")
                    if isinstance(ps, int) and isinstance(pe, int) and 0 <= ps < len(offsets):
                        if pe >= len(offsets):
                            pe = len(offsets) - 1
                        pred_start = offsets[ps][0]
                        pred_end = offsets[pe][1]
            args = None
            if isinstance(frame, dict):
                args = frame.get("arguments") or frame.get("args")
            elif isinstance(frame, (list, tuple)) and len(frame) >= 2:
                args = frame[1]
            if not args:
                continue
            for arg in args:
                text = None
                role = None
                start = None
                end = None
                if isinstance(arg, dict):
                    role = arg.get("role") or arg.get("label")
                    start = arg.get("start")
                    end = arg.get("end")
                    text = arg.get("text") if isinstance(arg.get("text"), str) else None
                elif isinstance(arg, (list, tuple)) and len(arg) >= 3:
                    role = arg[0]
                    start = arg[1]
                    end = arg[2]
                    text = arg[3] if len(arg) >= 4 and isinstance(arg[3], str) else None
                if role is None or start is None or end is None:
                    if role is not None and text:
                        mapped = (
                            "subject"
                            if str(role) in {"A0", "ARG0"}
                            else "object"
                            if str(role) in {"A1", "A2", "ARG1", "ARG2"}
                            else None
                        )
                        if mapped == "subject" and text not in sub_tokens:
                            sub_tokens.append(text)
                        if mapped == "object" and text not in obj_tokens:
                            obj_tokens.append(text)
                    continue
                role = str(role)
                if role in {"A0", "ARG0"}:
                    mapped = "subject"
                elif role in {"A1", "A2", "ARG1", "ARG2"}:
                    mapped = "object"
                else:
                    continue
                if isinstance(start, str) or isinstance(end, str):
                    text = text or (start if isinstance(start, str) else end if isinstance(end, str) else None)
                    if text:
                        if mapped == "subject" and text not in sub_tokens:
                            sub_tokens.append(text)
                        if mapped == "object" and text not in obj_tokens:
                            obj_tokens.append(text)
                    continue
                s = int(start)
                e = int(end)
                if s < 0 or e < 0 or s >= len(token_texts):
                    continue
                if e < s:
                    e = s
                if e >= len(token_texts):
                    e = len(token_texts) - 1
                text = "".join(token_texts[s : e + 1])
                if mapped == "subject" and text not in sub_tokens:
                    sub_tokens.append(text)
                if mapped == "object" and text not in obj_tokens:
                    obj_tokens.append(text)
                h_start = offsets[s][0]
                h_end = offsets[e][1]
                hints.append(RoleHint(h_start, h_end, mapped))
                args_out.append(SRLArg(h_start, h_end, mapped, pred_start, pred_end))
        self._cache_sentence = sentence
        self._cache_tokens = token_texts
        self._cache_offsets = offsets
        self._cache_srl_hints = hints
        self._cache_srl_subject = sub_tokens
        self._cache_srl_object = obj_tokens
        self._cache_srl_args = args_out
        return hints

    def _ltp_role(self, sentence: str, position: int) -> Optional[str]:
        try:
            self._ensure_ltp()
            out = self._ltp.pipeline([sentence], tasks=["cws", "pos", "dep"])
        except Exception as e:
            logger.debug("ltp dep pipeline failed: %s", e)
            return None
        tokens = out.cws[0]
        dep = out.dep[0]
        heads = dep.get("head", [])
        rels = dep.get("label", [])
        if len(tokens) > self.max_tokens:
            return None
        offsets = self._get_offsets(tokens, sentence)
        roles = []
        for rel in rels:
            if rel in {"SBV"}:
                roles.append("subject")
            elif rel in {"VOB", "IOB", "POB"}:
                roles.append("object")
            else:
                roles.append(None)
        self._cache_sentence = sentence
        self._cache_tokens = tokens
        self._cache_offsets = offsets
        self._cache_roles = roles
        self._cache_heads = heads
        self._cache_rels = rels
        idx = self._find_token_index(position, offsets)
        if idx is None or idx >= len(roles):
            return None
        return roles[idx]

    def _ltp_event_summary(self, sentence: str) -> Optional[str]:
        try:
            self._ensure_ltp()
            out = self._ltp.pipeline([sentence], tasks=["cws", "pos", "dep"])
        except Exception as e:
            logger.debug("ltp event summary pipeline failed: %s", e)
            return None
        tokens = out.cws[0]
        dep = out.dep[0]
        heads = dep.get("head", [])
        rels = dep.get("label", [])
        if not tokens or not heads:
            return None
        root_idx = None
        for i, h in enumerate(heads):
            if h == 0:
                root_idx = i
                break
        if root_idx is None:
            return None
        objs = [tokens[i] for i, r in enumerate(rels) if r in {"VOB", "POB"}]
        if objs:
            return tokens[root_idx] + objs[0]
        return tokens[root_idx]

    def _hanlp_event_summary(self, sentence: str) -> Optional[str]:
        try:
            self._ensure_hanlp()
            dep = self._hanlp_dep(sentence)
        except Exception as e:
            logger.debug("hanlp dep parse failed: %s", e)
            return None
        tokens: List[str] = []
        heads: List[int] = []
        rels: List[str] = []
        for tok in dep:
            form = getattr(tok, "form", None)
            if form is None:
                try:
                    form = tok[1]
                except (IndexError, KeyError, TypeError, ValueError):
                    form = str(tok)
            tokens.append(form)
            try:
                heads.append(int(tok[6]))
                rels.append(str(tok[7]))
            except (IndexError, KeyError, TypeError, ValueError):
                heads.append(0)
                rels.append("")
        root_idx = None
        for i, r in enumerate(rels):
            if r == "root" or heads[i] == 0:
                root_idx = i
                break
        if root_idx is None:
            return None
        objs = [tokens[i] for i, r in enumerate(rels) if r in {"dobj", "pobj"}]
        if objs:
            return tokens[root_idx] + objs[0]
        return tokens[root_idx]
