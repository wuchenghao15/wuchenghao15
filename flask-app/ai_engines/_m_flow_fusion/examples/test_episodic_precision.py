#!/usr/bin/env python3
"""
Episodic Memory 检索精度测试

测试检索结果的排名和相关性，展示 top-k 结果的详细信息。

运行方式：
    cd m_flow-main
    uv run python examples/test_episodic_precision.py
"""

import asyncio
import os

# 确保启用 episodic
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"

from m_flow.retrieval.utils.episodic_triplet_search import episodic_triplet_search


# 测试查询和预期答案
TEST_QUERIES = [
    {
        "query": "这个项目的技术方案是什么？",
        "expected_keywords": ["GPT-4o-mini", "LanceDB", "Kuzu", "RAG", "LLM", "向量"],
        "description": "技术方案查询 - 期望找到模型选择、数据库选择等信息",
    },
    {
        "query": "有哪些风险和应对措施？",
        "expected_keywords": ["风险", "幻觉", "并发", "安全", "应对", "隐患"],
        "description": "风险查询 - 期望找到技术风险和业务风险",
    },
    {
        "query": "项目的成本和收益如何？",
        "expected_keywords": ["成本", "收益", "ROI", "节省", "万元", "投资"],
        "description": "成本收益查询 - 期望找到投资和回报信息",
    },
    {
        "query": "项目的时间计划是什么？",
        "expected_keywords": ["2024", "2025", "灰度", "上线", "阶段", "月"],
        "description": "时间计划查询 - 期望找到里程碑和时间线",
    },
    {
        "query": "客服系统的性能指标？",
        "expected_keywords": ["延迟", "满意度", "等待", "分钟", "响应", "%"],
        "description": "性能指标查询 - 期望找到KPI和指标数据",
    },
]


def calculate_keyword_match(text: str, keywords: list) -> tuple:
    """计算关键词匹配度"""
    text_lower = text.lower()
    matched = [k for k in keywords if k.lower() in text_lower]
    return len(matched), len(keywords), matched


async def test_retrieval_precision():
    """测试检索精度"""
    print("=" * 80)
    print("Episodic Memory 检索精度测试")
    print("=" * 80)

    for i, test_case in enumerate(TEST_QUERIES, 1):
        query = test_case["query"]
        expected = test_case["expected_keywords"]
        desc = test_case["description"]

        print(f"\n{'=' * 80}")
        print(f"[Query {i}] {query}")
        print(f"描述: {desc}")
        print(f"期望关键词: {expected}")
        print("-" * 80)

        try:
            # 获取 top-10 结果
            triplets = await episodic_triplet_search(
                query=query,
                top_k=10,
                wide_search_top_k=100,
            )

            if not triplets:
                print("  ⚠ 无检索结果")
                continue

            print(f"\n  返回 {len(triplets)} 个 triplets:\n")

            best_rank = None
            best_match_count = 0

            for rank, edge in enumerate(triplets, 1):
                # 提取节点和边信息
                node1 = edge.node1
                node2 = edge.node2

                n1_type = node1.attributes.get("type", "?")
                n1_name = node1.attributes.get("name", "?")
                n1_summary = node1.attributes.get("summary", "")[:100] if node1.attributes.get("summary") else ""
                n1_search_text = node1.attributes.get("search_text", "")

                n2_type = node2.attributes.get("type", "?")
                n2_name = node2.attributes.get("name", "?")
                n2_summary = node2.attributes.get("summary", "")[:100] if node2.attributes.get("summary") else ""
                n2_search_text = node2.attributes.get("search_text", "")
                n2_desc = node2.attributes.get("description", "")[:100] if node2.attributes.get("description") else ""

                rel_type = edge.attributes.get("relationship_type") or edge.attributes.get("relationship_name", "?")
                edge_text = edge.attributes.get("edge_text", "")[:150] if edge.attributes.get("edge_text") else ""

                # 计算分数
                n1_dist = node1.attributes.get("vector_distance", 1.0)
                n2_dist = node2.attributes.get("vector_distance", 1.0)
                e_dist = edge.attributes.get("vector_distance", 1.0)
                total_score = n1_dist + n2_dist + e_dist

                # 组合所有文本用于关键词匹配
                all_text = f"{n1_name} {n1_summary} {n1_search_text} {n2_name} {n2_summary} {n2_search_text} {n2_desc} {edge_text}"
                match_count, total_keywords, matched = calculate_keyword_match(all_text, expected)

                # 记录最佳匹配
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_rank = rank

                # 显示 triplet 信息
                relevance = "🎯" if match_count >= 2 else "✓" if match_count >= 1 else "○"
                print(f"  {relevance} Rank {rank}: [{n1_type}] {n1_name[:30]}")
                print(f"              --[{rel_type}]-->")
                print(f"              [{n2_type}] {n2_name[:40]}")
                print(f"     分数: {total_score:.4f} (n1={n1_dist:.3f}, n2={n2_dist:.3f}, e={e_dist:.3f})")
                print(f"     匹配: {match_count}/{total_keywords} 关键词 {matched}")

                if n2_search_text:
                    print(f"     search_text: {n2_search_text[:60]}")
                if edge_text:
                    print(f"     edge_text: {edge_text[:80]}...")
                print()

            # 汇总
            print("-" * 40)
            if best_rank:
                print(f"  📊 最佳匹配: Rank {best_rank} ({best_match_count}/{len(expected)} 关键词)")
                if best_rank == 1:
                    print("  ✅ 精度评估: 最相关结果排在 Top 1")
                elif best_rank <= 3:
                    print("  ✅ 精度评估: 最相关结果排在 Top 3")
                elif best_rank <= 5:
                    print("  ⚠ 精度评估: 最相关结果排在 Top 5")
                else:
                    print(f"  ❌ 精度评估: 最相关结果排在 Top {best_rank}")
            else:
                print("  ❌ 未找到匹配关键词的结果")

        except Exception as e:
            print(f"  ✗ 检索失败: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("检索精度测试完成")
    print("=" * 80)


async def ensure_data_exists():
    """确保数据已写入"""
    from m_flow.adapters.graph import get_graph_provider

    graph_engine = await get_graph_provider()

    try:
        episode_query = """
            MATCH (n:Node)
            WHERE n.type = 'Episode'
            RETURN count(n)
        """
        result = await graph_engine.query(episode_query)
        count = result[0][0] if result else 0

        if count == 0:
            print("⚠ 数据库中没有 Episode，请先运行：")
            print("   uv run python examples/test_episodic_20chunks.py")
            return False

        print(f"✓ 数据库中有 {count} 个 Episode")
        return True
    except Exception as e:
        print(f"✗ 检查数据失败: {e}")
        return False


async def main():
    print("\n检查数据库状态...")
    if not await ensure_data_exists():
        return

    await test_retrieval_precision()


if __name__ == "__main__":
    asyncio.run(main())
