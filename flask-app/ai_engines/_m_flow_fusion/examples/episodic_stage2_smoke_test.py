"""
Stage 2 Smoke Test: 验证 write_episodic_memories 任务

这个测试使用 MOCK_EPISODIC=true 模式，不需要 LLM API。
验证 write_episodic_memories 能正确生成 Episode、Facet 和富语义边。

运行方式：
    cd m_flow-main
    MOCK_EPISODIC=true uv run python examples/episodic_stage2_smoke_test.py

期望输出：
- 原始 summaries 被保留
- 新增 MemorySpace (Episodic)
- 新增 Episode（带 has_facet / involves_entity 关系）
- Episode 的 memory_spaces 指向 Episodic MemorySpace
"""

import asyncio
import os

# 设置 MOCK 模式
os.environ["MOCK_EPISODIC"] = "true"

from uuid import uuid4

from m_flow.core import MemoryNode
from m_flow.core.domain.models import Entity
from m_flow.core.domain.models.graph_scope import MemorySpace
from m_flow.core.domain.models import Episode, Facet
from m_flow.ingestion.chunking.models.ContentFragment import ContentFragment
from m_flow.data.processing.document_types import Document
from m_flow.knowledge.summarization.models import FragmentDigest
from m_flow.memory.episodic import write_episodic_memories
from m_flow.knowledge.graph_ops.utils.extract_graph import extract_graph


async def main():
    print("=" * 60)
    print("Stage 2 Smoke Test: write_episodic_memories 验证")
    print("=" * 60)

    # 1. 创建 Mock 数据
    doc = Document(
        id=uuid4(),
        name="Q3 促销策略分析报告.txt",
        processed_path="memory://test",
        external_metadata=None,
        mime_type="text/plain",
    )
    print(f"\n✓ 创建 Document: {doc.name} (id={doc.id})")

    # 创建一些 Entity
    entity1 = Entity(name="促销", description="促销活动")
    entity2 = Entity(name="毛利", description="毛利率指标")
    print(f"✓ 创建 Entity: {entity1.name}, {entity2.name}")

    # 创建 ContentFragment，包含 Entity
    chunk1 = ContentFragment(
        id=uuid4(),
        text="Q3 我们采取了促销策略，包括满减和会员券叠加。",
        chunk_size=50,
        chunk_index=0,
        cut_type="paragraph",
        is_part_of=doc,
        contains=[entity1],  # 直接包含 Entity
    )

    chunk2 = ContentFragment(
        id=uuid4(),
        text="促销带来销量提升，但毛利下降约 2pct。",
        chunk_size=40,
        chunk_index=1,
        cut_type="paragraph",
        is_part_of=doc,
        contains=[entity1, entity2],
    )
    print("✓ 创建 ContentFragment x2")

    # 创建 FragmentDigest
    summary1 = FragmentDigest(
        id=uuid4(),
        text="Q3 采取促销策略，包括满减和会员券叠加。",
        made_from=chunk1,
    )

    summary2 = FragmentDigest(
        id=uuid4(),
        text="促销带来销量提升但毛利下降约 2pct。",
        made_from=chunk2,
    )
    print("✓ 创建 FragmentDigest x2")

    # 2. 调用 write_episodic_memories
    print("\n" + "-" * 60)
    print("调用 write_episodic_memories()...")
    print("-" * 60)

    result = await write_episodic_memories([summary1, summary2])

    # 3. 分析结果
    print(f"\n返回 {len(result)} 个 MemoryNodes:")

    summaries_count = 0
    nodesets_count = 0
    episodes_count = 0
    facets_count = 0
    other_count = 0

    episode_obj = None

    for item in result:
        item_type = type(item).__name__
        if item_type == "FragmentDigest":
            summaries_count += 1
        elif item_type == "MemorySpace":
            nodesets_count += 1
            print(f"  [MemorySpace] name={item.name}")
        elif item_type == "Episode":
            episodes_count += 1
            episode_obj = item
            print(f"  [Episode] name={item.name}")
            print(f"    summary: {item.summary[:80]}..." if len(item.summary) > 80 else f"    summary: {item.summary}")
            print(f"    signature: {item.signature}")
            print(f"    has_facet: {len(item.has_facet) if item.has_facet else 0} facets")
            print(f"    involves_entity: {len(item.involves_entity) if item.involves_entity else 0} entities")
            if item.memory_spaces:
                print(f"    memory_spaces: {[ns.name for ns in item.memory_spaces]}")
        elif item_type == "Facet":
            facets_count += 1
        else:
            other_count += 1
            print(f"  [{item_type}] id={item.id}")

    print("\n统计:")
    print(f"  FragmentDigest: {summaries_count} (应为 2)")
    print(f"  MemorySpace: {nodesets_count} (应为 1)")
    print(f"  Episode: {episodes_count} (应为 1)")

    # 4. 验证 Episode 的图结构
    if episode_obj:
        print("\n" + "-" * 60)
        print("验证 Episode 的图结构...")
        print("-" * 60)

        nodes, edges = await extract_graph(
            episode_obj,
            added_nodes={},
            added_edges={},
            visited_properties={},
            include_root=True,
        )

        print(f"\n=== NODES ({len(nodes)}) ===")
        for n in nodes:
            node_type = type(n).__name__
            node_name = getattr(n, "name", "N/A")
            print(f"  [{node_type}] {node_name}")

        print(f"\n=== EDGES ({len(edges)}) ===")
        edge_types = set()
        for e in edges:
            src, dst, rel, props = e
            edge_types.add(rel)
            edge_text = props.get("edge_text", "N/A")
            if edge_text and len(edge_text) > 60:
                edge_text = edge_text[:57] + "..."
            print(f"  {rel}: edge_text={edge_text}")

        # 验证
        print("\n" + "=" * 60)
        print("验证结果")
        print("=" * 60)

        # 检查 Episode 是否有正确的关系
        has_involves_entity = "involves_entity" in edge_types
        has_memory_spaces = "memory_spaces" in edge_types

        print("\n边类型检查:")
        print(f"  involves_entity: {'✅' if has_involves_entity else '❌'}")
        print(f"  memory_spaces: {'✅' if has_memory_spaces else '❌'}")

        # 检查 Entity 是否也 memory_spaces（Stage 3.0 关键修正）
        entity_in_nodes = any(type(n).__name__ == "Entity" for n in nodes)
        print("\n实体关联检查:")
        print(f"  Entity 在 nodes 中: {'✅' if entity_in_nodes else '❌'}")

        all_pass = (
            summaries_count == 2
            and nodesets_count == 1
            and episodes_count == 1
            and has_involves_entity
            and has_memory_spaces
        )

        print("\n" + "=" * 60)
        if all_pass:
            print("🎉 Stage 2 Smoke Test PASSED!")
            print("write_episodic_memories 任务工作正常，可以进入 Stage 3")
        else:
            print("⚠️ Stage 2 Smoke Test 部分通过")
            print("请检查上述失败项")
        print("=" * 60)

    else:
        print("\n❌ 没有找到 Episode 对象，测试失败")


if __name__ == "__main__":
    asyncio.run(main())
