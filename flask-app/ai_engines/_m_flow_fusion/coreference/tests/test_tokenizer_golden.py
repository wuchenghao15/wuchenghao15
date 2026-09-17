"""
Golden regression tests for Chinese tokenizer (entity recognition).
"""

import pytest
from coreference_module import ChineseTokenizer


@pytest.fixture(scope="module")
def tok():
    return ChineseTokenizer()


class TestPersonRecognition:
    def test_common_name(self, tok):
        r = tok.analyze("小明在学校读书")
        assert "小明" in r["person_names"]

    def test_foreign_name(self, tok):
        r = tok.analyze("大卫去机场")
        assert "大卫" in r["person_names"]

    def test_person_title(self, tok):
        """'妈妈' is reduplicated (妈=妈) so tokenizer classifies as PER_NAME, not PER_TITLE."""
        r = tok.analyze("妈妈在超市买苹果")
        assert "妈妈" in r["person_names"]  # reduplicated chars → PER_NAME

    def test_actual_title(self, tok):
        """'医生' is a true profession title → PER_TITLE."""
        r = tok.analyze("医生在医院看病人")
        assert "医生" in r["person_titles"]

    def test_surname_title(self, tok):
        tokens = tok.tokenize("张阿姨来了")
        types = [t.entity_type for t in tokens if t.word == "张阿姨"]
        assert "PER_TITLE" in types

    def test_not_person(self, tok):
        """Company names should NOT be tagged as person."""
        r = tok.analyze("华为发布新手机")
        assert "华为" not in r["person_names"]


class TestLocationRecognition:
    def test_location_name(self, tok):
        r = tok.analyze("小明去北京")
        assert "北京" in r["location_names"]

    def test_place_word(self, tok):
        r = tok.analyze("小明在学校读书")
        assert "学校" in r["location_places"]

    def test_not_location(self, tok):
        """'东西' should NOT be tagged as location."""
        r = tok.analyze("买了很多东西")
        assert "东西" not in r["location_names"]
        assert "东西" not in r["location_places"]


class TestObjectRecognition:
    def test_object(self, tok):
        r = tok.analyze("我买了一部手机")
        assert "手机" in r["objects"]

    def test_compound_split(self, tok):
        """'看电视' should be split: '看' + '电视'(OBJ)."""
        tokens = tok.tokenize("看电视")
        objs = [t for t in tokens if t.entity_type == "OBJ"]
        assert any("电视" in t.word for t in objs)


class TestTimeRecognition:
    def test_time_word(self, tok):
        r = tok.analyze("昨天天气很好")
        assert "昨天" in r["times"]


class TestPositionInfo:
    def test_token_has_position(self, tok):
        """Tokens must have start/end character positions."""
        tokens = tok.tokenize("小明去北京")
        for t in tokens:
            assert t.start >= 0
            assert t.end > t.start

    def test_mention_has_position(self, tok):
        """Mentions must have start/end character positions."""
        mentions = tok.analyze_mentions("小明去北京")
        for m in mentions:
            assert m.start >= 0
            assert m.end > m.start
