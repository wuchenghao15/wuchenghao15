"""
Stage 1 Smoke Test: 验证 Episode/Facet 模型的图结构抽取

这个测试不需要 LLM 或 embedding，只验证 extract_graph() 能正确抽取：
1. nodes 里包含 Episode / Facet / Entity
2. edges 里包含 has_facet、involves_entity 两条边
3. 每条边 properties 里有 relationship_name 和 edge_text

运行方式：
    cd m_flow-main
    python examples/episodic_stage1_smoke_test.py

期望输出：
- 3 个节点：Episode, Facet, Entity
- 2 条边：has_facet, involves_entity
- 每条边都有 edge_text 属性
"""

import asyncio

from m_flow.core import Edge
from m_flow.core.domain.models import Entity, Episode, Facet
from m_flow.knowledge.graph_ops.utils.extract_graph import extract_graph


def _make_has_facet_edge_text(episode_name: str, facet: Facet) -> str:
    """生成 has_facet 边的 edge_text（对齐 contains.edge_text 的结构化风格）"""
    return "; ".join(
        [
            "relationship_name: has_facet",
            f"episode: {episode_name}",
            f"facet_type: {facet.facet_type}",
            f"facet_search_text: {facet.search_text}",
        ]
    )


def _make_involves_entity_edge_text(episode_name: str, entity: Entity) -> str:
    """生成 involves_entity 边的 edge_text（对齐 contains.edge_text 的结构化风格）"""
    desc = getattr(entity, "description", "") or ""
    if len(desc) > 200:
        desc = desc[:197] + "..."
    return "; ".join(
        [
            "relationship_name: involves_entity",
            f"episode: {episode_name}",
            f"entity_name: {entity.name}",
            f"entity_description: {desc}",
        ]
    )


async def main():
    print("=" * 60)
    print("Stage 1 Smoke Test: Episode/Facet 图结构抽取验证")
    print("=" * 60)

    # 1. 创建一个 Entity（detail）
    promo = Entity(name="促销", description="促销活动")
    print(f"\n✓ 创建 Entity: {promo.name} (id={promo.id})")

    # 2. 创建一个 Facet（detail handle）
    facet = Facet(
        name="Q3 促销导致毛利下降 2pct",
        facet_type="outcome",
        search_text="Q3 促销导致毛利下降 2pct",
        description="Q3 期间采用满减与会员券叠加，带来销量提升但毛利下降约 2pct。",
    )
    print(f"✓ 创建 Facet: {facet.name} (id={facet.id})")

    # 3. 创建 Episode（anchor），挂载 Facet 和 Entity
    episode_name = "Q3 促销策略与毛利变化"

    ep = Episode(
        name=episode_name,
        summary="在 Q3，我们采取促销策略提升销量，但出现毛利下降约 2pct 的结果。",
        signature="Q3-促销-毛利-下降",
        has_facet=[
            (
                Edge(
                    relationship_type="has_facet",
                    edge_text=_make_has_facet_edge_text(episode_name, facet),
                ),
                facet,
            )
        ],
        involves_entity=[
            (
                Edge(
                    relationship_type="involves_entity",
                    edge_text=_make_involves_entity_edge_text(episode_name, promo),
                ),
                promo,
            )
        ],
    )
    print(f"✓ 创建 Episode: {ep.name} (id={ep.id})")

    # 4. 调用 extract_graph 抽取图结构
    print("\n" + "-" * 60)
    print("调用 extract_graph() 抽取图结构...")
    print("-" * 60)

    nodes, edges = await extract_graph(
        ep,
        added_nodes={},
        added_edges={},
        visited_properties={},
        include_root=True,
    )

    # 5. 打印节点
    print("\n=== NODES ===")
    for n in nodes:
        node_type = type(n).__name__
        node_id = getattr(n, "id", "N/A")
        node_name = getattr(n, "name", "N/A")
        print(f"  [{node_type}] id={node_id}, name={node_name}")

    # 6. 打印边
    print("\n=== EDGES ===")
    for e in edges:
        src, dst, rel, props = e
        print(f"\n  关系: {rel}")
        print(f"    src_id: {src}")
        print(f"    dst_id: {dst}")
        print(f"    relationship_name: {props.get('relationship_name', 'N/A')}")
        edge_text = props.get("edge_text", "N/A")
        if edge_text and len(edge_text) > 100:
            edge_text = edge_text[:97] + "..."
        print(f"    edge_text: {edge_text}")

    # 7. 验证结果
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)

    # 检查节点数量和类型
    node_types = [type(n).__name__ for n in nodes]
    expected_node_types = {"Episode", "Facet", "Entity"}
    actual_node_types = set(node_types)

    print("\n节点类型检查:")
    print(f"  期望: {expected_node_types}")
    print(f"  实际: {actual_node_types}")
    if expected_node_types == actual_node_types:
        print("  ✅ PASS")
    else:
        print("  ❌ FAIL")

    # 检查边数量和类型
    edge_rels = [e[2] for e in edges]
    expected_edge_rels = {"has_facet", "involves_entity"}
    actual_edge_rels = set(edge_rels)

    print("\n边关系检查:")
    print(f"  期望: {expected_edge_rels}")
    print(f"  实际: {actual_edge_rels}")
    if expected_edge_rels == actual_edge_rels:
        print("  ✅ PASS")
    else:
        print("  ❌ FAIL")

    # 检查 edge_text 是否存在
    print("\nedge_text 存在性检查:")
    all_have_edge_text = all(e[3].get("edge_text") for e in edges)
    for e in edges:
        rel = e[2]
        has_text = bool(e[3].get("edge_text"))
        status = "✅" if has_text else "❌"
        print(f"  {rel}: {status}")

    if all_have_edge_text:
        print("  ✅ PASS - 所有边都有 edge_text")
    else:
        print("  ❌ FAIL - 部分边缺少 edge_text")

    # 检查 relationship_name 是否在 props 中
    print("\nrelationship_name in props 检查:")
    all_have_rel_name = all(e[3].get("relationship_name") for e in edges)
    for e in edges:
        rel = e[2]
        rel_in_props = e[3].get("relationship_name")
        status = "✅" if rel_in_props else "❌"
        print(f"  {rel}: relationship_name={rel_in_props} {status}")

    if all_have_rel_name:
        print("  ✅ PASS - 所有边都有 relationship_name")
    else:
        print("  ❌ FAIL - 部分边缺少 relationship_name")

    # 总结
    print("\n" + "=" * 60)
    all_pass = (
        expected_node_types == actual_node_types
        and expected_edge_rels == actual_edge_rels
        and all_have_edge_text
        and all_have_rel_name
    )
    if all_pass:
        print("🎉 Stage 1 Smoke Test PASSED!")
        print("图结构抽取正确，可以进入 Stage 2")
    else:
        print("⚠️ Stage 1 Smoke Test FAILED!")
        print("请检查上述失败项")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
