"""
快速检索测试 - 不调用 LLM，直接使用 episodic_triplet_search
"""

import asyncio
import os
import time

os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"

from m_flow.retrieval.utils.episodic_triplet_search import episodic_triplet_search

# 测试查询
TEST_QUERIES = [
    ("智能客服系统用的是什么技术方案？", ["gpt-4o-mini", "rag", "lancedb", "kuzu"]),
    ("技术架构升级有哪些内容？", ["微服务", "postgresql", "redis", "容灾"]),
    ("技术债务有多少？", ["15万行", "测试覆盖", "45%"]),
    ("Q4销售业绩怎么样？", ["1.2亿", "25%", "华东"]),
    ("A系列产品卖得好吗？", ["5000万", "42%", "30%"]),
    ("销售团队有多少人？", ["80人", "150万", "王五"]),
    ("公司年度营收是多少？", ["4.5亿", "28%", "65%"]),
    ("研发投入多少钱？", ["0.8亿", "18%", "1.2亿"]),
    ("公司有多少员工？", ["580人", "20%", "12%"]),
    ("员工福利有哪些？", ["体检", "健身房", "300元"]),
    ("国际化战略是什么？", ["东南亚", "新加坡", "2000万"]),
    ("AI研发中心预算多少？", ["1500万", "800万", "a100"]),
    ("产品规划有哪些？", ["d系列", "800万", "q2"]),
    ("客户满意度怎么样？", ["85分", "nps", "45"]),
    ("双十一活动效果如何？", ["5000万", "roi", "10:1"]),
    ("供应链优化了什么？", ["45天", "32天", "12%"]),
    ("数据安全审计结果？", ["92分", "iso", "等保"]),
    ("新办公室装修预算？", ["600万", "4000平方"]),
    ("招聘情况怎么样？", ["150人", "28天", "85%"]),
    ("现金流状况如何？", ["1.2亿", "2.8亿"]),
]


def extract_triplet_text(triplets) -> str:
    """从 triplets 提取所有文本用于关键词匹配"""
    texts = []
    for edge in triplets:
        # node1
        if edge.node1:
            for key in ["name", "summary", "search_text", "description", "aliases_text"]:
                val = edge.node1.attributes.get(key)
                if val:
                    texts.append(str(val))
        # node2
        if edge.node2:
            for key in ["name", "summary", "search_text", "description", "aliases_text"]:
                val = edge.node2.attributes.get(key)
                if val:
                    texts.append(str(val))
        # edge
        edge_text = edge.attributes.get("edge_text")
        if edge_text:
            texts.append(str(edge_text))

    return " ".join(texts).lower()


async def test_single_query(query: str, keywords: list, top_k: int = 5):
    """测试单个查询"""
    start = time.time()

    triplets = await episodic_triplet_search(query, top_k=top_k)

    elapsed = time.time() - start

    # 提取文本
    combined = extract_triplet_text(triplets)

    # 关键词匹配
    matched = [kw for kw in keywords if kw.lower() in combined]
    missed = [kw for kw in keywords if kw.lower() not in combined]

    match_rate = len(matched) / len(keywords) if keywords else 0
    success = match_rate >= 0.5

    return {
        "query": query,
        "success": success,
        "match_rate": match_rate,
        "matched": matched,
        "missed": missed,
        "triplet_count": len(triplets),
        "elapsed": elapsed,
        "preview": combined[:150] if combined else "(empty)",
    }


async def main():
    print("=" * 70)
    print("快速检索测试 - 直接 triplet search（无 LLM）")
    print("=" * 70)

    total = len(TEST_QUERIES)
    success_count = 0
    total_time = 0

    for i, (query, keywords) in enumerate(TEST_QUERIES, 1):
        result = await test_single_query(query, keywords)
        total_time += result["elapsed"]

        if result["success"]:
            success_count += 1
            status = "✅"
        else:
            status = "❌"

        print(f"\n[{i}/{total}] {query}")
        print(
            f"   {status} {result['elapsed']:.2f}s | {result['triplet_count']} triplets | 匹配 {len(result['matched'])}/{len(keywords)}"
        )
        print(f"   匹配: {result['matched']}")
        if result["missed"]:
            print(f"   缺失: {result['missed']}")
        print(f"   预览: {result['preview'][:100]}...")

    print("\n" + "=" * 70)
    print(f"测试结果: {success_count}/{total} 成功 ({success_count / total * 100:.0f}%)")
    print(f"总耗时: {total_time:.1f}s | 平均: {total_time / total:.2f}s/查询")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
