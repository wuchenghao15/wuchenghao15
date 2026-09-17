#!/usr/bin/env python3
"""
Test LLM-driven Episode Router

Tests:
1. First document -> CREATE_NEW
2. Related follow-up document -> MERGE_TO_EXISTING
3. Unrelated document -> CREATE_NEW
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Environment setup
os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"
os.environ["MFLOW_EPISODIC_ENABLE_ROUTING"] = "true"
os.environ["MFLOW_EPISODIC_ROUTING_USE_LLM"] = "true"
os.environ["LLM_MODEL"] = os.getenv("LLM_MODEL", "gpt-5-nano")

import m_flow
from m_flow.adapters.graph import get_graph_provider


async def clear_database():
    """Clear all data."""
    print("\n[1] Clearing database...")
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    print("Database cleared.")


async def add_document(title: str, content: str):
    """Add a single document and memorize."""
    print(f"\n[ADD] {title[:50]}...")
    await m_flow.add(
        data=content,
        dataset_name=title.replace(" ", "_")[:30],
    )
    await m_flow.memorize()
    print(f"[ADD] Done: {title[:50]}")


async def count_episodes():
    """Count episodes in graph."""
    graph_engine = await get_graph_provider()
    try:
        result = await graph_engine.query("MATCH (n:Node) WHERE n.type = 'Episode' RETURN count(n)")
        return result[0][0] if result else 0
    except Exception as e:
        print(f"Error counting episodes: {e}")
        return -1


async def run_test():
    """Run the LLM router test."""
    await clear_database()

    # Document 1: Initial project document
    doc1_title = "智能客服系统技术方案"
    doc1_content = """
    项目名称：智能客服系统
    项目负责人：张明
    技术方案：
    - 使用 GPT-4o-mini 作为基础 LLM
    - 采用 RAG 架构进行知识检索
    - 预计响应延迟 < 500ms
    - 项目预算：150万元
    - 预计上线时间：2025年3月
    """

    # Document 2: Follow-up document (should MERGE)
    doc2_title = "智能客服系统进度更新"
    doc2_content = """
    项目名称：智能客服系统
    更新日期：2025年1月20日
    项目负责人：张明
    进度更新：
    - RAG 检索模块已完成 80%
    - GPT-4o-mini 集成测试通过
    - 响应延迟实测 450ms，符合预期
    - 预算已使用 60%
    - 计划下周进行用户测试
    """

    # Document 3: Unrelated document (should CREATE_NEW)
    doc3_title = "2024年度财务报告"
    doc3_content = """
    公司名称：科技有限公司
    财务年度：2024年
    营业收入：5.2亿元
    净利润：8000万元
    员工人数：500人
    研发投入占比：15%
    未来规划：扩展海外市场
    """

    print("\n" + "=" * 70)
    print("TEST 1: First document (should create new episode)")
    print("=" * 70)
    await add_document(doc1_title, doc1_content)
    count1 = await count_episodes()
    print(f"Episodes after doc1: {count1}")

    print("\n" + "=" * 70)
    print("TEST 2: Related follow-up (should merge into existing)")
    print("=" * 70)
    await add_document(doc2_title, doc2_content)
    count2 = await count_episodes()
    print(f"Episodes after doc2: {count2}")

    print("\n" + "=" * 70)
    print("TEST 3: Unrelated document (should create new episode)")
    print("=" * 70)
    await add_document(doc3_title, doc3_content)
    count3 = await count_episodes()
    print(f"Episodes after doc3: {count3}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Episode count: {count1} -> {count2} -> {count3}")

    if count1 == 1 and count2 == 1 and count3 == 2:
        print("✅ SUCCESS: LLM router correctly merged related doc and created new for unrelated")
    elif count2 == 1:
        print("⚠️ PARTIAL: Related doc merged correctly, but unrelated doc behavior unexpected")
    else:
        print("❌ NEEDS REVIEW: Check logs for router decisions")

    # Print episode details
    print("\n" + "=" * 70)
    print("EPISODE DETAILS")
    print("=" * 70)
    graph_engine = await get_graph_provider()
    try:
        result = await graph_engine.query("MATCH (n:Node) WHERE n.type = 'Episode' RETURN n.id, n.name, n.properties")
        for row in result:
            ep_id, ep_name, props = row
            summary = ""
            if isinstance(props, dict):
                summary = props.get("summary", "")[:150]
            print(f"\nEpisode: {ep_name}")
            print(f"  ID: {ep_id[:30]}...")
            print(f"  Summary: {summary}...")
    except Exception as e:
        print(f"Error fetching episodes: {e}")


if __name__ == "__main__":
    asyncio.run(run_test())
