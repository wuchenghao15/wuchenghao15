"""
MCP客户端示例
演示如何通过MCP协议调用M-flow工具
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_PARAMS = StdioServerParameters(
    command="uv",
    args=["--directory", ".", "run", "m_flow"],
    env=None,
)

_SESSION_TIMEOUT = timedelta(minutes=3)


async def demo():
    """运行MCP客户端演示"""
    async with stdio_client(_SERVER_PARAMS) as (reader, writer):
        async with ClientSession(reader, writer, _SESSION_TIMEOUT) as session:
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print(f"发现 {len(tools.tools)} 个工具")

            # 清空数据（重置状态）
            await session.call_tool("prune", arguments={})

            # 添加示例数据
            await session.call_tool(
                "memorize", arguments={"data": "人工智能（AI）是计算机科学的一个分支，致力于创建智能机器。"}
            )

            # 等待后台处理完成
            await asyncio.sleep(5)

            # 搜索
            result = await session.call_tool(
                "search",
                arguments={"search_query": "什么是人工智能?", "recall_mode": "TRIPLET_COMPLETION"},
            )

            print(f"搜索结果: {result.content}")


if __name__ == "__main__":
    asyncio.run(demo())
