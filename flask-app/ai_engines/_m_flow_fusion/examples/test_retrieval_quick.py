"""
快速检索测试 - 减少查询数量
"""

import asyncio
import os
import time

os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"

import m_flow
from m_flow.search.types import RecallMode

# 精简的测试查询 - 每个类别选1个代表性查询
TEST_QUERIES = [
    ("智能客服系统用的是什么技术方案？", ["gpt-4o-mini", "rag", "lancedb", "kuzu"]),
    ("Q4销售业绩怎么样？", ["1.2亿", "25%"]),
    ("公司年度营收是多少？", ["4.5亿", "28%"]),
    ("员工福利有哪些？", ["体检", "健身房"]),
    ("AI研发中心预算多少？", ["1500万", "a100"]),
    ("客户满意度怎么样？", ["85分", "nps"]),
    ("数据安全审计结果？", ["92分", "iso"]),
    ("新办公室装修预算？", ["600万"]),
]


async def main():
    print("=" * 60)
    print("快速检索测试 (8个查询)")
    print("=" * 60)

    total = len(TEST_QUERIES)
    success_count = 0

    for i, (query, keywords) in enumerate(TEST_QUERIES, 1):
        start = time.time()
        print(f"\n[{i}/{total}] {query}")

        try:
            results = await m_flow.search(query_type=RecallMode.EPISODIC, query_text=query, top_k=3)

            elapsed = time.time() - start

            # 结果是字符串列表
            combined = " ".join(str(r) for r in results).lower()

            # 检查关键词
            matched = [kw for kw in keywords if kw.lower() in combined]
            missed = [kw for kw in keywords if kw.lower() not in combined]

            match_rate = len(matched) / len(keywords) if keywords else 0
            success = match_rate >= 0.5

            if success:
                success_count += 1
                status = "✅"
            else:
                status = "❌"

            print(f"   {status} {elapsed:.1f}s | 匹配 {len(matched)}/{len(keywords)}: {matched}")
            if missed:
                print(f"      缺失: {missed}")

            # 显示结果预览
            preview = combined[:120].replace("\n", " ")
            print(f"      预览: {preview}...")

        except Exception as e:
            print(f"   ❌ 错误: {e}")

    print("\n" + "=" * 60)
    print(f"结果: {success_count}/{total} 成功 ({success_count / total * 100:.0f}%)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
