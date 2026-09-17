"""验证 extract_graph 在模型存在循环引用时的节点/边提取行为。"""

from __future__ import annotations

import asyncio
from typing import List
from uuid import NAMESPACE_OID, uuid5

import pytest

from m_flow.core import MemoryNode
from m_flow.knowledge.graph_ops.utils import extract_graph


class Project(MemoryNode):
    """顶层项目实体"""

    root_path: str
    metadata: dict = {"index_fields": []}


class Module(MemoryNode):
    """项目内模块，可相互依赖"""

    belongs_to: Project
    fragments: List["Fragment"] = []
    imports: List["Module"] = []
    content: str
    metadata: dict = {"index_fields": []}


class Fragment(MemoryNode):
    """模块中的代码片段"""

    parent_module: Module
    content: str
    metadata: dict = {"index_fields": []}


Module.model_rebuild()
Fragment.model_rebuild()


class TestCircularGraphExtraction:
    """当模型图中包含循环引用时，确保 extract_graph 能正确终止并返回期望的节点与边数量。"""

    @pytest.mark.asyncio
    async def test_cyclic_model_produces_expected_graph(self):
        """构造 Project -> Module -> Fragment 循环引用，验证返回 3 个节点、3 条边。"""
        proj = Project(root_path="sample_proj")

        mod_a = Module(
            id=uuid5(NAMESPACE_OID, "mod_alpha"),
            content="module code",
            belongs_to=proj,
            fragments=[],
            imports=[],
        )
        frag_a = Fragment(content="fragment_alpha", parent_module=mod_a)
        mod_a.fragments.append(frag_a)

        node_map = {}
        edge_map = {}
        prop_tracker = {}

        extracted_nodes, extracted_edges = await extract_graph(
            mod_a,
            added_nodes=node_map,
            added_edges=edge_map,
            visited_properties=prop_tracker,
        )

        assert len(extracted_nodes) == 3
        assert len(extracted_edges) == 3


if __name__ == "__main__":
    asyncio.run(TestCircularGraphExtraction().test_cyclic_model_produces_expected_graph())
