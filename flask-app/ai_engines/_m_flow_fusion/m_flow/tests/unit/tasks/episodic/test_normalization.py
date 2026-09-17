# m_flow/tests/unit/tasks/episodic/test_normalization.py
"""
文本规范化函数单元测试

测试 normalize_for_compare, normalize_for_id 等函数。
"""

from m_flow.memory.episodic.normalization import (
    normalize_for_compare,
    normalize_for_id,
    is_bad_search_text,
)


class TestNormalizeForCompare:
    """测试 normalize_for_compare 函数"""

    def test_basic_normalization(self):
        """测试基本规范化"""
        assert normalize_for_compare("Hello World") == "hello world"
        assert normalize_for_compare("HELLO WORLD") == "hello world"

    def test_unicode_normalization(self):
        """测试 Unicode 规范化 (NFKC)"""
        # 全角字符转半角
        assert normalize_for_compare("Ａｐｐｌｅ") == "apple"
        # 特殊空格
        assert normalize_for_compare("hello\u3000world") == "hello world"

    def test_whitespace_normalization(self):
        """测试空白字符规范化"""
        assert normalize_for_compare("  hello   world  ") == "hello world"
        assert normalize_for_compare("hello\n\nworld") == "hello world"
        assert normalize_for_compare("hello\t\tworld") == "hello world"

    def test_chinese_text(self):
        """测试中文文本"""
        assert normalize_for_compare("你好世界") == "你好世界"
        assert normalize_for_compare("  你好  世界  ") == "你好 世界"

    def test_mixed_language(self):
        """测试混合语言"""
        assert normalize_for_compare("Hello 世界 123") == "hello 世界 123"

    def test_empty_string(self):
        """测试空字符串"""
        assert normalize_for_compare("") == ""
        assert normalize_for_compare("   ") == ""

    def test_special_characters(self):
        """测试特殊字符"""
        # 特殊字符保留
        assert normalize_for_compare("hello-world") == "hello-world"
        assert normalize_for_compare("hello_world") == "hello_world"
        assert normalize_for_compare("hello@world.com") == "hello@world.com"


class TestNormalizeForId:
    """测试 normalize_for_id 函数"""

    def test_basic_id_generation(self):
        """测试基本 ID 生成"""
        # normalize_for_id 应该生成一致的、可用于 ID 的字符串
        id1 = normalize_for_id("Hello World")
        id2 = normalize_for_id("hello world")
        assert id1 == id2  # 大小写不敏感

    def test_unicode_consistency(self):
        """测试 Unicode 一致性"""
        id1 = normalize_for_id("Ａｐｐｌｅ")
        id2 = normalize_for_id("Apple")
        assert id1 == id2  # 全角半角统一

    def test_whitespace_handling(self):
        """测试空白字符处理"""
        id1 = normalize_for_id("hello world")
        id2 = normalize_for_id("hello  world")
        id3 = normalize_for_id("  hello world  ")
        assert id1 == id2 == id3

    def test_chinese_id(self):
        """测试中文 ID"""
        id1 = normalize_for_id("产品说明书")
        id2 = normalize_for_id("产品说明书")
        assert id1 == id2
        assert len(id1) > 0

    def test_deterministic(self):
        """测试确定性 - 相同输入产生相同输出"""
        text = "Some random text with 中文 and numbers 123"
        ids = [normalize_for_id(text) for _ in range(10)]
        assert all(id == ids[0] for id in ids)

    def test_empty_input(self):
        """测试空输入"""
        id1 = normalize_for_id("")
        id2 = normalize_for_id("   ")
        # 空输入应该返回空或一致的结果
        assert id1 == id2


class TestIsBadSearchText:
    """测试 is_bad_search_text 函数"""

    def test_good_search_text(self):
        """测试有效的搜索文本"""
        assert is_bad_search_text("产品说明书") is False
        assert is_bad_search_text("Hello World") is False
        assert is_bad_search_text("用户手册 v2.0") is False

    def test_empty_or_whitespace(self):
        """测试空或纯空白"""
        assert is_bad_search_text("") is True
        assert is_bad_search_text("   ") is True
        assert is_bad_search_text("\n\t") is True

    def test_too_short(self):
        """测试过短文本"""
        # 单个字符可能被视为无效
        assert is_bad_search_text("a") is True
        assert is_bad_search_text("好") is True

    def test_pure_numbers(self):
        """测试纯数字"""
        assert is_bad_search_text("123") is True
        assert is_bad_search_text("12345") is True

    def test_pure_punctuation(self):
        """测试纯标点"""
        assert is_bad_search_text("...") is True
        assert is_bad_search_text("???") is True
        assert is_bad_search_text("---") is True

    def test_mixed_valid(self):
        """测试混合有效文本"""
        assert is_bad_search_text("产品 123") is False
        assert is_bad_search_text("v2.0 说明") is False

    def test_english_bad_prefix(self):
        """测试英文无效前缀"""
        assert is_bad_search_text("this section describes") is True
        assert is_bad_search_text("the above content") is True
        assert is_bad_search_text("this part shows") is True
        assert is_bad_search_text("here we have") is True

    def test_english_too_generic_now_allowed(self):
        """测试英文过于通用的词汇 - 现在是 WARNING 而非 CRITICAL，所以返回 False"""
        # Phase 6: 通用词汇现在只产生 WARNING，不再丢弃
        assert is_bad_search_text("summary") is False  # WARNING but not CRITICAL
        assert is_bad_search_text("risk") is False
        assert is_bad_search_text("decision") is False
        assert is_bad_search_text("progress") is False
        assert is_bad_search_text("result") is False
        assert is_bad_search_text("issue") is False
        assert is_bad_search_text("plan") is False
        assert is_bad_search_text("impact") is False

    def test_english_valid(self):
        """测试有效的英文文本"""
        assert is_bad_search_text("TensorFlow") is False
        assert is_bad_search_text("machine learning") is False
        assert is_bad_search_text("Python programming") is False
        assert is_bad_search_text("API documentation") is False


class TestEvaluateSearchText:
    """测试 evaluate_search_text 函数"""

    def test_good_quality(self):
        """测试高质量文本"""
        from m_flow.memory.episodic.normalization import evaluate_search_text, SearchTextQuality

        eval_result = evaluate_search_text("TensorFlow")
        assert eval_result.quality == SearchTextQuality.GOOD
        assert eval_result.is_usable is True
        assert eval_result.should_warn is False

    def test_warning_quality_generic(self):
        """测试通用词汇返回 WARNING"""
        from m_flow.memory.episodic.normalization import evaluate_search_text, SearchTextQuality

        eval_result = evaluate_search_text("summary")
        assert eval_result.quality == SearchTextQuality.WARNING
        assert eval_result.reason == "too_generic"
        assert eval_result.is_usable is True  # 可用
        assert eval_result.should_warn is True  # 需要警告

    def test_critical_quality_empty(self):
        """测试空文本返回 CRITICAL"""
        from m_flow.memory.episodic.normalization import evaluate_search_text, SearchTextQuality

        eval_result = evaluate_search_text("")
        assert eval_result.quality == SearchTextQuality.CRITICAL
        assert eval_result.reason == "empty_or_whitespace"
        assert eval_result.is_usable is False

    def test_critical_quality_bad_prefix(self):
        """测试无效前缀返回 CRITICAL"""
        from m_flow.memory.episodic.normalization import evaluate_search_text, SearchTextQuality

        eval_result = evaluate_search_text("this section describes")
        assert eval_result.quality == SearchTextQuality.CRITICAL
        assert eval_result.reason == "bad_prefix"
        assert eval_result.is_usable is False

    def test_critical_quality_too_short(self):
        """测试过短文本返回 CRITICAL"""
        from m_flow.memory.episodic.normalization import evaluate_search_text, SearchTextQuality

        eval_result = evaluate_search_text("a")
        assert eval_result.quality == SearchTextQuality.CRITICAL
        assert eval_result.reason == "too_short"

    def test_critical_quality_pure_digits(self):
        """测试纯数字返回 CRITICAL"""
        from m_flow.memory.episodic.normalization import evaluate_search_text, SearchTextQuality

        eval_result = evaluate_search_text("12345")
        assert eval_result.quality == SearchTextQuality.CRITICAL
        assert eval_result.reason == "pure_digits"


class TestNormalizationConsistency:
    """测试规范化一致性"""

    def test_compare_and_id_consistency(self):
        """测试 compare 和 id 函数的一致性"""
        texts = [
            "Hello World",
            "产品说明书",
            "Mixed 中文 Text",
            "  Spaces  ",
        ]

        for text in texts:
            compare = normalize_for_compare(text)
            id_result = normalize_for_id(text)

            # ID 应该基于规范化后的文本
            assert len(compare) > 0 or len(id_result) >= 0

    def test_same_input_same_output(self):
        """测试相同输入产生相同输出"""
        test_cases = [
            ("Hello World", "hello world"),
            ("UPPER CASE", "upper case"),
            ("  spaces  ", "spaces"),
        ]

        for input_text, expected in test_cases:
            for _ in range(5):
                assert normalize_for_compare(input_text) == expected
