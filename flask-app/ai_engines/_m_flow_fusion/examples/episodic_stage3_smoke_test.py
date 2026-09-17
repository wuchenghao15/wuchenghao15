#!/usr/bin/env python3
"""
Stage 3 Smoke Test: Episodic MemoryTriplet Search

验证 episodic_triplet_search 的检索逻辑。

运行方式：
    cd m_flow-main
    uv run python examples/episodic_stage3_smoke_test.py

注意：
    - 这是一个简化的单元测试，主要验证函数签名和基本逻辑
    - 完整测试需要实际的图数据库和向量索引
"""

import asyncio
import sys
from uuid import uuid4, uuid5, NAMESPACE_OID


async def test_imports():
    """验证所有必要的导入"""
    print("\n" + "=" * 60)
    print("Stage 3 Smoke Test: Episodic MemoryTriplet Search")
    print("=" * 60)

    print("\n[1] 测试导入...")

    # 1. 导入 episodic_triplet_search
    try:
        from m_flow.retrieval.utils.episodic_triplet_search import (
            episodic_triplet_search,
            get_episodic_memory_fragment,
            _score_triplet,
        )

        print("  ✓ episodic_triplet_search 导入成功")
    except ImportError as e:
        print(f"  ✗ episodic_triplet_search 导入失败: {e}")
        return False

    # 2. 导入 EpisodicRetriever
    try:
        from m_flow.retrieval.episodic_retriever import (
            EpisodicRetriever,
            _inject_text_for_episodic_nodes,
        )

        print("  ✓ EpisodicRetriever 导入成功")
    except ImportError as e:
        print(f"  ✗ EpisodicRetriever 导入失败: {e}")
        return False

    # 3. 导入 RecallMode.EPISODIC
    try:
        from m_flow.search.types import RecallMode

        assert hasattr(RecallMode, "EPISODIC"), "RecallMode 没有 EPISODIC 属性"
        assert RecallMode.EPISODIC.value == "EPISODIC"
        print("  ✓ RecallMode.EPISODIC 导入成功")
    except (ImportError, AssertionError) as e:
        print(f"  ✗ RecallMode.EPISODIC 导入失败: {e}")
        return False

    return True


async def test_retriever_interface():
    """验证 EpisodicRetriever 接口"""
    print("\n[2] 测试 EpisodicRetriever 接口...")

    from m_flow.retrieval.episodic_retriever import EpisodicRetriever
    from m_flow.retrieval.base_graph_retriever import BaseGraphRetriever

    # 检查继承
    assert issubclass(EpisodicRetriever, BaseGraphRetriever), "EpisodicRetriever 应继承 BaseGraphRetriever"
    print("  ✓ EpisodicRetriever 继承 BaseGraphRetriever")

    # 检查初始化参数
    retriever = EpisodicRetriever(
        top_k=10,
        episodic_nodeset_name="TestMemorySpace",
        wide_search_top_k=50,
    )
    assert retriever.top_k == 10
    assert retriever.episodic_nodeset_name == "TestMemorySpace"
    assert retriever.wide_search_top_k == 50
    print("  ✓ EpisodicRetriever 初始化参数正确")

    # 检查方法存在
    assert hasattr(retriever, "get_context"), "缺少 get_context 方法"
    assert hasattr(retriever, "get_completion"), "缺少 get_completion 方法"
    assert hasattr(retriever, "get_triplets"), "缺少 get_triplets 方法"
    assert hasattr(retriever, "convert_retrieved_objects_to_context"), "缺少 convert_retrieved_objects_to_context 方法"
    print("  ✓ EpisodicRetriever 所有必要方法存在")

    return True


async def test_score_triplet():
    """验证 _score_triplet 评分函数"""
    print("\n[3] 测试 _score_triplet 评分函数...")

    from m_flow.retrieval.utils.episodic_triplet_search import _score_triplet
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge, Node

    # 创建模拟节点和边（注意：Node 使用 node_id 而非 id）
    node1 = Node(node_id=str(uuid4()), attributes={"type": "Episode"}, node_penalty=0.1)
    node2 = Node(node_id=str(uuid4()), attributes={"type": "Facet"}, node_penalty=0.2)

    # 手动设置 vector_distance（因为 node_penalty 会覆盖）
    node1.attributes["vector_distance"] = 0.1
    node2.attributes["vector_distance"] = 0.2

    edge = Edge(
        node1=node1,
        node2=node2,
        attributes={"relationship_type": "has_facet"},
        edge_penalty=0.15,
    )
    edge.attributes["vector_distance"] = 0.15

    score = _score_triplet(edge)
    expected_score = 0.1 + 0.2 + 0.15  # n1 + n2 + e
    assert abs(score - expected_score) < 0.001, f"评分错误: {score} != {expected_score}"
    print(f"  ✓ _score_triplet 评分正确: {score:.3f} (n1=0.1 + n2=0.2 + e=0.15)")

    # 测试默认距离
    node1_no_dist = Node(node_id=str(uuid4()), attributes={"type": "Episode"})
    node2_no_dist = Node(node_id=str(uuid4()), attributes={"type": "Facet"})
    edge_no_dist = Edge(
        node1=node1_no_dist,
        node2=node2_no_dist,
        attributes={"relationship_type": "has_facet"},
    )

    # 默认 node_penalty=3.5, edge_penalty=3.5，所以默认距离是 3.5 * 3 = 10.5
    score_default = _score_triplet(edge_no_dist)
    expected_default = 3.5 + 3.5 + 3.5
    assert abs(score_default - expected_default) < 0.001, f"默认评分应为 {expected_default}: {score_default}"
    print(f"  ✓ _score_triplet 默认距离处理正确: {score_default}")

    return True


async def test_inject_text():
    """验证 _inject_text_for_episodic_nodes 函数"""
    print("\n[4] 测试 _inject_text_for_episodic_nodes...")

    from m_flow.retrieval.episodic_retriever import _inject_text_for_episodic_nodes
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge, Node

    # 创建 Episode 节点（注意：Node 使用 node_id 而非 id）
    episode_node = Node(
        node_id=str(uuid4()),
        attributes={
            "type": "Episode",
            "summary": "This is the episode summary for testing",
            "name": "Test Episode",
        },
    )

    # 创建 Facet 节点
    facet_node = Node(
        node_id=str(uuid4()),
        attributes={
            "type": "Facet",
            "search_text": "risk mitigation",
            "description": "This is a detailed description for RAG",
        },
    )

    edge = Edge(
        node1=episode_node,
        node2=facet_node,
        attributes={"relationship_type": "has_facet"},
    )

    # 注入前检查（注意：Node 初始化会自动添加 vector_distance）
    assert "text" not in episode_node.attributes
    assert "text" not in facet_node.attributes

    # 执行注入
    _inject_text_for_episodic_nodes([edge])

    # 验证注入结果
    assert episode_node.attributes.get("text") == "This is the episode summary for testing"
    print("  ✓ Episode.summary 正确注入到 text")

    assert facet_node.attributes.get("text") == "This is a detailed description for RAG"
    print("  ✓ Facet.description 优先注入到 text")

    # 测试 Facet 只有 search_text 的情况
    facet_node_only_search = Node(
        node_id=str(uuid4()),
        attributes={
            "type": "Facet",
            "search_text": "only search text",
        },
    )
    edge2 = Edge(
        node1=episode_node,
        node2=facet_node_only_search,
        attributes={"relationship_type": "has_facet"},
    )
    _inject_text_for_episodic_nodes([edge2])
    assert facet_node_only_search.attributes.get("text") == "only search text"
    print("  ✓ Facet.search_text 作为 fallback 注入到 text")

    return True


async def test_recall_mode_integration():
    """验证 RecallMode.EPISODIC 集成"""
    print("\n[5] 测试 RecallMode.EPISODIC 集成...")

    from m_flow.search.types import RecallMode
    from m_flow.search.methods.get_recall_mode_tools import get_recall_mode_tools

    # 验证 EPISODIC 类型存在
    assert RecallMode.EPISODIC.value == "EPISODIC"
    print("  ✓ RecallMode.EPISODIC 定义正确")

    # 验证 get_recall_mode_tools 可以处理 EPISODIC
    # 注意：这会实际创建 EpisodicRetriever 实例
    try:
        tools = await get_recall_mode_tools(
            query_type=RecallMode.EPISODIC,
            query_text="test query",
            top_k=5,
        )
        assert len(tools) == 2, f"应该有 2 个工具 (get_completion, get_context): {len(tools)}"
        print(f"  ✓ get_recall_mode_tools 返回 {len(tools)} 个工具")
    except Exception as e:
        print(f"  ✗ get_recall_mode_tools 调用失败: {e}")
        return False

    return True


async def main():
    """运行所有测试"""
    results = []

    results.append(("导入测试", await test_imports()))
    results.append(("Retriever 接口测试", await test_retriever_interface()))
    results.append(("评分函数测试", await test_score_triplet()))
    results.append(("Text 注入测试", await test_inject_text()))
    results.append(("RecallMode 集成测试", await test_recall_mode_integration()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ Stage 3 Smoke Test 全部通过！")
        print("\n可以使用 RecallMode.EPISODIC 进行检索：")
        print("""
    await m_flow.search(
        query_text="这个项目目前最大的风险是什么？",
        query_type=RecallMode.EPISODIC,
        top_k=10,
    )
""")
    else:
        print("✗ 部分测试失败，请检查上述错误")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
