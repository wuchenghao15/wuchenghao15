"""
加权边测试
"""

from __future__ import annotations

from typing import Any, List

import pytest
from pydantic import SkipValidation

from m_flow.core import MemoryNode
from m_flow.core.models.Edge import Edge
from m_flow.knowledge.graph_ops.utils import extract_graph


class _Product(MemoryNode):
    name: str
    description: str
    metadata: dict = {"index_fields": ["name"]}


class _Category(MemoryNode):
    name: str
    description: str
    products: List[_Product] = []
    metadata: dict = {"index_fields": ["name"]}


class _User(MemoryNode):
    name: str
    email: str
    purchased_products: SkipValidation[Any] = None
    favorite_categories: SkipValidation[Any] = None
    follows: SkipValidation[Any] = None
    metadata: dict = {"index_fields": ["name", "email"]}


class _Company(MemoryNode):
    name: str
    description: str
    employees: SkipValidation[Any] = None
    partners: SkipValidation[Any] = None
    metadata: dict = {"index_fields": ["name"]}


@pytest.mark.asyncio
async def test_single_weight():
    """单权重边测试"""
    p1 = _Product(name="笔记本", description="游戏本")
    p2 = _Product(name="鼠标", description="无线鼠标")

    user = _User(
        name="张三",
        email="zhang@test.com",
        purchased_products=(Edge(weight=0.8, relationship_type="purchased"), [p1, p2]),
    )

    nodes, edges = await extract_graph(user, {}, {}, {})

    assert len(nodes) == 3
    assert len(edges) == 2
    for e in edges:
        props = e[3]
        assert props["weight"] == 0.8
        assert props["relationship_name"] == "purchased"


@pytest.mark.asyncio
async def test_multi_weights():
    """多权重边测试"""
    c1 = _Category(name="电子产品", description="电子类")
    c2 = _Category(name="游戏", description="游戏类")

    user = _User(
        name="李四",
        email="li@test.com",
        favorite_categories=(
            Edge(
                weights={"兴趣": 0.9, "时间": 0.7, "频率": 0.8, "专业度": 0.6},
                relationship_type="interested_in",
            ),
            [c1, c2],
        ),
    )

    nodes, edges = await extract_graph(user, {}, {}, {})

    assert len(nodes) == 3
    assert len(edges) == 2
    for e in edges:
        props = e[3]
        assert props["weight_兴趣"] == 0.9
        assert props["weight_时间"] == 0.7


@pytest.mark.asyncio
async def test_mixed_weights():
    """混合权重测试"""
    p = _Product(name="手机", description="智能手机")

    user = _User(
        name="王五",
        email="wang@test.com",
        purchased_products=(
            Edge(weight=0.7, weights={"满意度": 0.9, "性价比": 0.6}, relationship_type="owns"),
            [p],
        ),
    )

    nodes, edges = await extract_graph(user, {}, {}, {})

    assert len(nodes) == 2
    assert len(edges) == 1
    props = edges[0][3]
    assert props["weight"] == 0.7
    assert props["weight_满意度"] == 0.9
    assert props["weight_性价比"] == 0.6


@pytest.mark.asyncio
async def test_complex_relations():
    """复杂关系测试"""
    p1 = _Product(name="游戏椅", description="电竞椅")
    p2 = _Product(name="键盘", description="机械键盘")
    cat = _Category(name="游戏配件", description="配件类")
    cat.products = [p1, p2]

    u1 = _User(
        name="玩家A",
        email="a@test.com",
        purchased_products=(
            Edge(weights={"满意度": 0.95, "使用频率": 0.9}, relationship_type="purchased"),
            [p1, p2],
        ),
        favorite_categories=(Edge(weight=0.9, relationship_type="follows"), [cat]),
    )
    u2 = _User(
        name="用户B",
        email="b@test.com",
        purchased_products=(Edge(weight=0.6, relationship_type="purchased"), [p1]),
    )
    u1.follows = (Edge(weights={"友谊度": 0.7, "共同兴趣": 0.8}, relationship_type="follows"), [u2])

    nodes, edges = await extract_graph(u1, {}, {}, {})

    assert len(nodes) == 5
    edge_types = {e[2] for e in edges}
    assert "purchased" in edge_types
    assert "follows" in edge_types


@pytest.mark.asyncio
async def test_company_hierarchy():
    """公司层级测试"""
    ceo = _User(name="CEO", email="ceo@co.com")
    mgr = _User(name="经理", email="mgr@co.com")
    dev = _User(name="开发者", email="dev@co.com")

    startup = _Company(
        name="科技公司",
        description="创业公司",
        employees=(
            Edge(weights={"资历": 0.9, "绩效": 0.8, "领导力": 0.95}, relationship_type="employs"),
            [ceo, mgr, dev],
        ),
    )
    corp = _Company(name="大企业", description="大公司")
    startup.partners = (
        Edge(weights={"信任度": 0.7, "商业价值": 0.8}, relationship_type="partners_with"),
        [corp],
    )

    nodes, edges = await extract_graph(startup, {}, {}, {})

    assert len(nodes) == 5
    partner_edges = [e for e in edges if e[2] == "partners_with"]
    emp_edges = [e for e in edges if e[2] == "employs"]
    assert len(partner_edges) == 1
    assert len(emp_edges) == 3


@pytest.mark.asyncio
async def test_metadata_preservation():
    """元数据保持测试"""
    p = _Product(name="测试产品", description="测试")

    user = _User(
        name="测试用户",
        email="test@test.com",
        purchased_products=(
            Edge(weight=0.8, weights={"质量": 0.9, "价格": 0.7}, relationship_type="purchased"),
            [p],
        ),
    )

    nodes, edges = await extract_graph(user, {}, {}, {})

    assert len(edges) == 1
    props = edges[0][3]
    assert "source_node_id" in props
    assert "target_node_id" in props
    assert "relationship_name" in props
    assert props["weight"] == 0.8
    assert props["weight_质量"] == 0.9


@pytest.mark.asyncio
async def test_no_weights():
    """无权重边测试"""
    p = _Product(name="简单产品", description="简单")

    user = _User(
        name="简单用户",
        email="simple@test.com",
        purchased_products=(Edge(relationship_type="purchased"), [p]),
    )

    nodes, edges = await extract_graph(user, {}, {}, {})

    assert len(nodes) == 2
    assert len(edges) == 1
    props = edges[0][3]
    assert "weight" not in props
    assert len([k for k in props if k.startswith("weight_")]) == 0
