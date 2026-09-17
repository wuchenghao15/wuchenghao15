"""
Neptune Analytics混合存储测试

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

from m_flow.core.domain.models import Entity, EntityType
from m_flow.data.processing.document_types import TextDocument
from m_flow.ingestion.chunking.models import ContentFragment
from m_flow.shared.logging_utils import get_logger

_collection = "test_coll"
_log = get_logger("neptune_hybrid_test")


# 延迟初始化适配器
def _get_adapters():
    from m_flow.adapters.hybrid.neptune_analytics.NeptuneAnalyticsAdapter import NeptuneAnalyticsAdapter
    from m_flow.adapters.vector.embeddings import get_embedding_engine

    _embed = get_embedding_engine()
    _graph = NeptuneAnalyticsAdapter(_graph_id)
    _vector = NeptuneAnalyticsAdapter(_graph_id, _embed)
    return _graph, _vector, _embed


@pytest.fixture
def adapters():
    """获取适配器"""
    return _get_adapters()


def _create_data():
    """创建测试数据"""
    doc = TextDocument(
        name="sample.txt",
        processed_path="/path/to/sample.txt",
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
    amazon_db = Entity(name="amazon neptune database", description="托管图数据库")
    storage = EntityType(name="storage", description="存储")
    s3 = Entity(name="amazon s3", description="AWS存储服务")

    nodes = [doc, chunk, graph_db, neptune, amazon_db, storage, s3]
    edges = [
        (str(chunk.id), str(s3.id), "contains"),
        (str(s3.id), str(storage.id), "is_a"),
        (str(chunk.id), str(amazon_db.id), "contains"),
        (str(amazon_db.id), str(graph_db.id), "is_a"),
        (str(chunk.id), str(doc.id), "is_part_of"),
        (str(chunk.id), str(neptune.id), "contains"),
        (str(neptune.id), str(graph_db.id), "is_a"),
    ]
    return nodes, edges


async def test_graph_then_vector():
    """测试先图后向量"""
    _graph, _vector, _embed = _get_adapters()
    _log.info("--- 测试: 先图后向量 ---")
    nodes, edges = _create_data()

    await _graph.add_nodes(nodes)
    await _graph.add_edges(edges)
    await _vector.create_memory_nodes(_collection, nodes)

    ids = [str(n.id) for n in nodes]
    mem = await _vector.retrieve(_collection, ids)
    graph_nodes = await _graph.get_nodes(ids)

    assert len(mem) == len(graph_nodes) == len(ids)

    await _graph.delete_graph()
    await _vector.prune()

    n, e = await _graph.get_graph_data()
    assert len(n) == 0 and len(e) == 0
    _log.info("--- 通过 ---")


async def test_vector_then_graph():
    """测试先向量后图"""
    _graph, _vector, _embed = _get_adapters()
    _log.info("--- 测试: 先向量后图 ---")
    nodes, edges = _create_data()

    await _vector.create_memory_nodes(_collection, nodes)
    await _graph.add_nodes(nodes)
    await _graph.add_edges(edges)

    ids = [str(n.id) for n in nodes]
    mem = await _vector.retrieve(_collection, ids)
    graph_nodes = await _graph.get_nodes(ids)

    assert len(mem) == len(graph_nodes) == len(ids)

    await _vector.prune()
    await _graph.delete_graph()

    n, e = await _graph.get_graph_data()
    assert len(n) == 0 and len(e) == 0
    _log.info("--- 通过 ---")


def main():
    """运行测试"""
    asyncio.run(test_graph_then_vector())
    asyncio.run(test_vector_then_graph())


if __name__ == "__main__":
    main()
