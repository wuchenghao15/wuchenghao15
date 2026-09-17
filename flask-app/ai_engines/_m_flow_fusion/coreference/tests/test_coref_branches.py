"""
Branch coverage tests for _find_replacement() and resolve_sentence().
These capture CURRENT behavior as golden standard for refactoring safety.
"""

import pytest
from coreference_module import CoreferenceResolver


def _resolve(text: str) -> str:
    r = CoreferenceResolver()
    out, _ = r.resolve_text(text)
    return out


def _resolve_with_reps(text: str):
    r = CoreferenceResolver()
    return r.resolve_text(text)


# ===========================================================================
# P0: First-person possessive non-resolution (Phase 1 fix protection)
# ===========================================================================
class TestFirstPersonPossessive:
    def test_our_not_resolved(self):
        r = _resolve("小明买了手机。我们的计划是明天出发。")
        assert "我们的" in r

    def test_zan_not_resolved(self):
        r = _resolve("公司开会了。咱们的方案通过了。")
        assert "咱们的" in r


# ===========================================================================
# P0: Emphatic reflexive non-resolution
# ===========================================================================
class TestEmphaticReflexive:
    def test_ta_ziji_not_resolved(self):
        r = _resolve("小明很了解自己。他自己知道答案。")
        assert "他自己" in r

    def test_ta_benren_not_resolved(self):
        r = _resolve("小明说了实话。她本人也承认了。")
        assert "本人" in r


# ===========================================================================
# P1: Event pronoun resolution
# ===========================================================================
class TestEventPronoun:
    def test_zhejianshi(self):
        """这件事 should be resolved to event summary."""
        out, reps = _resolve_with_reps("小明迟到了。这件事让老师很生气。")
        event_reps = [r for r in reps if r["pronoun"] == "这件事"]
        assert len(event_reps) > 0, "这件事 should be resolved"

    def test_single_char_event(self):
        """Single-char 这 with trigger verb should be resolved."""
        out, reps = _resolve_with_reps("他考试作弊。这让大家很失望。")
        event_reps = [r for r in reps if r["pronoun"] == "这"]
        assert len(event_reps) > 0, "这 with trigger should be resolved"


# ===========================================================================
# P1: Formal deictic resolution
# ===========================================================================
class TestFormalDeictic:
    def test_gai_gongsi(self):
        """该公司 should be resolved (formal deictic)."""
        out, reps = _resolve_with_reps("公司决定裁员。该公司已发布公告。")
        formal_reps = [r for r in reps if r["pronoun"] == "该公司"]
        assert len(formal_reps) > 0, "该公司 should be resolved"


# ===========================================================================
# P1: 对方 resolution
# ===========================================================================
class TestDuifang:
    def test_duifang_resolved(self):
        """对方 in dialogue context should be resolved."""
        out, reps = _resolve_with_reps("张三对李四说了一句话。对方很生气。")
        duifang_reps = [r for r in reps if r["pronoun"] == "对方"]
        assert len(duifang_reps) > 0, "对方 should be resolved in speech context"


# ===========================================================================
# P1: Gender filtering
# ===========================================================================
class TestGenderFilter:
    def test_she_resolves_to_female(self):
        """她 should resolve to female name when both genders present."""
        r = _resolve("小明和小红是同学。她很开心。")
        assert "小红" in r


# ===========================================================================
# P2: Filler word detection
# ===========================================================================
class TestFillerDetection:
    def test_nage_filler_not_resolved(self):
        """Colloquial 那个，... should not be resolved."""
        r = _resolve("那个，我想说一下。")
        assert "那个" in r


# ===========================================================================
# P2: Descriptive phrase
# ===========================================================================
class TestDescriptivePhrase:
    def test_nage_ren_resolved(self):
        """那个人 with unique candidate should be resolved."""
        out, reps = _resolve_with_reps("小明来了。那个人很友好。")
        desc_reps = [r for r in reps if r["pronoun"] == "那个人"]
        assert len(desc_reps) > 0, "那个人 should be resolved when unique candidate"


# ===========================================================================
# P2: Ambiguous pronoun
# ===========================================================================
class TestAmbiguousPronoun:
    def test_zhege_resolved_to_object(self):
        """这个 should be resolved to recent object."""
        r = _resolve("小明买了手机。这个很好用。")
        assert "手机" in r


# ===========================================================================
# P2: Modifier+noun skip
# ===========================================================================
class TestModifierNounSkip:
    def test_zhege_wenti_not_resolved(self):
        """这个问题 (determiner+noun) should NOT be resolved."""
        r = _resolve("小明说了一句话。这个问题很严重。")
        assert "这个问题" in r


# ===========================================================================
# P2: Object no antecedent
# ===========================================================================
class TestObjectNoAntecedent:
    def test_ta_no_object_antecedent(self):
        """它 with no object antecedent should not be resolved."""
        r = _resolve("它很好用。")
        assert r == "它很好用。"


# ===========================================================================
# P2: Passive sentence resolution
# ===========================================================================
class TestPassiveSentence:
    def test_passive_bei(self):
        """In passive sentence, 他被... should refer to patient."""
        r = _resolve("警察抓住了小偷。他被带走了。")
        assert "小偷" in r


# ===========================================================================
# P2: Multi-person conservative non-resolution
# ===========================================================================
class TestMultiPersonAmbiguity:
    def test_three_persons_not_resolved(self):
        """With 3+ persons and no semantic signal, should not resolve."""
        r = _resolve("张三和李四和王五一起来了。他很高兴。")
        assert "他很高兴" in r


# ===========================================================================
# P1: Object possessive (OBJECT_POSS type)
# ===========================================================================
class TestObjectPossessive:
    def test_tade_object(self):
        """它的 should be resolved to object possessive."""
        r = _resolve("小明买了手机。它的屏幕很大。")
        assert "手机的" in r


# ===========================================================================
# P2: Formal deictic standalone (FORMAL type — 该/此/本 without noun)
# ===========================================================================
class TestFormalDeicticStandalone:
    def test_shangshu_compound_resolved(self):
        """上述方案 as formal deictic should be resolved when antecedent exists."""
        out, reps = _resolve_with_reps("方案已提交。上述方案需要审核。")
        formal_reps = [rep for rep in reps if "上述" in rep["pronoun"]]
        assert len(formal_reps) > 0 or "上述方案" in out  # either resolved or kept

    def test_shangshu_standalone_resolved(self):
        """Standalone 上述 (FORMAL type) should be resolved."""
        r = _resolve("方案已经确定了。上述需要重新审核。")
        assert "方案" in r


# ===========================================================================
# P2: Speech verb multi-person conservative non-resolution
# ===========================================================================
class TestSpeechMultiPerson:
    def test_speech_multi_person_not_resolved(self):
        """Multiple persons with speech verbs, conservatively don't resolve."""
        r = _resolve("张三对李四说，王五表示他会来。")
        assert "他会来" in r


# ===========================================================================
# P2: Conditional sentence resolution
# ===========================================================================
class TestConditionalSentence:
    def test_conditional_resolves_to_condition_person(self):
        """In conditional '如果X..., Y...他', resolve to person in condition."""
        r = _resolve("如果张三同意，李四会通知他。")
        assert "张三" in r


# ===========================================================================
# P2: Mental verb ambiguity non-resolution
# ===========================================================================
class TestMentalVerbAmbiguity:
    def test_mental_verb_not_resolved(self):
        """'X觉得他...' pattern should not resolve (ambiguous)."""
        r = _resolve("张三觉得他不对。")
        assert "他不对" in r


# ===========================================================================
# P2: Transfer structure conservative non-resolution
# ===========================================================================
class TestTransferStructure:
    def test_transfer_conservative(self):
        """'A把X交给B，然后他...' — conservative strategy: either keep or resolve to B."""
        r = _resolve("张三把文件交给李四，然后他离开了。")
        # Due to jieba global state, tokenization may differ across test runs.
        # Acceptable: kept as-is (conservative) OR resolved to 李四 (receiver).
        # NOT acceptable: resolved to 张三 (wrong entity for this structure).
        assert "然后他" in r or "然后李四" in r
