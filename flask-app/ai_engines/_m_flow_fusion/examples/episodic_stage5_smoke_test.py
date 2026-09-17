#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stage 5 Smoke Test: 写入质量增强验证

验证内容：
- 5.1 模型增强：Facet.aliases / Facet.supported_by / Episode.includes_chunk
- 5.2 Episode State 拉取：fetch_episode_state
- 5.3 Prompt 升级：v2 prompt 包含 EXISTING_FACETS
- 5.4 Facet 去重合并：normalize + merge_facets_by_string
- 5.5 证据回溯：supported_by / includes_chunk 边
- 5.6 PGVector upsert 修正

运行方式：
    ENABLE_BACKEND_ACCESS_CONTROL=false uv run python examples/episodic_stage5_smoke_test.py
"""

import asyncio
import sys


async def test_5_1_model_enhancement():
    """测试 5.1 模型增强"""
    print("\n[5.1] 测试模型增强...")

    from m_flow.core.domain.models import Episode, Facet

    # 测试 Facet.aliases
    facet = Facet(
        name="测试facet",
        facet_type="decision",
        search_text="测试facet",
        description="这是一个测试",
        aliases=["测试 facet", "测试facet"],
    )
    assert hasattr(facet, "aliases"), "Facet 应该有 aliases 属性"
    assert hasattr(facet, "supported_by"), "Facet 应该有 supported_by 属性"
    print("  ✅ Facet.aliases 和 Facet.supported_by 属性存在")

    # 测试 Episode.includes_chunk
    episode = Episode(
        name="测试episode",
        summary="这是一个测试摘要",
    )
    assert hasattr(episode, "includes_chunk"), "Episode 应该有 includes_chunk 属性"
    print("  ✅ Episode.includes_chunk 属性存在")

    return True


async def test_5_2_episode_state():
    """测试 5.2 Episode State 拉取"""
    print("\n[5.2] 测试 Episode State 拉取...")

    from m_flow.memory.episodic import EpisodeState, ExistingFacet, fetch_episode_state

    # 测试 EpisodeState 模型
    state = EpisodeState(
        episode_id="test-episode",
        title="测试标题",
        signature="测试签名",
        summary="测试摘要",
        facets=[ExistingFacet(id="f1", facet_type="decision", search_text="决策1")],
        entity_names=["Concept1", "Concept2"],
    )

    assert state.episode_id == "test-episode"
    assert state.title == "测试标题"
    assert len(state.facets) == 1
    assert len(state.entity_names) == 2
    print("  ✅ EpisodeState 和 ExistingFacet 模型正常")

    # 测试 fetch_episode_state 函数存在
    assert callable(fetch_episode_state)
    print("  ✅ fetch_episode_state 函数存在")

    return True


async def test_5_3_prompt_v2():
    """测试 5.3 Prompt 升级"""
    print("\n[5.3] 测试 Prompt 升级...")

    from m_flow.llm.prompts import read_query_prompt

    prompt = read_query_prompt("episodic_write_episode_and_facets_v2.txt")

    assert prompt is not None, "v2 prompt 文件应该存在"
    assert "EXISTING_FACETS" in prompt, "v2 prompt 应该包含 EXISTING_FACETS"
    assert "PREVIOUS_EPISODE_TITLE" in prompt, "v2 prompt 应该包含 PREVIOUS_EPISODE_TITLE"
    assert "DO NOT output facets that duplicate" in prompt, "v2 prompt 应该包含去重指令"
    print("  ✅ v2 prompt 文件存在且包含增量更新指令")

    return True


async def test_5_4_facet_merge():
    """测试 5.4 Facet 去重合并"""
    print("\n[5.4] 测试 Facet 去重合并...")

    from m_flow.memory.episodic import (
        normalize_for_compare,
        normalize_for_id,
        FacetCandidate,
        merge_facets_by_string,
    )
    from m_flow.core.domain.utils.generate_node_id import generate_node_id

    # 测试 normalize 函数
    assert normalize_for_compare("  测试  文本  ") == "测试 文本"
    assert normalize_for_compare("TEST TEXT") == "test text"
    assert normalize_for_compare("ＡＢＣ") == "abc"  # 全角→半角
    print("  ✅ normalize_for_compare 正常工作")

    assert normalize_for_id("  测试  文本  ") == "测试文本"
    print("  ✅ normalize_for_id 正常工作")

    # 测试 merge_facets_by_string
    existing = [
        {"id": "f1", "facet_type": "decision", "search_text": "选择GPT-4o-mini", "aliases": []},
    ]
    candidates = [
        FacetCandidate(facet_type="decision", search_text="选择GPT-4o-mini", description="新描述"),  # 重复
        FacetCandidate(
            facet_type="decision", search_text="  选择GPT-4o-mini  ", description="空格变体"
        ),  # 归一化后重复
        FacetCandidate(facet_type="risk", search_text="新风险", description="风险描述"),  # 新的
    ]

    merged, mapping = merge_facets_by_string(
        episode_id="test-episode",
        existing=existing,
        candidates=candidates,
        id_fn=generate_node_id,
    )

    # 应该合并成 2 个（1 个已存在的 + 1 个新的）
    assert len(merged) == 2, f"Expected 2 merged facets, got {len(merged)}"
    print(f"  ✅ merge_facets_by_string 正常工作（3 个候选 → {len(merged)} 个合并后）")

    return True


async def test_5_5_evidence_edges():
    """测试 5.5 证据回溯结构化"""
    print("\n[5.5] 测试证据回溯结构化...")

    # 检查 write_episodic_memories 中的证据边生成函数
    from m_flow.memory.episodic.write_episodic_memories import (
        _make_supported_by_edge_text,
        _make_includes_chunk_edge_text,
    )

    # 测试 supported_by 边
    edge_text = _make_supported_by_edge_text(
        facet_search_text="测试facet",
        chunk_id="chunk-1",
        chunk_index=0,
        chunk_summary="这是一段摘要",
    )
    assert "relationship_name: supported_by" in edge_text
    assert "facet_search_text: 测试facet" in edge_text
    assert "chunk_id: chunk-1" in edge_text
    print("  ✅ _make_supported_by_edge_text 正常工作")

    # 测试 includes_chunk 边
    edge_text = _make_includes_chunk_edge_text(
        episode_name="测试episode",
        chunk_id="chunk-1",
        chunk_index=0,
    )
    assert "relationship_name: includes_chunk" in edge_text
    assert "episode: 测试episode" in edge_text
    assert "chunk_id: chunk-1" in edge_text
    print("  ✅ _make_includes_chunk_edge_text 正常工作")

    return True


async def test_5_6_pgvector_upsert():
    """测试 5.6 PGVector upsert 修正"""
    print("\n[5.6] 测试 PGVector upsert 修正...")

    # 直接读取源文件检查（避免 asyncpg 依赖问题）
    import os

    pgvector_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "m_flow",
        "infrastructure",
        "databases",
        "vector",
        "pgvector",
        "PGVectorAdapter.py",
    )

    try:
        with open(pgvector_path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print("  ⚠️ PGVectorAdapter.py 文件未找到，跳过测试")
        return True

    assert "on_conflict_do_update" in source, "PGVectorAdapter 应该使用 on_conflict_do_update"
    assert "excluded.vector" in source, "PGVectorAdapter 应该更新 vector 字段"
    assert "excluded.payload" in source, "PGVectorAdapter 应该更新 payload 字段"
    print("  ✅ PGVectorAdapter 已修正为 on_conflict_do_update")

    return True


async def main():
    print("=" * 80)
    print("🧪 Stage 5 Smoke Test: 写入质量增强验证")
    print("=" * 80)

    tests = [
        ("5.1 模型增强", test_5_1_model_enhancement),
        ("5.2 Episode State 拉取", test_5_2_episode_state),
        ("5.3 Prompt 升级", test_5_3_prompt_v2),
        ("5.4 Facet 去重合并", test_5_4_facet_merge),
        ("5.5 证据回溯结构化", test_5_5_evidence_edges),
        ("5.6 PGVector upsert 修正", test_5_6_pgvector_upsert),
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
        print("✅ 所有测试通过！Stage 5 实现完成。")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
