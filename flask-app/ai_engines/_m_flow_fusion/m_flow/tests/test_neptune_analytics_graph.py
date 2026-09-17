"""
Neptune Analytics图数据库测试

NOTE: 需要 AWS Neptune Analytics 环境才能运行这些测试。
设置 GRAPH_ID 环境变量后才能执行测试。
"""

from __future__ import annotations

import asyncio
import os

import pytest
from dotenv import load_dotenv

load_dotenv()
_graph_id = os.getenv("GRAPH_ID", "")

# 跳过测试，除非 GRAPH_ID 已配置
pytestmark = pytest.mark.skipif(not _graph_id, reason="需要设置 GRAPH_ID 环境变量来运行 Neptune Analytics 测试")


# 延迟导入，避免在收集时实例化
def _get_adapter():
    from m_flow.adapters.graph.neptune_driver import NeptuneGraphDB

    return NeptuneGraphDB(_graph_id)


from m_flow.core.domain.models import Entity, EntityType
from m_flow.data.processing.document_types import TextDocument
from m_flow.ingestion.chunking.models import ContentFragment


@pytest.fixture
def adapter():
    """获取 Neptune 适配器"""
    return _get_adapter()


def _create_data():
    """创建测试数据"""
    doc = TextDocument(
        name="sample.txt",
        processed_path="/path/sample.txt",
        external_metadata="{}",
        mime_type="text/plain",
    )
    chunk = ContentFragment(
        text="Neptune Analytics是数据分析的理想选择，支持图数据上的向量搜索。它与Amazon Neptune Database互补。",
        chunk_size=50,
        chunk_index=0,
        cut_type="paragraph_end",
        is_part_of=doc,
    )

    graph_db = EntityType(name="graph database", description="图数据库")
    neptune = Entity(name="neptune analytics", description="内存优化的图分析引擎")
    neptune_db = Entity(name="amazon neptune database", description="托管图数据库")
    storage = EntityType(name="storage", description="存储")
    s3 = Entity(name="amazon s3", description="AWS存储服务")

    nodes = [doc, chunk, graph_db, neptune, neptune_db, storage, s3]
    edges = [
        (str(chunk.id), str(s3.id), "contains"),
        (str(s3.id), str(storage.id), "is_a"),
        (str(chunk.id), str(neptune_db.id), "contains"),
        (str(neptune_db.id), str(graph_db.id), "is_a"),
        (str(chunk.id), str(doc.id), "is_part_of"),
        (str(chunk.id), str(neptune.id), "contains"),
        (str(neptune.id), str(graph_db.id), "is_a"),
    ]
    return nodes, edges


async def test_pipeline():
    """流水线测试"""
    _adapter = _get_adapter()
    print("--- 清空图 ---")
    await _adapter.delete_graph()

    print("--- 创建数据 ---")
    nodes, edges = _create_data()

    print("--- 添加节点 ---")
    await _adapter.add_node(nodes[0])
    await _adapter.add_nodes(nodes[1:])

    print("--- 获取节点 ---")
    ids = [str(n.id) for n in nodes]
    db_nodes = await _adapter.get_nodes(ids)
    for n in db_nodes:
        print(n)

    print("--- 添加边 ---")
    await _adapter.add_edge(edges[0][0], edges[0][1], edges[0][2])
    await _adapter.add_edges(edges[1:])

    print("--- 检查边 ---")
    has = await _adapter.has_edge(edges[0][0], edges[0][1], edges[0][2])
    if has:
        print(f"找到边: {edges[0]}")
    found = await _adapter.has_edges(edges)
    print(f"找到边数: {len(found)} (期望: {len(edges)})")

    print("--- 获取图 ---")
    all_n, all_e = await _adapter.get_graph_data()
    print(f"节点: {len(all_n)}, 边: {len(all_e)}")

    print("--- 邻居节点 ---")
    center = nodes[2]
    neighbors = await _adapter.get_neighbors(str(center.id))
    print(f"{center.name}的邻居: {len(neighbors)}")

    print("--- 邻居边 ---")
    adj_edges = await _adapter.get_edges(str(center.id))
    print(f"{center.name}的边: {len(adj_edges)}")

    print("--- 连接 ---")
    conns = await _adapter.get_triplets(str(center.id))
    print(f"{center.name}的连接: {len(conns)}")

    print("--- 子图 ---")
    names = ["neptune analytics", "amazon neptune database"]
    sub_n, sub_e = await _adapter.extract_typed_subgraph(Entity, names)
    print(f"子图: {len(sub_n)}节点, {len(sub_e)}边")

    print("--- 统计 ---")
    stat = await _adapter.get_graph_metrics(extended=True)
    assert stat["num_nodes"] == 7 and stat["num_edges"] == 7
    assert stat["mean_degree"] == 2.0
    assert round(stat["edge_density"], 3) == 0.167
    assert stat["num_selfloops"] == 0

    print("--- 删除 ---")
    await _adapter.delete_graph()
    found = await _adapter.has_edges(edges)
    print("删除成功" if len(found) == 0 else "删除失败")


async def test_misc():
    """杂项测试"""
    _adapter = _get_adapter()
    print("--- 清空 ---")
    await _adapter.delete_graph()

    print("--- 设置 ---")
    nodes, edges = _create_data()
    await _adapter.add_nodes(nodes)
    await _adapter.add_edges(edges)

    print("--- 断开节点 ---")
    disconnected = await _adapter.get_disconnected_nodes()
    assert len(disconnected) == 0

    print("--- 标签 ---")
    print(await _adapter.get_node_labels_string())
    print(await _adapter.get_relationship_labels_string())

    print("--- 过滤图 ---")
    fn, fe = await _adapter.query_by_attributes([{"name": ["sample.txt"]}])
    print(fn, fe)

    print("--- 度为1节点 ---")
    d1 = await _adapter.get_degree_one_nodes("EntityType")
    print(d1)

    print("--- 前驱 ---")
    src, dst, rel = edges[0]
    pred = await _adapter.get_predecessors(node_id=dst, edge_label=rel)
    assert len(pred) > 0
    await _adapter.remove_connection_to_predecessors_of([src], edge_label=rel)
    pred2 = await _adapter.get_predecessors(node_id=dst, edge_label=rel)
    assert len(pred2) == 0

    print("--- 后继 ---")
    _, ee = await _adapter.get_graph_data()
    src, dst, rel, _ = ee[0]
    succ = await _adapter.get_successors(node_id=src, edge_label=rel)
    assert len(succ) > 0
    await _adapter.remove_connection_to_successors_of([dst], edge_label=rel)
    succ2 = await _adapter.get_successors(node_id=src, edge_label=rel)
    assert len(succ2) == 0

    await _adapter.project_entire_graph()
    await _adapter.drop_graph()
    await _adapter.graph_exists()


if __name__ == "__main__":
    asyncio.run(test_pipeline())
    asyncio.run(test_misc())
