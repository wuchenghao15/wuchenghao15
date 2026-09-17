"""
全面检索测试 - 15个事件记忆库
"""

import asyncio
import os

os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"

import m_flow
from m_flow.search.types import RecallMode

# 测试查询列表 - 覆盖各类事件和问题类型
TEST_QUERIES = [
    # 技术相关
    ("智能客服系统用的是什么技术方案？", ["GPT-4o-mini", "RAG", "LanceDB", "Kuzu"]),
    ("技术架构升级有哪些内容？", ["微服务", "PostgreSQL", "Redis", "容灾"]),
    ("技术债务有多少？怎么清理？", ["15万行", "测试覆盖", "45%", "Sprint"]),
    # 销售相关
    ("Q4销售业绩怎么样？", ["1.2亿", "25%", "华东", "华南"]),
    ("A系列产品卖得好吗？", ["5000万", "42%", "30%"]),
    ("销售团队有多少人？", ["80人", "150万", "王五"]),
    # 财务相关
    ("公司年度营收是多少？", ["4.5亿", "28%", "65%"]),
    ("研发投入多少钱？", ["0.8亿", "18%", "1.2亿"]),
    ("现金流状况如何？", ["1.2亿", "2.8亿"]),
    # HR相关
    ("公司有多少员工？", ["580人", "20%", "12%"]),
    ("员工福利有哪些？", ["体检", "健身房", "300元", "育儿假"]),
    ("招聘情况怎么样？", ["150人", "28天", "85%"]),
    # 战略相关
    ("国际化战略是什么？", ["东南亚", "新加坡", "2000万美元", "30%"]),
    ("AI研发中心预算多少？", ["1500万", "800万", "A100", "15人"]),
    ("产品规划有哪些？", ["D系列", "800万", "Q2", "微服务"]),
    # 运营相关
    ("客户满意度怎么样？", ["85分", "NPS", "45", "88分"]),
    ("双十一活动效果如何？", ["5000万", "ROI", "10:1", "抖音"]),
    ("供应链优化了什么？", ["45天", "32天", "60家", "12%"]),
    # 安全合规
    ("数据安全审计结果？", ["92分", "ISO 27001", "等保三级", "中危"]),
    # 行政
    ("新办公室装修预算？", ["600万", "4000平方米", "智能化"]),
]


async def test_single_query(query: str, expected_keywords: list, top_k: int = 5):
    """测试单个查询"""
    try:
        results = await m_flow.search(query_type=RecallMode.EPISODIC, query_text=query, top_k=top_k)

        # 收集结果文本 - 结果可能是字符串列表
        result_texts = []
        for r in results:
            if isinstance(r, str):
                result_texts.append(r)
            elif isinstance(r, dict):
                # dict-like
                for key in ["node_2", "edge", "node_1", "text", "content", "description"]:
                    val = r.get(key)
                    if isinstance(val, dict):
                        for field in ["search_text", "summary", "edge_text", "description", "name", "text"]:
                            fval = val.get(field, "")
                            if fval:
                                result_texts.append(str(fval))
                    elif val:
                        result_texts.append(str(val))
            elif hasattr(r, "__dict__"):
                for val in r.__dict__.values():
                    if val:
                        result_texts.append(str(val))

        combined_text = " ".join(result_texts).lower()

        # 检查关键词匹配
        matched = []
        missed = []
        for kw in expected_keywords:
            if kw.lower() in combined_text:
                matched.append(kw)
            else:
                missed.append(kw)

        match_rate = len(matched) / len(expected_keywords) if expected_keywords else 0

        return {
            "query": query,
            "success": match_rate >= 0.5,  # 50%以上关键词匹配视为成功
            "match_rate": match_rate,
            "matched": matched,
            "missed": missed,
            "result_count": len(results),
            "results": results[:3],  # 保留前3个结果供查看
            "combined_text": combined_text[:300],  # 用于调试
        }

    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "match_rate": 0,
            "matched": [],
            "missed": expected_keywords,
            "result_count": 0,
            "results": [],
            "combined_text": "",
        }


async def main():
    print("=" * 70)
    print("全面检索测试 - 15个事件记忆库")
    print("=" * 70)

    total = len(TEST_QUERIES)
    success_count = 0
    results_summary = []

    for i, (query, keywords) in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{total}] 查询: {query}")
        print(f"       预期关键词: {keywords}")

        result = await test_single_query(query, keywords)
        results_summary.append(result)

        if result["success"]:
            success_count += 1
            status = "✅ 成功"
        else:
            status = "❌ 失败"

        print(f"       {status} | 匹配率: {result['match_rate'] * 100:.0f}%")
        print(f"       匹配: {result['matched']}")
        if result["missed"]:
            print(f"       缺失: {result['missed']}")

        # 显示结果预览
        if result.get("combined_text"):
            preview = result["combined_text"][:150].replace("\n", " ")
            print(f"       预览: {preview}...")

    # 总结
    print("\n" + "=" * 70)
    print("测试结果总结")
    print("=" * 70)
    print(f"总查询数: {total}")
    print(f"成功数量: {success_count}")
    print(f"成功率: {success_count / total * 100:.1f}%")

    # 列出失败的查询
    failed = [r for r in results_summary if not r["success"]]
    if failed:
        print(f"\n失败的查询 ({len(failed)}个):")
        for r in failed:
            print(f"  - {r['query']}")
            print(f"    匹配率: {r['match_rate'] * 100:.0f}%, 缺失: {r['missed']}")

    # 按类别统计
    print("\n按类别统计:")
    categories = [
        ("技术", [0, 1, 2]),
        ("销售", [3, 4, 5]),
        ("财务", [6, 7, 8]),
        ("HR", [9, 10, 11]),
        ("战略", [12, 13, 14]),
        ("运营", [15, 16, 17]),
        ("安全", [18]),
        ("行政", [19]),
    ]

    for cat_name, indices in categories:
        cat_results = [results_summary[i] for i in indices if i < len(results_summary)]
        cat_success = sum(1 for r in cat_results if r["success"])
        print(f"  {cat_name}: {cat_success}/{len(cat_results)} 成功")


if __name__ == "__main__":
    asyncio.run(main())
