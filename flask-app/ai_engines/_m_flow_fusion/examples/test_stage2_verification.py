#!/usr/bin/env python3
"""
Stage2 验收测试：FacetPoint 写入 MVP

验收标准：
1) 图数据库里出现新结构：FacetPoint 节点、Facet -[has_point]-> FacetPoint 边、Facet.anchor_text
2) 向量库里出现新 collection：Facet_anchor_text、FacetPoint_search_text
3) 日志里能看到每个 facet 生成了多少 points
"""

import asyncio
import os
import sys

# Set environment variables
os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"
os.environ["MFLOW_EPISODIC_ENABLE_FACET_POINTS"] = "true"
os.environ["LLM_MODEL"] = os.getenv("LLM_MODEL", "gpt-5-nano")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import m_flow
from m_flow.adapters.graph import get_graph_provider
from m_flow.adapters.vector import get_vector_provider


TEST_CONTENT = """
项目名称：智能客服系统

技术方案概述：
- 基础 LLM：GPT-4o-mini，选择原因是成本低且响应快
- 架构：RAG（Retrieval Augmented Generation），使用 Kuzu 图数据库存储知识图谱
- 向量检索：LanceDB 本地向量库，embedding 模型使用 text-embedding-3-small
- 目标响应延迟：< 500ms

项目预算与时间：
- 总预算：150万元人民币
- 人力成本：80万元（4名工程师，6个月）
- 云服务成本：40万元（GPU 算力、存储、API 调用）
- 预计上线时间：2025年3月

预期收益：
- 客户满意度提升 15%
- 人工客服成本降低 30%
- 平均响应时间从 2 分钟降至 30 秒
"""


async def main():
    print("=" * 70)
    print("Stage2 验收测试：FacetPoint 写入 MVP")
    print("=" * 70)

    # 1. 清空数据库
    print("\n[1/4] 清空数据库...")
    try:
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)
        print("  ✅ 数据库已清空")
    except Exception as e:
        print(f"  ⚠️ 清空数据库失败（可能已为空）: {e}")

    # 2. 添加测试数据并 memorize
    print("\n[2/4] 添加测试数据并 memorize...")
    await m_flow.add(TEST_CONTENT, dataset_name="stage2_test")
    await m_flow.memorize(chunk_size=400)
    print("  ✅ memorize 完成")

    # 3. 检查图数据库
    print("\n[3/4] 检查图数据库...")
    graph_engine = await get_graph_provider()

    # 检查 FacetPoint 节点
    facet_point_query = "MATCH (n:Node) WHERE n.type = 'FacetPoint' RETURN n.id, n.name LIMIT 10"
    try:
        facet_point_results = await graph_engine.query(facet_point_query)
        if facet_point_results:
            print(f"  ✅ 找到 {len(facet_point_results)} 个 FacetPoint 节点:")
            for row in facet_point_results[:5]:
                print(f"     - {row[1]}")
        else:
            print("  ⚠️ 没有找到 FacetPoint 节点（可能是因为 facet 数量少或 LLM 未生成 points）")
    except Exception as e:
        print(f"  ❌ 查询 FacetPoint 失败: {e}")

    # 检查 has_point 边
    has_point_query = """
    MATCH (f:Node)-[r:EDGE]->(p:Node)
    WHERE f.type = 'Facet' AND p.type = 'FacetPoint' AND r.relationship_name = 'has_point'
    RETURN f.name, p.name LIMIT 10
    """
    try:
        has_point_results = await graph_engine.query(has_point_query)
        if has_point_results:
            print(f"  ✅ 找到 {len(has_point_results)} 条 has_point 边:")
            for row in has_point_results[:5]:
                print(f"     - Facet: {row[0][:40]}... -> Point: {row[1]}")
        else:
            print("  ⚠️ 没有找到 has_point 边")
    except Exception as e:
        print(f"  ❌ 查询 has_point 边失败: {e}")

    # 检查 Facet.anchor_text
    anchor_text_query = "MATCH (n:Node) WHERE n.type = 'Facet' RETURN n.name, n.properties LIMIT 5"
    try:
        anchor_text_results = await graph_engine.query(anchor_text_query)
        if anchor_text_results:
            has_anchor_text = False
            for row in anchor_text_results:
                props = row[1] if row[1] else {}
                if isinstance(props, str):
                    import json

                    try:
                        props = json.loads(props)
                    except:
                        props = {}
                if props.get("anchor_text"):
                    has_anchor_text = True
                    anchor_val = props.get("anchor_text", "")
                    print("  ✅ Facet 节点有 anchor_text:")
                    print(f"     - {row[0][:40]}... anchor_text: {anchor_val[:60]}...")
                    break
            if not has_anchor_text:
                print("  ⚠️ Facet 节点的 anchor_text 为空（检查 properties 字段）")
        else:
            print("  ⚠️ 没有找到 Facet 节点")
    except Exception as e:
        print(f"  ❌ 查询 Facet.anchor_text 失败: {e}")

    # 4. 检查向量库
    print("\n[4/4] 检查向量库 collections...")
    vector_engine = get_vector_provider()

    expected_collections = [
        "Facet_anchor_text",
        "FacetPoint_search_text",
        "FacetPoint_aliases_text",
    ]

    for coll in expected_collections:
        try:
            # 尝试列出集合（不同的 vector engine 可能有不同的方法）
            exists = await vector_engine.has_collection(coll)
            if exists:
                print(f"  ✅ Collection '{coll}' 存在")
            else:
                print(f"  ⚠️ Collection '{coll}' 不存在（可能是因为该字段为空）")
        except Exception as e:
            print(f"  ⚠️ 检查 collection '{coll}' 失败: {e}")

    # 验收结果
    print("\n" + "=" * 70)
    print("验收结果")
    print("=" * 70)
    print("\n检查完成！请查看上方输出确认：")
    print("  1. FacetPoint 节点和 has_point 边是否创建")
    print("  2. Facet.anchor_text 是否有值")
    print("  3. 向量库 collections 是否创建")
    print("\n如果看到 FacetPoint 节点和 has_point 边，说明 Stage2 基本功能正常。")
    print("如果看到 '没有找到 FacetPoint 节点'，可能是：")
    print("  - facet 数量太少")
    print("  - LLM 输出了空的 points 列表")
    print("  - 可以检查日志中 '[episodic] FacetPoint built' 的输出")


if __name__ == "__main__":
    asyncio.run(main())
