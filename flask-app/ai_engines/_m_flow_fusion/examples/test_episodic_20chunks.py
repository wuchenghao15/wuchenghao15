#!/usr/bin/env python3
"""
测试脚本：写入20个chunk并验证episodic memory

运行方式：
    cd m_flow-main
    uv run python examples/test_episodic_20chunks.py          # 默认不重置
    uv run python examples/test_episodic_20chunks.py --reset  # 重置数据库
"""

import asyncio
import os
import sys

# 确保启用 episodic
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"

import m_flow


# 准备测试数据：一个完整的项目报告，会被分割成多个chunk
TEST_DOCUMENT = """
# 智能客服系统升级项目报告

## 一、项目背景

随着公司业务规模的快速扩张，现有客服系统已无法满足日益增长的用户咨询需求。2024年Q3客服工单量达到日均5万件，较去年同期增长180%。人工客服团队规模已扩展至200人，但客户等待时长仍高达平均8分钟，客户满意度下降至72%。

经过多方调研和技术评估，公司决定引入基于大语言模型的智能客服系统，以提升服务效率和用户体验。本项目于2024年10月正式启动，计划于2025年3月完成全面部署。

## 二、技术方案选型

### 2.1 LLM模型选择

经过对比测试，我们最终选择了GPT-4o-mini作为基础模型，主要考虑因素包括：
- 响应速度：平均延迟低于500ms
- 成本效益：相比GPT-4，成本降低80%
- 中文能力：在客服场景测试中准确率达到94%
- 安全性：支持内容过滤和敏感词检测

备选方案包括Claude-3-Sonnet和文心一言4.0，但在综合评估后未被采纳。

### 2.2 向量数据库方案

选择LanceDB作为向量存储方案，理由如下：
- 本地部署，无需额外运维成本
- 支持快速增量更新
- 与现有Python技术栈兼容良好
- 查询性能满足业务需求（p99 < 100ms）

### 2.3 知识图谱方案

采用Kuzu作为图数据库，用于存储实体关系和业务逻辑：
- 开源免费，社区活跃
- 支持Cypher查询语法
- 内存占用低，适合边缘部署

## 三、系统架构设计

### 3.1 整体架构

系统采用微服务架构，主要包含以下模块：
1. 接入网关：负责多渠道接入（网页、APP、微信）
2. 对话引擎：基于LLM的对话管理
3. 知识库服务：文档检索和知识抽取
4. 工单系统：人工接管和工单流转
5. 数据分析：对话日志和用户画像

### 3.2 关键技术决策

**决策1**：采用RAG（检索增强生成）而非纯LLM方案
- 优点：知识可控、可更新、可追溯
- 风险：检索准确率直接影响回答质量

**决策2**：实现人机协作模式
- 复杂问题自动转人工
- 人工回答反馈用于模型优化
- 预计可减少人工介入率至30%

**决策3**：分阶段灰度发布
- Phase 1：内部测试（11月）
- Phase 2：10%用户灰度（12月）
- Phase 3：全量发布（2025年3月）

## 四、项目进展与里程碑

### 4.1 已完成工作（截至2024年12月）

1. **基础设施搭建**（100%完成）
   - Kubernetes集群部署
   - CI/CD流水线配置
   - 监控告警系统上线

2. **知识库构建**（85%完成）
   - 导入历史FAQ 5000条
   - 产品文档结构化处理
   - 向量索引优化

3. **对话引擎开发**（70%完成）
   - 多轮对话管理
   - 意图识别模块
   - 实体抽取模块

### 4.2 待完成工作

1. **工单系统对接**（预计1月完成）
   - 人工接管触发逻辑
   - 工单自动分类
   - SLA监控

2. **数据分析平台**（预计2月完成）
   - 对话质量评估
   - 用户满意度追踪
   - 成本效益分析

## 五、风险评估与应对

### 5.1 技术风险

**风险1**：LLM幻觉问题
- 影响：可能提供错误信息
- 应对：强化检索校验，增加置信度阈值

**风险2**：高并发性能瓶颈
- 影响：响应延迟增加
- 应对：引入请求队列，实现自动扩缩容

**风险3**：数据安全隐患
- 影响：用户隐私泄露
- 应对：敏感信息脱敏，日志审计

### 5.2 业务风险

**风险4**：用户接受度低
- 影响：满意度下降
- 应对：保留一键转人工，优化交互体验

**风险5**：知识库更新滞后
- 影响：回答过时
- 应对：建立知识更新机制，定期review

## 六、成本与收益分析

### 6.1 投资成本

| 项目 | 成本（万元） |
|------|-------------|
| LLM API费用（年） | 120 |
| 基础设施 | 80 |
| 开发人力 | 200 |
| 运维成本（年） | 50 |
| **合计** | **450** |

### 6.2 预期收益

- 人工客服成本节省：预计年省200万
- 客户等待时长：从8分钟降至1分钟
- 客户满意度：预计提升至85%
- 7x24小时服务能力
- ROI：预计18个月回本

## 七、下一步计划

1. **2025年1月**
   - 完成工单系统对接
   - 启动内部测试
   - 收集反馈优化

2. **2025年2月**
   - 10%用户灰度
   - 性能压测
   - 安全审计

3. **2025年3月**
   - 全量发布
   - 运营监控
   - 持续优化

## 八、总结

智能客服系统升级项目进展顺利，技术方案已验证可行，核心功能开发完成度达70%。项目团队将继续按计划推进，确保2025年Q1完成全面上线。

项目负责人：张三
报告日期：2024年12月20日
"""


async def main():
    # 检查命令行参数
    should_reset = "--reset" in sys.argv

    print("=" * 60)
    print("测试 Episodic Memory：写入20个chunks")
    print("=" * 60)

    # 1. 重置数据库（可选）
    if should_reset:
        print("\n[1] 重置数据库...")
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)
        print("  ✓ 数据库已重置")
    else:
        print("\n[1] 跳过数据库重置（使用 --reset 参数可重置）")

    # 2. 添加文档
    print("\n[2] 添加测试文档...")
    await m_flow.add(TEST_DOCUMENT, dataset_name="customer_service_project")
    print("  ✓ 文档已添加")

    # 3. 运行 memorize（包含 episodic 写入）
    print("\n[3] 运行 memorize（包含 episodic 写入）...")
    print("  这将触发：")
    print("    - 文档分块 (chunking) - 使用 chunk_size=200")
    print("    - 实体抽取 (entity extraction)")
    print("    - 文本摘要 (summarization)")
    print("    - Episodic Memory 写入")
    print("  请稍候，这可能需要1-2分钟...")

    try:
        await m_flow.memorize(chunk_size=200)
        print("  ✓ memorize 完成！")
    except Exception as e:
        print(f"  ✗ memorize 出错: {e}")
        import traceback

        traceback.print_exc()
        return

    # 4. 验证写入结果
    print("\n[4] 验证写入结果...")

    # 检查图数据库中的节点
    from m_flow.adapters.graph import get_graph_provider

    graph_engine = await get_graph_provider()

    # 查询 Episode 节点
    try:
        episode_query = """
            MATCH (n:Node)
            WHERE n.type = 'Episode'
            RETURN n.id, n.name, n.properties
        """
        episodes = await graph_engine.query(episode_query)
        print(f"\n  Episodes 数量: {len(episodes)}")
        for ep in episodes[:3]:  # 只显示前3个
            print(f"    - {ep[1]}")
    except Exception as e:
        print(f"  查询 Episode 失败: {e}")

    # 查询 Facet 节点
    try:
        facet_query = """
            MATCH (n:Node)
            WHERE n.type = 'Facet'
            RETURN n.id, n.name, n.properties
        """
        facets = await graph_engine.query(facet_query)
        print(f"\n  Facets 数量: {len(facets)}")
        for f in facets[:5]:  # 只显示前5个
            print(f"    - {f[1]}")

        # 显示 Facet Descriptions
        print("\n  === Facet Descriptions (凝练版) ===")
        import json as json_mod

        for f in facets:
            name = f[1] if f[1] else "N/A"
            props_str = f[2] if len(f) > 2 else "{}"
            try:
                props = json_mod.loads(props_str) if isinstance(props_str, str) else props_str
            except:
                props = {}
            desc = props.get("description", "N/A") if isinstance(props, dict) else "N/A"
            desc_len = len(str(desc)) if desc else 0
            print(f"\n  📌 {name}")
            print(f"     描述: {desc}")
            print(f"     字数: {desc_len}")
    except Exception as e:
        print(f"  查询 Facet 失败: {e}")

    # 查询 ContentFragment 节点
    try:
        chunk_query = """
            MATCH (n:Node)
            WHERE n.type = 'ContentFragment'
            RETURN count(n)
        """
        chunks = await graph_engine.query(chunk_query)
        chunk_count = chunks[0][0] if chunks else 0
        print(f"\n  ContentFragments 数量: {chunk_count}")
    except Exception as e:
        print(f"  查询 ContentFragment 失败: {e}")

    # 5. 测试 Episodic 检索精度
    print("\n[5] 测试 Episodic 检索精度...")

    from m_flow.retrieval.utils.episodic_triplet_search import episodic_triplet_search

    test_cases = [
        {
            "query": "这个项目的技术方案是什么？",
            "expected": ["GPT-4o-mini", "LanceDB", "Kuzu", "RAG", "LLM"],
        },
        {
            "query": "有哪些风险和应对措施？",
            "expected": ["风险", "幻觉", "并发", "安全", "应对"],
        },
        {
            "query": "项目的成本和收益如何？",
            "expected": ["成本", "收益", "ROI", "节省", "万元"],
        },
    ]

    for test in test_cases:
        query = test["query"]
        expected = test["expected"]

        print(f"\n  Query: {query}")
        print(f"  期望关键词: {expected}")

        try:
            triplets = await episodic_triplet_search(query=query, top_k=5)

            if not triplets:
                print("    ⚠ 无结果")
                continue

            print(f"    ✓ 返回 {len(triplets)} 个 triplets:")

            for rank, edge in enumerate(triplets, 1):
                n1 = edge.node1
                n2 = edge.node2

                n1_type = n1.attributes.get("type", "?")
                n1_name = n1.attributes.get("name", "?")[:30]
                n2_type = n2.attributes.get("type", "?")
                n2_name = n2.attributes.get("name", "?")[:40]
                rel_type = edge.attributes.get("relationship_type") or edge.attributes.get("relationship_name", "?")

                # 分数
                n1_dist = n1.attributes.get("vector_distance", 1.0)
                n2_dist = n2.attributes.get("vector_distance", 1.0)
                e_dist = edge.attributes.get("vector_distance", 1.0)
                total = n1_dist + n2_dist + e_dist

                # 关键词匹配
                all_text = (
                    f"{n1_name} {n2_name} {n2.attributes.get('search_text', '')} {n2.attributes.get('description', '')}"
                )
                matched = [k for k in expected if k.lower() in all_text.lower()]

                marker = "🎯" if len(matched) >= 2 else "✓" if matched else "○"
                print(f"      {marker} Rank {rank}: [{n1_type}] --[{rel_type}]--> [{n2_type}] {n2_name}")
                print(f"         分数: {total:.3f} | 匹配: {matched if matched else '无'}")

        except Exception as e:
            print(f"    ✗ 检索失败: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
