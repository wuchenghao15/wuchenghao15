#!/usr/bin/env python3
"""
Stage 4 Smoke Test: MemorySpace ID-Filtered Projection

验证 Stage 4 的实现：
1. Kuzu adapter 新增 get_nodeset_id_filtered_graph_data
2. MemoryGraph 支持 nodeset + relevant_ids 过滤 + strict 模式
3. episodic_triplet_search 启用 strict_nodeset_filtering
4. relevant_ids 上限裁剪

运行方式：
    cd m_flow-main
    uv run python examples/episodic_stage4_smoke_test.py
"""

import asyncio
import sys


async def test_imports():
    """验证所有必要的导入"""
    print("\n" + "=" * 60)
    print("Stage 4 Smoke Test: MemorySpace ID-Filtered Projection")
    print("=" * 60)

    print("\n[1] 测试导入...")

    # 1. 导入 KuzuAdapter
    try:
        from m_flow.adapters.graph.kuzu.adapter import KuzuAdapter

        # 检查新方法存在
        assert hasattr(KuzuAdapter, "get_nodeset_id_filtered_graph_data"), (
            "KuzuAdapter 缺少 get_nodeset_id_filtered_graph_data"
        )
        print("  ✓ KuzuAdapter.get_nodeset_id_filtered_graph_data 存在")
    except (ImportError, AssertionError) as e:
        print(f"  ✗ KuzuAdapter 导入失败: {e}")
        return False

    # 2. 导入 MemoryGraph
    try:
        from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
        import inspect

        # 检查 project_graph_from_db 新增 strict_nodeset_filtering 参数
        sig = inspect.signature(MemoryGraph.project_graph_from_db)
        assert "strict_nodeset_filtering" in sig.parameters, "project_graph_from_db 缺少 strict_nodeset_filtering 参数"
        print("  ✓ MemoryGraph.project_graph_from_db 支持 strict_nodeset_filtering")

        # 检查 _extract_typed_subgraph 新增参数
        sig2 = inspect.signature(MemoryGraph._extract_typed_subgraph)
        assert "relevant_ids_to_filter" in sig2.parameters, "_extract_typed_subgraph 缺少 relevant_ids_to_filter 参数"
        assert "strict_nodeset_filtering" in sig2.parameters, (
            "_extract_typed_subgraph 缺少 strict_nodeset_filtering 参数"
        )
        print("  ✓ MemoryGraph._extract_typed_subgraph 支持 relevant_ids_to_filter 和 strict")
    except (ImportError, AssertionError) as e:
        print(f"  ✗ MemoryGraph 导入失败: {e}")
        return False

    # 3. 导入 episodic_triplet_search
    try:
        from m_flow.retrieval.utils.episodic_triplet_search import (
            episodic_triplet_search,
            MAX_RELEVANT_IDS,
        )
        import inspect

        # 检查新增 max_relevant_ids 参数
        sig = inspect.signature(episodic_triplet_search)
        assert "max_relevant_ids" in sig.parameters, "episodic_triplet_search 缺少 max_relevant_ids 参数"
        print(f"  ✓ episodic_triplet_search 支持 max_relevant_ids (默认: {MAX_RELEVANT_IDS})")
    except (ImportError, AssertionError) as e:
        print(f"  ✗ episodic_triplet_search 导入失败: {e}")
        return False

    return True


async def test_kuzu_adapter_method_signature():
    """验证 Kuzu adapter 新方法签名"""
    print("\n[2] 测试 KuzuAdapter.get_nodeset_id_filtered_graph_data 签名...")

    import inspect
    from m_flow.adapters.graph.kuzu.adapter import KuzuAdapter

    sig = inspect.signature(KuzuAdapter.get_nodeset_id_filtered_graph_data)
    params = list(sig.parameters.keys())

    expected_params = ["self", "node_type", "node_name", "target_ids"]
    for p in expected_params:
        assert p in params, f"缺少参数 {p}"
        print(f"  ✓ 参数 {p} 存在")

    # 检查返回类型注解
    annotations = KuzuAdapter.get_nodeset_id_filtered_graph_data.__annotations__
    assert "return" in annotations, "缺少返回类型注解"
    print("  ✓ 返回类型注解存在")

    return True


async def test_m_flow_graph_strict_mode():
    """验证 MemoryGraph strict 模式逻辑"""
    print("\n[3] 测试 MemoryGraph strict 模式逻辑...")

    import inspect
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph

    # 读取 _extract_typed_subgraph 源码，验证 strict 逻辑
    source = inspect.getsource(MemoryGraph._extract_typed_subgraph)

    # 验证关键逻辑存在
    assert "strict_nodeset_filtering" in source, "_extract_typed_subgraph 源码中缺少 strict_nodeset_filtering"
    print("  ✓ _extract_typed_subgraph 包含 strict_nodeset_filtering 逻辑")

    assert "get_nodeset_id_filtered_graph_data" in source, (
        "_extract_typed_subgraph 源码中缺少 get_nodeset_id_filtered_graph_data 调用"
    )
    print("  ✓ _extract_typed_subgraph 调用 get_nodeset_id_filtered_graph_data")

    assert "if strict_nodeset_filtering" in source, "_extract_typed_subgraph 缺少 strict 模式判断"
    print("  ✓ _extract_typed_subgraph 包含 strict 模式判断逻辑")

    return True


async def test_episodic_search_strict_and_limit():
    """验证 episodic_triplet_search 的 strict 模式和上限裁剪"""
    print("\n[4] 测试 episodic_triplet_search strict 模式和上限裁剪...")

    import inspect
    from m_flow.retrieval.utils.episodic_triplet_search import (
        get_episodic_memory_fragment,
        episodic_triplet_search,
    )

    # 验证 get_episodic_memory_fragment 使用 strict
    source1 = inspect.getsource(get_episodic_memory_fragment)
    assert "strict_nodeset_filtering=True" in source1, "get_episodic_memory_fragment 没有启用 strict"
    print("  ✓ get_episodic_memory_fragment 启用 strict_nodeset_filtering=True")

    # 验证 episodic_triplet_search 的上限裁剪
    source2 = inspect.getsource(episodic_triplet_search)
    assert "max_relevant_ids" in source2, "episodic_triplet_search 没有 max_relevant_ids 参数"
    assert "[:max_relevant_ids]" in source2, "episodic_triplet_search 没有进行上限裁剪"
    print("  ✓ episodic_triplet_search 包含 relevant_ids 上限裁剪")

    # 验证验收日志
    assert "[episodic] projected" in source2, "episodic_triplet_search 缺少验收日志"
    print("  ✓ episodic_triplet_search 包含验收日志")

    return True


async def test_backward_compatibility():
    """验证向后兼容性 - strict 默认 False"""
    print("\n[5] 测试向后兼容性...")

    import inspect
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph

    # 检查 project_graph_from_db 的 strict_nodeset_filtering 默认值
    sig = inspect.signature(MemoryGraph.project_graph_from_db)
    strict_param = sig.parameters.get("strict_nodeset_filtering")
    assert strict_param is not None, "缺少 strict_nodeset_filtering 参数"
    assert strict_param.default is False, "strict_nodeset_filtering 默认值应为 False"
    print("  ✓ strict_nodeset_filtering 默认值为 False（向后兼容）")

    # 检查 _extract_typed_subgraph 的默认值
    sig2 = inspect.signature(MemoryGraph._extract_typed_subgraph)
    strict_param2 = sig2.parameters.get("strict_nodeset_filtering")
    assert strict_param2 is not None, "_extract_typed_subgraph 缺少 strict_nodeset_filtering 参数"
    assert strict_param2.default is False, "_extract_typed_subgraph 的 strict 默认值应为 False"
    print("  ✓ _extract_typed_subgraph strict 默认值为 False（向后兼容）")

    return True


async def main():
    """运行所有测试"""
    results = []

    results.append(("导入测试", await test_imports()))
    results.append(("Kuzu adapter 方法签名测试", await test_kuzu_adapter_method_signature()))
    results.append(("MemoryGraph strict 模式测试", await test_m_flow_graph_strict_mode()))
    results.append(("episodic_triplet_search 测试", await test_episodic_search_strict_and_limit()))
    results.append(("向后兼容性测试", await test_backward_compatibility()))

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
        print("✓ Stage 4 Smoke Test 全部通过！")
        print("\nStage 4 收益：")
        print("  - MemorySpace 投影规模随 query 命中范围变化，不会随 nodeset 总规模爆炸")
        print("  - strict 模式下，query 不命中 episodic 节点时直接返回空")
        print("  - 向后兼容：现有 MemorySpace 检索不受影响（strict 默认 False）")
        print("\n验收观察点：")
        print('  - 日志中会出现 "[episodic] projected nodes=X edges=Y"')
        print("  - Stage 3 全量投影时 nodes/edges 随 episodic 存量增长")
        print("  - Stage 4 ID-filter 后 nodes/edges 基本稳定在小规模")
    else:
        print("✗ 部分测试失败，请检查上述错误")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
