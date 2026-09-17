# m_flow/tests/unit/tasks/episodic/test_facet_points_refiner.py
"""
FacetPointsRefiner 纯逻辑函数单元测试

测试以下公开函数:
- is_bad_point_handle: 判断 point.search_text 是否不合格
- extract_anchors_from_description: 从描述中提取锚点
- check_coverage: 检查 points 是否覆盖所有锚点
"""

from m_flow.memory.episodic.facet_points_refiner import (
    is_bad_point_handle,
    extract_anchors_from_description,
    check_coverage,
)
from m_flow.memory.episodic.models import FacetPointDraft


# =============================================================================
# TestIsBadPointHandle - 测试 is_bad_point_handle 函数
# =============================================================================


class TestIsBadPointHandle:
    """测试 is_bad_point_handle 函数"""

    # -------------------------------------------------------------------------
    # 边界条件测试
    # -------------------------------------------------------------------------

    def test_empty_string_returns_true(self):
        """空字符串应返回 True"""
        assert is_bad_point_handle("") is True

    def test_none_like_empty_returns_true(self):
        """纯空白字符串应返回 True"""
        assert is_bad_point_handle("   ") is True
        assert is_bad_point_handle("\t\n") is True

    # -------------------------------------------------------------------------
    # 过于通用的词汇测试 (间接测试 _is_too_generic)
    # -------------------------------------------------------------------------

    def test_generic_term_reason_returns_true(self):
        """'原因' 这种过于通用的词应返回 True"""
        assert is_bad_point_handle("原因") is True

    def test_generic_term_problem_returns_true(self):
        """'问题' 这种过于通用的词应返回 True"""
        assert is_bad_point_handle("问题") is True

    def test_generic_term_impact_returns_true(self):
        """'影响' 这种过于通用的词应返回 True"""
        assert is_bad_point_handle("影响") is True

    def test_generic_term_background_returns_true(self):
        """'背景' 这种过于通用的词应返回 True"""
        assert is_bad_point_handle("背景") is True

    def test_generic_term_method_returns_true(self):
        """'方法' 这种过于通用的词应返回 True"""
        assert is_bad_point_handle("方法") is True

    # -------------------------------------------------------------------------
    # 正常文本测试
    # -------------------------------------------------------------------------

    def test_specific_text_with_anchor_returns_false(self):
        """包含锚点（如 API）的具体文本应返回 False"""
        assert is_bad_point_handle("API认证模块的错误处理") is False

    def test_text_with_module_name_returns_false(self):
        """包含模块名的文本应返回 False"""
        assert is_bad_point_handle("UserService 的缓存策略") is False

    # -------------------------------------------------------------------------
    # 段落样式检测 (间接测试 _is_paragraph_style)
    # -------------------------------------------------------------------------

    def test_paragraph_with_multiple_periods_returns_true(self):
        """包含多个句号的长段落应返回 True"""
        text = "这是第一句话。这是第二句话。这是第三句话。这是第四句话。"
        assert is_bad_point_handle(text) is True

    def test_paragraph_with_multiple_newlines_returns_true(self):
        """包含多个换行的长段落应返回 True"""
        text = "第一行\n第二行\n第三行\n第四行"
        assert is_bad_point_handle(text) is True

    # -------------------------------------------------------------------------
    # 有锚点的文本 (间接测试 _has_concrete_anchor)
    # -------------------------------------------------------------------------

    def test_text_with_api_key_returns_false(self):
        """包含 API_KEY 这种标识符的文本应返回 False"""
        assert is_bad_point_handle("API_KEY_12345") is False

    def test_text_with_percentage_returns_false(self):
        """包含百分比的文本应返回 False"""
        assert is_bad_point_handle("90%的用户") is False

    def test_text_with_number_unit_returns_false(self):
        """包含数字+单位的文本应返回 False"""
        assert is_bad_point_handle("延迟300ms") is False

    def test_text_with_camelcase_returns_false(self):
        """包含 CamelCase 命名的文本应返回 False"""
        assert is_bad_point_handle("UserService") is False

    # -------------------------------------------------------------------------
    # 组合条件测试
    # -------------------------------------------------------------------------

    def test_short_generic_without_anchor_returns_true(self):
        """短文本 + 无锚点 + 通用词 应返回 True"""
        assert is_bad_point_handle("这是问题") is True

    def test_short_with_anchor_returns_false(self):
        """短文本 + 有锚点 应返回 False"""
        assert is_bad_point_handle("API错误") is False


# =============================================================================
# TestExtractAnchorsFromDescription - 测试 extract_anchors_from_description 函数
# =============================================================================


class TestExtractAnchorsFromDescription:
    """测试 extract_anchors_from_description 函数"""

    # -------------------------------------------------------------------------
    # 边界条件测试
    # -------------------------------------------------------------------------

    def test_empty_description_returns_empty_set(self):
        """空描述应返回空集合"""
        assert extract_anchors_from_description("") == set()

    def test_none_description_returns_empty_set(self):
        """None 描述应返回空集合"""
        assert extract_anchors_from_description(None) == set()

    # -------------------------------------------------------------------------
    # 百分比提取
    # -------------------------------------------------------------------------

    def test_extract_percentage(self):
        """应提取百分比"""
        result = extract_anchors_from_description("提升了90%的性能")
        assert "90%" in result

    def test_extract_percentage_with_decimal(self):
        """应提取带小数的百分比"""
        result = extract_anchors_from_description("准确率达到99.5%")
        assert "99.5%" in result

    # -------------------------------------------------------------------------
    # 数字+单位提取
    # -------------------------------------------------------------------------

    def test_extract_number_with_ms(self):
        """应提取毫秒单位"""
        result = extract_anchors_from_description("延迟降低到300ms")
        assert "300ms" in result

    def test_extract_number_with_chinese_unit(self):
        """应提取中文单位"""
        result = extract_anchors_from_description("处理了5万条数据")
        assert "5万" in result

    # -------------------------------------------------------------------------
    # CamelCase 提取
    # -------------------------------------------------------------------------

    def test_extract_camelcase(self):
        """应提取 CamelCase 命名"""
        result = extract_anchors_from_description("使用 UserService 处理请求")
        assert "UserService" in result

    def test_extract_multiple_camelcase(self):
        """应提取多个 CamelCase"""
        result = extract_anchors_from_description("AuthController 调用 UserService")
        assert "AuthController" in result
        assert "UserService" in result

    # -------------------------------------------------------------------------
    # 下划线命名提取
    # -------------------------------------------------------------------------

    def test_extract_underscore_naming(self):
        """应提取下划线命名"""
        result = extract_anchors_from_description("设置 user_name 字段")
        assert "user_name" in result

    def test_extract_underscore_with_numbers(self):
        """应提取带数字的下划线命名"""
        result = extract_anchors_from_description("调用 api_v2_endpoint")
        assert "api_v2_endpoint" in result

    # -------------------------------------------------------------------------
    # 大写缩写提取
    # -------------------------------------------------------------------------

    def test_extract_uppercase_abbreviation(self):
        """应提取大写缩写"""
        result = extract_anchors_from_description("使用 API 和 SDK")
        assert "API" in result
        assert "SDK" in result

    def test_extract_rag_abbreviation(self):
        """应提取 RAG 缩写"""
        result = extract_anchors_from_description("实现 RAG 检索增强")
        assert "RAG" in result

    # -------------------------------------------------------------------------
    # 综合测试
    # -------------------------------------------------------------------------

    def test_extract_multiple_types(self):
        """应同时提取多种类型的锚点"""
        result = extract_anchors_from_description("UserService 处理了90%的请求，延迟降低到50ms，使用 API")
        assert "UserService" in result
        assert "90%" in result
        assert "50ms" in result
        assert "API" in result


# =============================================================================
# TestCheckCoverage - 测试 check_coverage 函数
# =============================================================================


class TestCheckCoverage:
    """测试 check_coverage 函数"""

    # -------------------------------------------------------------------------
    # 边界条件测试
    # -------------------------------------------------------------------------

    def test_empty_anchors_returns_empty_set(self):
        """空锚点集应返回空集合"""
        points = [FacetPointDraft(search_text="test", aliases=[])]
        result = check_coverage(points, set())
        assert result == set()

    def test_empty_points_returns_all_anchors(self):
        """空 points 应返回所有锚点"""
        anchors = {"API", "SDK"}
        result = check_coverage([], anchors)
        assert result == anchors

    # -------------------------------------------------------------------------
    # 完全覆盖测试
    # -------------------------------------------------------------------------

    def test_full_coverage_returns_empty(self):
        """完全覆盖时应返回空集合"""
        points = [
            FacetPointDraft(search_text="API 调用", aliases=[]),
            FacetPointDraft(search_text="SDK 集成", aliases=[]),
        ]
        anchors = {"API", "SDK"}
        result = check_coverage(points, anchors)
        assert result == set()

    def test_coverage_case_insensitive(self):
        """覆盖检查应忽略大小写"""
        points = [
            FacetPointDraft(search_text="api 调用", aliases=[]),
        ]
        anchors = {"API"}
        result = check_coverage(points, anchors)
        assert result == set()

    # -------------------------------------------------------------------------
    # 部分覆盖测试
    # -------------------------------------------------------------------------

    def test_partial_coverage_returns_uncovered(self):
        """部分覆盖时应返回未覆盖的锚点"""
        points = [
            FacetPointDraft(search_text="API 调用", aliases=[]),
        ]
        anchors = {"API", "SDK", "RAG"}
        result = check_coverage(points, anchors)
        assert "SDK" in result
        assert "RAG" in result
        assert "API" not in result

    # -------------------------------------------------------------------------
    # 通过 aliases 覆盖测试
    # -------------------------------------------------------------------------

    def test_coverage_via_aliases(self):
        """应通过 aliases 实现覆盖"""
        points = [
            FacetPointDraft(search_text="接口调用", aliases=["API调用", "API请求"]),
        ]
        anchors = {"API"}
        result = check_coverage(points, anchors)
        assert result == set()

    def test_coverage_via_aliases_partial(self):
        """部分通过 aliases 覆盖"""
        points = [
            FacetPointDraft(search_text="服务调用", aliases=["API"]),
        ]
        anchors = {"API", "SDK"}
        result = check_coverage(points, anchors)
        assert "SDK" in result
        assert "API" not in result

    # -------------------------------------------------------------------------
    # 多 points 测试
    # -------------------------------------------------------------------------

    def test_multiple_points_coverage(self):
        """多个 points 共同实现覆盖"""
        points = [
            FacetPointDraft(search_text="API 处理", aliases=[]),
            FacetPointDraft(search_text="SDK 集成", aliases=[]),
            FacetPointDraft(search_text="RAG 检索", aliases=[]),
        ]
        anchors = {"API", "SDK", "RAG"}
        result = check_coverage(points, anchors)
        assert result == set()

    def test_one_point_covers_multiple_anchors(self):
        """一个 point 覆盖多个锚点"""
        points = [
            FacetPointDraft(search_text="API 和 SDK 的集成方案", aliases=[]),
        ]
        anchors = {"API", "SDK"}
        result = check_coverage(points, anchors)
        assert result == set()
