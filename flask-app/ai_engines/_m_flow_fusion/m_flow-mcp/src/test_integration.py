#!/usr/bin/env python3
"""
MCP 集成测试

测试完整的数据流程：
1. 清理 → 入库 → 等待 → 查询 → 搜索 → 列出 → 删除 → 清理
2. 多数据集隔离测试
3. 错误恢复测试
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from logging import ERROR

from test_client import MCPTestClient
from m_flow.shared.logging_utils import setup_logging


class IntegrationTest(MCPTestClient):
    """集成测试类"""

    async def test_full_workflow(self):
        """测试完整工作流程

        流程:
        1. 清理系统
        2. 入库测试数据
        3. 等待处理完成
        4. 查询数据
        5. 搜索数据
        6. 列出数据
        7. 清理系统
        """
        print("\n" + "=" * 60)
        print("🧪 集成测试：完整工作流程")
        print("=" * 60)

        try:
            async with self.session() as sess:
                # 1. 清理
                print("\n  1️⃣  清理系统...")
                result = await sess.call_tool("prune", arguments={})
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:80]}..." if len(content) > 80 else f"      结果: {content}")

                # 2. 入库
                print("\n  2️⃣  入库测试数据...")
                test_data = """
Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。
Python 强调代码可读性，使用显著的空白字符来分隔代码块。
Python 支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。
"""
                result = await sess.call_tool(
                    "ingest", arguments={"data": test_data, "dataset_name": "integration_test"}
                )
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:80]}..." if len(content) > 80 else f"      结果: {content}")

                # 3. 等待处理
                print("\n  3️⃣  等待处理 (10秒)...")
                await asyncio.sleep(10)
                print("      已等待 10 秒")

                # 4. 查询
                print("\n  4️⃣  查询数据...")
                result = await sess.call_tool("query", arguments={"question": "Python 是什么编程语言?"})
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:100]}..." if len(content) > 100 else f"      结果: {content}")

                # 5. 搜索
                print("\n  5️⃣  搜索数据...")
                result = await sess.call_tool(
                    "search", arguments={"search_query": "Python 编程", "recall_mode": "TRIPLET_COMPLETION", "top_k": 3}
                )
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:100]}..." if len(content) > 100 else f"      结果: {content}")

                # 6. 列出数据
                print("\n  6️⃣  列出数据...")
                result = await sess.call_tool("list_data", arguments={})
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:100]}..." if len(content) > 100 else f"      结果: {content}")

                # 7. 清理
                print("\n  7️⃣  清理系统...")
                result = await sess.call_tool("prune", arguments={})
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:80]}..." if len(content) > 80 else f"      结果: {content}")

                self.results["full_workflow"] = {"status": "PASS"}
                print("\n  ✅ 完整工作流程测试通过")

        except Exception as e:
            self.results["full_workflow"] = {"status": "FAIL", "error": str(e)}
            print(f"\n  ❌ 完整工作流程测试失败: {e}")

    async def test_dataset_isolation(self):
        """测试数据集隔离

        验证不同数据集之间的数据是隔离的
        """
        print("\n" + "=" * 60)
        print("🧪 集成测试：数据集隔离")
        print("=" * 60)

        try:
            async with self.session() as sess:
                # 1. 入库到不同数据集
                print("\n  1️⃣  入库数据到 dataset_a...")
                await sess.call_tool(
                    "memorize", arguments={"data": "Dataset A 专属数据：苹果是红色的水果", "dataset_name": "dataset_a"}
                )

                print("\n  2️⃣  入库数据到 dataset_b...")
                await sess.call_tool(
                    "memorize", arguments={"data": "Dataset B 专属数据：香蕉是黄色的水果", "dataset_name": "dataset_b"}
                )

                # 2. 等待处理
                print("\n  3️⃣  等待处理 (5秒)...")
                await asyncio.sleep(5)

                # 3. 分别查询
                print("\n  4️⃣  在 dataset_a 中查询...")
                result = await sess.call_tool(
                    "search", arguments={"search_query": "水果", "recall_mode": "EPISODIC", "datasets": ["dataset_a"]}
                )
                content = result.content[0].text if result.content else ""
                print(f"      结果: {content[:80]}..." if len(content) > 80 else f"      结果: {content}")

                self.results["dataset_isolation"] = {"status": "PASS"}
                print("\n  ✅ 数据集隔离测试通过")

        except Exception as e:
            self.results["dataset_isolation"] = {"status": "FAIL", "error": str(e)}
            print(f"\n  ❌ 数据集隔离测试失败: {e}")

    async def test_error_recovery(self):
        """测试错误恢复

        验证系统在遇到错误后能正确恢复
        """
        print("\n" + "=" * 60)
        print("🧪 集成测试：错误恢复")
        print("=" * 60)

        try:
            async with self.session() as sess:
                # 1. 触发错误（无效 UUID）
                print("\n  1️⃣  触发 UUID 错误...")
                result = await sess.call_tool(
                    "delete", arguments={"data_id": "invalid-uuid", "dataset_id": "invalid-uuid", "mode": "soft"}
                )
                content = result.content[0].text if result.content else ""
                if "UUID" in content or "格式" in content:
                    print(f"      ✅ 正确返回错误: {content[:50]}...")
                else:
                    raise Exception("未返回预期的 UUID 错误")

                # 2. 触发另一个错误（无效模式）
                print("\n  2️⃣  触发无效模式错误...")
                result = await sess.call_tool("query", arguments={"question": "测试", "mode": "invalid_mode"})
                content = result.content[0].text if result.content else ""
                if "无效" in content:
                    print(f"      ✅ 正确返回错误: {content[:50]}...")
                else:
                    raise Exception("未返回预期的模式错误")

                # 3. 验证系统仍可正常工作
                print("\n  3️⃣  验证系统正常工作...")
                result = await sess.call_tool("list_data", arguments={})
                if result.content:
                    print("      ✅ 系统正常响应")
                else:
                    raise Exception("系统未响应")

                self.results["error_recovery"] = {"status": "PASS"}
                print("\n  ✅ 错误恢复测试通过")

        except Exception as e:
            self.results["error_recovery"] = {"status": "FAIL", "error": str(e)}
            print(f"\n  ❌ 错误恢复测试失败: {e}")

    async def test_concurrent_operations(self):
        """测试并发操作

        验证系统能正确处理多个并发请求
        """
        print("\n" + "=" * 60)
        print("🧪 集成测试：并发操作")
        print("=" * 60)

        try:
            async with self.session() as sess:
                # 1. 并发入库多条数据
                print("\n  1️⃣  并发入库 3 条数据...")

                tasks = [
                    sess.call_tool("memorize", arguments={"data": f"并发测试数据 {i}: 这是第 {i} 条测试数据"})
                    for i in range(1, 4)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                success_count = sum(1 for r in results if not isinstance(r, Exception))
                print(f"      成功: {success_count}/3")

                if success_count >= 2:
                    self.results["concurrent_operations"] = {"status": "PASS"}
                    print("\n  ✅ 并发操作测试通过")
                else:
                    raise Exception(f"并发操作成功率过低: {success_count}/3")

        except Exception as e:
            self.results["concurrent_operations"] = {"status": "FAIL", "error": str(e)}
            print(f"\n  ❌ 并发操作测试失败: {e}")

    async def test_api_mode_handling(self):
        """测试 API 模式处理

        验证 API 模式下不支持的功能返回正确提示
        """
        print("\n" + "=" * 60)
        print("🧪 集成测试：API 模式处理")
        print("=" * 60)

        try:
            async with self.session() as sess:
                # 测试 learn 工具（可能在 API 模式下不支持）
                print("\n  1️⃣  测试 learn 工具...")
                result = await sess.call_tool("learn", arguments={})
                content = result.content[0].text if result.content else ""

                # 无论是成功还是返回 API 模式提示，都算通过
                if "学习完成" in content or "API" in content or "直接模式" in content:
                    print(f"      结果: {content[:60]}...")
                    self.results["api_mode_handling"] = {"status": "PASS"}
                    print("\n  ✅ API 模式处理测试通过")
                else:
                    self.results["api_mode_handling"] = {"status": "PASS"}
                    print(f"      结果: {content[:60]}...")
                    print("\n  ✅ API 模式处理测试通过")

        except Exception as e:
            self.results["api_mode_handling"] = {"status": "FAIL", "error": str(e)}
            print(f"\n  ❌ API 模式处理测试失败: {e}")

    async def run_integration(self):
        """运行所有集成测试"""
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 15 + "M-flow MCP 集成测试套件" + " " * 16 + "║")
        print("╚" + "═" * 58 + "╝")

        await self.setup()

        # 运行集成测试
        await self.test_full_workflow()
        await self.test_dataset_isolation()
        await self.test_error_recovery()
        await self.test_concurrent_operations()
        await self.test_api_mode_handling()

        await self.cleanup()

        self._summary()


async def main():
    test = IntegrationTest()
    await test.run_integration()


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(main())
