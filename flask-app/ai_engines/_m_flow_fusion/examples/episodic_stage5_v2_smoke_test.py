#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stage 5.8-5.13 Smoke Test: aliases 兜底召回 + 语义同义合并

验证内容：
- 5.8 Facet.aliases_text 索引字段
- 5.9 EpisodicFacetDraft.aliases + EpisodicAliasUpdate
- 5.11 aliases.py + semantic_merge.py
- 5.12 write_episodic_memories v3
- 5.13 episodic_triplet_search v2（aliases 兜底 + best-by-id）

Note: 5.10 Prompt v3 测试已移除 (episodic_write_episode_and_facets_v3.txt 从未被实际调用)

运行方式：
    ENABLE_BACKEND_ACCESS_CONTROL=false uv run python examples/episodic_stage5_v2_smoke_test.py
"""

import asyncio
import sys


async def test_5_8_facet_aliases_text():
    """测试 5.8 Facet.aliases_text 索引字段"""
    print("\n[5.8] 测试 Facet.aliases_text 索引字段...")

    from m_flow.core.domain.models import Facet

    facet = Facet(
        name="测试facet",
        facet_type="decision",
        search_text="测试facet",
        aliases=["别名1", "别名2"],
        aliases_text="别名1\n别名2",
    )

    assert hasattr(facet, "aliases_text"), "Facet 应该有 aliases_text 属性"
    assert "aliases_text" in facet.metadata.get("index_fields", [])
    print(f"  ✅ Facet.metadata.index_fields = {facet.metadata.get('index_fields')}")

    return True


async def test_5_9_llm_models():
    """测试 5.9 LLM 输出模型"""
    print("\n[5.9] 测试 LLM 输出模型...")

    from m_flow.memory.episodic import (
        EpisodicFacetDraft,
        EpisodicAliasUpdate,
        EpisodicWriteDraft,
    )

    # EpisodicFacetDraft.aliases
    draft = EpisodicFacetDraft(
        facet_type="decision",
        search_text="选择GPT-4o-mini",
        aliases=["GPT选型", "LLM决策"],
    )
    assert draft.aliases == ["GPT选型", "LLM决策"]
    print("  ✅ EpisodicFacetDraft.aliases 正常")

    # EpisodicAliasUpdate
    update = EpisodicAliasUpdate(
        target_facet_search_text="选择GPT-4o-mini",
        new_aliases=["基础模型选型"],
    )
    assert update.target_facet_search_text == "选择GPT-4o-mini"
    print("  ✅ EpisodicAliasUpdate 正常")

    # EpisodicWriteDraft.alias_updates
    write_draft = EpisodicWriteDraft(
        title="测试",
        signature="test",
        summary="测试摘要",
        alias_updates=[update],
    )
    assert len(write_draft.alias_updates) == 1
    print("  ✅ EpisodicWriteDraft.alias_updates 正常")

    return True


async def test_5_11_aliases_tools():
    """测试 5.11 aliases.py + semantic_merge.py"""
    print("\n[5.11] 测试 aliases 工具模块...")

    from m_flow.memory.episodic import (
        is_bad_alias,
        clean_aliases,
        make_aliases_text,
        SemanticFacetMatcher,
        ExistingFacetInfo,
    )

    # is_bad_alias
    assert is_bad_alias("") == True
    assert is_bad_alias("短") == True
    assert is_bad_alias("风险") == True
    assert is_bad_alias("本段讨论了...") == True
    assert is_bad_alias("选择GPT-4o-mini") == False
    print("  ✅ is_bad_alias 正常工作")

    # clean_aliases
    cleaned = clean_aliases(
        search_text="选择GPT-4o-mini",
        aliases=["选择GPT-4o-mini", "GPT选型", "风险", "短"],
    )
    assert "GPT选型" in cleaned
    assert "风险" not in cleaned
    assert "选择GPT-4o-mini" not in cleaned
    print(f"  ✅ clean_aliases: {cleaned}")

    # make_aliases_text
    aliases_text = make_aliases_text(["别名1", "别名2"])
    assert aliases_text == "别名1\n别名2"
    print("  ✅ make_aliases_text 正常工作")

    # SemanticFacetMatcher
    matcher = SemanticFacetMatcher(enabled=False, threshold=0.90)
    assert matcher.enabled == False
    print("  ✅ SemanticFacetMatcher 初始化成功")

    # ExistingFacetInfo
    info = ExistingFacetInfo(
        id="f1",
        facet_type="decision",
        search_text="选择GPT-4o-mini",
        aliases=["GPT选型"],
    )
    assert info.id == "f1"
    print("  ✅ ExistingFacetInfo 正常工作")

    return True


async def test_5_12_write_v3():
    """测试 5.12 write_episodic_memories v3"""
    print("\n[5.12] 测试 write_episodic_memories v3...")

    from m_flow.memory.episodic import write_episodic_memories
    import inspect

    source = inspect.getsource(write_episodic_memories)

    assert "alias_updates" in source, "v3 应该处理 alias_updates"
    assert "aliases_text" in source, "v3 应该生成 aliases_text"
    assert "make_aliases_text" in source, "v3 应该调用 make_aliases_text"
    assert "SemanticFacetMatcher" in source, "v3 应该使用 SemanticFacetMatcher"
    print("  ✅ write_episodic_memories v3 包含所有增强功能")

    return True


async def test_5_13_search_v2():
    """测试 5.13 episodic_triplet_search v2"""
    print("\n[5.13] 测试 episodic_triplet_search v2...")

    from m_flow.retrieval.utils.episodic_triplet_search import (
        episodic_triplet_search,
        _best_node_distance_by_id,
    )
    import inspect

    source = inspect.getsource(episodic_triplet_search)

    assert "Facet_anchor_text" in source, "v2 应该包含 Facet_anchor_text 集合"
    assert "best_by_id" in source, "v2 应该使用 best_by_id 聚合"
    print("  ✅ episodic_triplet_search v2 包含 anchor 兜底召回")

    # 测试 _best_node_distance_by_id
    class MockResult:
        def __init__(self, id, score):
            self.id = id
            self.score = score

    node_distances = {
        "Facet_search_text": [MockResult("f1", 0.3)],
        "Facet_anchor_text": [MockResult("f1", 0.2)],  # f1 在两个集合都命中
    }

    best = _best_node_distance_by_id(node_distances)
    assert best.get("f1") == 0.2  # 取 min
    print(f"  ✅ _best_node_distance_by_id: f1={best.get('f1')} (取 min)")

    return True


async def main():
    print("=" * 80)
    print("🧪 Stage 5.8-5.13 Smoke Test: aliases 兜底召回 + 语义同义合并")
    print("=" * 80)

    tests = [
        ("5.8 Facet.aliases_text", test_5_8_facet_aliases_text),
        ("5.9 LLM 输出模型", test_5_9_llm_models),
        ("5.11 aliases 工具模块", test_5_11_aliases_tools),
        ("5.12 write_episodic_memories v3", test_5_12_write_v3),
        ("5.13 episodic_triplet_search v2", test_5_13_search_v2),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            result = await test_fn()
            if result:
                passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    print("=" * 80)

    if failed > 0:
        print("❌ 有测试失败")
        sys.exit(1)
    else:
        print("✅ 所有测试通过！Stage 5.8-5.13 实现完成。")
        print("\n📋 实现总结：")
        print("  - Facet.aliases_text 参与向量索引（兜底召回）")
        print("  - LLM 可生成 aliases + alias_updates")
        print("  - 字符串去重 + 可选语义同义合并")
        print("  - 检索时 Facet_search_text + Facet_aliases_text 双入口")
        print("  - best-by-id(min) 防止多集合命中时排序抖动")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
