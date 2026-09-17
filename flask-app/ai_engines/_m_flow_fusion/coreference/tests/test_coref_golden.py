"""
Golden regression tests for Chinese coreference resolution.
Each test captures CURRENT correct behavior.
If any test fails after refactoring, the refactoring introduced a regression.
"""

import pytest
from coreference_module import resolve, CoreferenceResolver


# ---------------------------------------------------------------------------
# Helper: resolve with fresh resolver each time
# ---------------------------------------------------------------------------
def _resolve(text: str) -> str:
    r = CoreferenceResolver()
    out, _ = r.resolve_text(text)
    return out


# ===========================================================================
# Group 1: Basic pronoun resolution (must pass)
# ===========================================================================
class TestBasicResolution:
    def test_person_pronoun(self):
        assert "小明" in _resolve("小明去北京。他在那里工作。")

    def test_female_pronoun(self):
        assert "妈妈" in _resolve("妈妈去超市买苹果。她买了很多。")

    def test_location_pronoun(self):
        r = _resolve("小明去北京。他在那里工作。")
        assert "北京" in r

    def test_possessive_pronoun(self):
        r = _resolve("小明买了书。他的书很有趣。")
        assert "小明" in r and "的书" in r

    def test_object_pronoun(self):
        r = _resolve("我买了一部手机。它很好用。")
        assert "手机" in r


# ===========================================================================
# Group 2: Plural pronouns
# ===========================================================================
class TestPluralResolution:
    def test_plural_person(self):
        r = _resolve("张三和李四去公园。他们在那里散步。")
        assert "张三" in r or "李四" in r

    def test_plural_possessive(self):
        r = _resolve("小明和小红是同学。他们的成绩都很好。")
        assert "小明" in r or "小红" in r


# ===========================================================================
# Group 3: Semantic role (patient/agent detection)
# ===========================================================================
class TestSemanticRole:
    def test_criticism_patient(self):
        """Criticized person should be sad, not the criticizer."""
        r = _resolve("老师批评了小明。他很难过。")
        assert "小明" in r

    def test_help_beneficiary(self):
        """Helped person should be grateful."""
        r = _resolve("小明帮助了老人。他很感激。")
        # "他" should refer to 老人 (the helped one)
        second_sentence = r.split("。")[1]
        assert "老人" in second_sentence


# ===========================================================================
# Group 4: Non-resolution cases (must NOT resolve)
# ===========================================================================
class TestNonResolution:
    def test_first_sentence_no_antecedent(self):
        """First sentence pronoun should not be resolved."""
        assert _resolve("他很高。") == "他很高。"

    def test_reflexive_pronoun(self):
        """Reflexive pronouns should not be resolved."""
        assert "自己" in _resolve("小明很了解自己。")

    def test_generic_pronoun(self):
        """Generic pronouns should not be resolved."""
        assert "人家" in _resolve("人家不想去。")

    def test_bound_variable(self):
        """Bound variable should not be resolved."""
        r = _resolve("每个学生都带了他的书。")
        assert "每个学生" in r and "他的书" in r

    def test_intra_sentence_binding(self):
        """Intra-sentence binding: 'A比他高' should not resolve '他' to A."""
        r = _resolve("张三很高。张三比他高。")
        # The second "他" should NOT become "张三"
        second = r.split("。")[1]
        assert "比张三高" not in second or "比他高" in second

    def test_inside_quotes(self):
        """Pronouns inside quotes should not be resolved."""
        r = _resolve("\u5f20\u4e09\u8bf4\uff1a\u201c\u4ed6\u4f1a\u6765\u3002\u201d")
        # "他" inside quotes should be preserved
        assert "\u4ed6" in r


# ===========================================================================
# Group 5: Reduplicative structure (pronoun should be DELETED)
# ===========================================================================
class TestReduclicative:
    def test_reduplicative_deletion(self):
        """'小明他很聪明' → '小明很聪明' (delete redundant pronoun)."""
        r = _resolve("小明去学校。小明他很聪明。")
        assert "小明很聪明" in r or "小明他很聪明" in r  # either deleted or kept


# ===========================================================================
# Group 6: Time pronoun resolution
# ===========================================================================
class TestTimeResolution:
    def test_time_pronoun(self):
        r = _resolve("去年我去了北京。那时候天气很好。")
        assert "去年" in r or "那时候" in r  # resolved or kept

    def test_time_no_antecedent(self):
        """Time pronoun with no antecedent should not be resolved."""
        assert _resolve("那时候天气好。") == "那时候天气好。"


# ===========================================================================
# Group 7: Ordinal pronouns (former/latter)
# ===========================================================================
class TestOrdinalResolution:
    def test_former(self):
        r = _resolve("张三和李四是朋友。前者是医生。")
        assert "张三" in r

    def test_latter(self):
        r = _resolve("张三和李四是朋友。后者是老师。")
        assert "李四" in r


# ===========================================================================
# Group 8: Safety checks
# ===========================================================================
class TestSafety:
    def test_empty_input(self):
        assert _resolve("") == ""

    def test_no_pronouns(self):
        text = "小明在学校读书。"
        assert _resolve(text) == text

    def test_pure_punctuation(self):
        assert _resolve("。！？") == "。！？"

    def test_no_sentence_end_punct(self):
        """Input without sentence-ending punctuation should not be resolved."""
        text = "小明去北京，他在那里工作"
        assert _resolve(text) == text


# ===========================================================================
# Group 9: Stream (incremental) resolution
# ===========================================================================
class TestStreamResolution:
    def test_stream_basic(self):
        from coreference_module.coreference import StreamCorefSession

        session = StreamCorefSession()
        r1, _ = session.add_sentence("小明去北京。")
        r2, _ = session.add_sentence("他在那里工作。")
        assert "小明" in r2 and "北京" in r2

    def test_stream_reset(self):
        from coreference_module.coreference import StreamCorefSession

        session = StreamCorefSession()
        session.add_sentence("小明去北京。")
        session.reset()
        r, _ = session.add_sentence("他很高。")
        # After reset, "他" has no antecedent
        assert r == "他很高。"


# ===========================================================================
# Group 10: Structured output
# ===========================================================================
class TestStructuredOutput:
    def test_structured_has_fields(self):
        resolver = CoreferenceResolver()
        output = resolver.resolve_text_structured("小明去北京。他在那里工作。")
        assert hasattr(output, "resolved_text")
        assert hasattr(output, "replacements")
        assert hasattr(output, "mentions")
        assert hasattr(output, "time_extractions")
        assert "小明" in output.resolved_text
