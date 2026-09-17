"""
图数据库节点写入子进程测试
用于测试并发写入场景
"""

from __future__ import annotations

import asyncio
import uuid
from time import sleep

from m_flow.adapters.graph.kuzu.adapter import KuzuAdapter
from m_flow.data.processing.document_types import PdfDocument

_DB_PATH = "test.db"
_NODE_COUNT = 5
_WAIT_SECONDS = 10


def create_pdf_node(idx: int) -> PdfDocument:
    """创建PDF文档节点"""
    name = f"TestDocument_{idx}"
    return PdfDocument(
        id=uuid.uuid4(),
        name=name,
        processed_path=f"/tmp/{name}.pdf",
        external_metadata="{'source': 'unit_test'}",
        mime_type="application/pdf",
    )


async def execute_write_test() -> None:
    """执行写入测试"""
    graph = KuzuAdapter(_DB_PATH)
    nodes = [create_pdf_node(i) for i in range(_NODE_COUNT)]

    print(f"开始写入 {len(nodes)} 个节点...")
    await graph.add_nodes(nodes)
    print(f"写入完成, 等待 {_WAIT_SECONDS} 秒...")

    sleep(_WAIT_SECONDS)


if __name__ == "__main__":
    asyncio.run(execute_write_test())
