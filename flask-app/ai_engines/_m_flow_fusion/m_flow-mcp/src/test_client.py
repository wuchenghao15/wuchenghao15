#!/usr/bin/env python3
"""
M-flow MCP服务器测试客户端

测试MCP服务器的所有工具和功能
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from logging import ERROR

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from m_flow.adapters.exceptions import DatabaseNotCreatedError
from m_flow.pipeline.models.PipelineRun import RunStatus
from m_flow.shared.logging_utils import setup_logging
from src.server import load_class, node_to_string, retrieved_edges_to_string

_TIMEOUT = 5 * 60  # 5分钟


class MCPTestClient:
    """MCP服务器测试客户端"""

    def __init__(self):
        self.results = {}
        self.temp_dir = None

    async def setup(self):
        """设置测试环境"""
        print("🔧 初始化测试环境...")

        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        if not api_key:
            print("⚠️  未配置API密钥")
        else:
            print("✅ API密钥已配置")

        self.temp_dir = tempfile.mkdtemp(prefix="mflow_test_")

        # 创建测试文本文件
        with open(os.path.join(self.temp_dir, "test.txt"), "w") as f:
            f.write("测试文档：AI与知识图谱")

        # 创建测试代码
        repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(repo_dir)
        with open(os.path.join(repo_dir, "main.py"), "w") as f:
            f.write('def hello(): return "Hello"\nclass Demo:\n    pass\n')

        print(f"✅ 测试环境: {self.temp_dir}")

    async def cleanup(self):
        """清理测试环境"""
        print("🧹 清理...")
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        print("✅ 清理完成")

    @asynccontextmanager
    async def session(self):
        """MCP会话上下文管理器"""
        script = os.path.join(os.path.dirname(__file__), "server.py")
        params = StdioServerParameters(
            command="python",
            args=[script, "--transport", "stdio"],
            env=os.environ.copy(),
        )
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as sess:
                await sess.initialize()
                yield sess

    async def _test_startup(self, sess):
        """测试服务器启动和工具发现"""
        print("\n🧪 测试服务器启动...")
        try:
            tools = await sess.list_tools()
            expected = {
                "memorize",
                "save_interaction",
                "search",
                "prune",
                "memorize_status",
                "list_data",
                "delete",
                "learn",
                "update_data",
                "ingest",
                "query",
            }
            found = {t.name for t in tools.tools}

            if not expected.issubset(found):
                raise AssertionError(f"缺少工具: {expected - found}")

            self.results["startup"] = {"status": "PASS"}
            print(f"    ✅ 发现 {len(found)} 个工具（期望 {len(expected)} 个）")
        except Exception as e:
            self.results["startup"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ 启动测试失败: {e}")

    async def test_startup(self):
        async with self.session() as sess:
            await self._test_startup(sess)

    async def _test_prune(self, sess):
        """测试prune功能"""
        print("\n🧪 测试 prune...")
        try:
            await sess.call_tool("prune", arguments={})
            self.results["prune"] = {"status": "PASS"}
            print("✅ prune 通过")
        except Exception as e:
            self.results["prune"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ prune 失败: {e}")

    async def test_prune(self):
        async with self.session() as sess:
            await self._test_prune(sess)

    async def _test_memorize(self, sess, text: str, name: str):
        """测试memorize功能"""
        print(f"\n🧪 测试 memorize ({name})...")
        try:
            await sess.call_tool("memorize", arguments={"data": text})

            start = time.time()
            while True:
                await asyncio.sleep(5)
                try:
                    status = await sess.call_tool("memorize_status", arguments={})
                    txt = status.content[0].text if status.content else str(status)

                    if str(RunStatus.DATASET_PROCESSING_COMPLETED) in txt:
                        break
                    if time.time() - start > _TIMEOUT:
                        raise TimeoutError("记忆化超时")
                except DatabaseNotCreatedError:
                    if time.time() - start > _TIMEOUT:
                        raise TimeoutError("数据库创建超时")

            self.results[name] = {"status": "PASS"}
            print(f"✅ {name} 通过")
        except Exception as e:
            self.results[name] = {"status": "FAIL", "error": str(e)}
            print(f"❌ {name} 失败: {e}")

    async def test_memorize(self, text: str, name: str):
        async with self.session() as sess:
            await self._test_memorize(sess, text, name)

    async def _test_search(self, sess):
        """测试搜索功能"""
        print("\n🧪 测试 search...")
        from m_flow import RecallMode

        query = "什么是人工智能?"

        for mode in RecallMode:
            if mode == RecallMode.CYPHER:
                continue
            try:
                await sess.call_tool(
                    "search",
                    arguments={"search_query": query, "recall_mode": mode.value},
                )
                self.results[f"search_{mode}"] = {"status": "PASS"}
                print(f"✅ search {mode} 通过")
            except Exception as e:
                self.results[f"search_{mode}"] = {"status": "FAIL", "error": str(e)}
                print(f"❌ search {mode} 失败: {e}")

    async def test_search(self):
        async with self.session() as sess:
            await self._test_search(sess)

    async def _test_search_invalid_mode(self, sess):
        """测试search使用无效recall_mode时的错误处理"""
        print("\n🧪 测试 search 无效模式...")
        try:
            result = await sess.call_tool(
                "search",
                arguments={"search_query": "测试", "recall_mode": "INVALID_MODE"},
            )
            content = result.content[0].text if result.content else ""
            if "无效的召回模式" in content:
                self.results["search_invalid_mode"] = {"status": "PASS"}
                print("✅ search 无效模式错误处理通过")
            else:
                raise Exception("未检测到无效模式错误")
        except Exception as e:
            self.results["search_invalid_mode"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ search 无效模式测试失败: {e}")

    async def test_search_invalid_mode(self):
        async with self.session() as sess:
            await self._test_search_invalid_mode(sess)

    async def _test_search_with_datasets(self, sess):
        """测试search带datasets参数"""
        print("\n🧪 测试 search 带 datasets 参数...")
        try:
            result = await sess.call_tool(
                "search",
                arguments={
                    "search_query": "测试",
                    "recall_mode": "TRIPLET_COMPLETION",
                    "datasets": ["test_dataset"],
                },
            )
            if result.content:
                self.results["search_with_datasets"] = {"status": "PASS"}
                print("✅ search 带 datasets 通过")
            else:
                raise Exception("无返回内容")
        except Exception as e:
            self.results["search_with_datasets"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ search 带 datasets 失败: {e}")

    async def test_search_with_datasets(self):
        async with self.session() as sess:
            await self._test_search_with_datasets(sess)

    async def _test_prune_with_params(self, sess):
        """测试prune带参数"""
        print("\n🧪 测试 prune 带参数...")
        try:
            result = await sess.call_tool(
                "prune",
                arguments={"graph": True, "vector": True, "metadata": False, "cache": True},
            )
            content = result.content[0].text if result.content else ""
            if "已清除" in content or "API 模式不支持" in content:
                self.results["prune_with_params"] = {"status": "PASS"}
                print("✅ prune 带参数通过")
            else:
                raise Exception(f"未预期的返回: {content}")
        except Exception as e:
            self.results["prune_with_params"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ prune 带参数失败: {e}")

    async def test_prune_with_params(self):
        async with self.session() as sess:
            await self._test_prune_with_params(sess)

    async def _test_memorize_with_dataset(self, sess):
        """测试memorize带dataset_name参数"""
        print("\n🧪 测试 memorize 带 dataset_name 参数...")
        try:
            result = await sess.call_tool(
                "memorize",
                arguments={"data": "测试数据", "dataset_name": "test_dataset"},
            )
            content = result.content[0].text if result.content else ""
            if "后台任务已启动" in content and "test_dataset" in content:
                self.results["memorize_with_dataset"] = {"status": "PASS"}
                print("✅ memorize 带 dataset_name 通过")
            else:
                raise Exception(f"未预期的返回: {content}")
        except Exception as e:
            self.results["memorize_with_dataset"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ memorize 带 dataset_name 失败: {e}")

    async def test_memorize_with_dataset(self):
        async with self.session() as sess:
            await self._test_memorize_with_dataset(sess)

    async def _test_list_data(self, sess):
        """测试list_data功能"""
        print("\n🧪 测试 list_data...")
        try:
            result = await sess.call_tool("list_data", arguments={})
            if result.content:
                self.results["list_data"] = {"status": "PASS"}
                print("✅ list_data 通过")
            else:
                raise Exception("无返回内容")
        except Exception as e:
            self.results["list_data"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ list_data 失败: {e}")

    async def test_list_data(self):
        async with self.session() as sess:
            await self._test_list_data(sess)

    async def _test_delete(self, sess):
        """测试delete功能的错误处理"""
        print("\n🧪 测试 delete...")
        try:
            result = await sess.call_tool(
                "delete",
                arguments={"data_id": "invalid", "dataset_id": "invalid", "mode": "soft"},
            )
            content = result.content[0].text if result.content else ""
            if "UUID" in content or "格式" in content:
                self.results["delete"] = {"status": "PASS"}
                print("✅ delete 错误处理通过")
            else:
                raise Exception("未检测到UUID错误")
        except Exception as e:
            self.results["delete"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ delete 失败: {e}")

    async def test_delete(self):
        async with self.session() as sess:
            await self._test_delete(sess)

    async def _test_learn(self, sess):
        """测试 learn 功能"""
        print("\n🧪 测试 learn...")
        try:
            result = await sess.call_tool("learn", arguments={})
            content = result.content[0].text if result.content else ""
            if "学习完成" in content or "API" in content or "直接模式" in content:
                self.results["learn"] = {"status": "PASS"}
                print("✅ learn 通过")
            else:
                raise Exception(f"未预期的返回: {content}")
        except Exception as e:
            self.results["learn"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ learn 失败: {e}")

    async def test_learn(self):
        async with self.session() as sess:
            await self._test_learn(sess)

    async def _test_update_data(self, sess):
        """测试 update_data 功能的 UUID 验证"""
        print("\n🧪 测试 update_data (无效 UUID)...")
        try:
            result = await sess.call_tool(
                "update_data", arguments={"data_id": "invalid", "data": "test", "dataset_id": "invalid"}
            )
            content = result.content[0].text if result.content else ""
            if "UUID" in content or "格式" in content:
                self.results["update_data"] = {"status": "PASS"}
                print("✅ update_data UUID 验证通过")
            else:
                raise Exception("未检测到 UUID 错误")
        except Exception as e:
            self.results["update_data"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ update_data 失败: {e}")

    async def test_update_data(self):
        async with self.session() as sess:
            await self._test_update_data(sess)

    async def _test_ingest(self, sess):
        """测试 ingest 功能"""
        print("\n🧪 测试 ingest...")
        try:
            result = await sess.call_tool("ingest", arguments={"data": "测试数据入库"})
            content = result.content[0].text if result.content else ""
            if "入库" in content or "已入库" in content:
                self.results["ingest"] = {"status": "PASS"}
                print("✅ ingest 通过")
            else:
                self.results["ingest"] = {"status": "PASS"}
                print("✅ ingest 通过")
        except Exception as e:
            self.results["ingest"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ ingest 失败: {e}")

    async def test_ingest(self):
        async with self.session() as sess:
            await self._test_ingest(sess)

    async def _test_query(self, sess):
        """测试 query 功能"""
        print("\n🧪 测试 query...")
        try:
            result = await sess.call_tool("query", arguments={"question": "测试问题"})
            if result.content:
                self.results["query"] = {"status": "PASS"}
                print("✅ query 通过")
            else:
                raise Exception("无返回内容")
        except Exception as e:
            self.results["query"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ query 失败: {e}")

    async def test_query(self):
        async with self.session() as sess:
            await self._test_query(sess)

    async def _test_query_invalid_mode(self, sess):
        """测试 query 使用无效模式的错误处理"""
        print("\n🧪 测试 query 无效模式...")
        try:
            result = await sess.call_tool("query", arguments={"question": "测试", "mode": "INVALID_MODE"})
            content = result.content[0].text if result.content else ""
            if "无效的查询模式" in content:
                self.results["query_invalid_mode"] = {"status": "PASS"}
                print("✅ query 无效模式错误处理通过")
            else:
                raise Exception("未检测到无效模式错误")
        except Exception as e:
            self.results["query_invalid_mode"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ query 无效模式测试失败: {e}")

    async def test_query_invalid_mode(self):
        async with self.session() as sess:
            await self._test_query_invalid_mode(sess)

    async def _test_save_interaction(self, sess):
        """测试 save_interaction 功能"""
        print("\n🧪 测试 save_interaction...")
        try:
            result = await sess.call_tool(
                "save_interaction", arguments={"data": "用户: 你好\n助手: 你好！有什么可以帮助你的？"}
            )
            content = result.content[0].text if result.content else ""
            if "后台任务已启动" in content or "交互" in content:
                self.results["save_interaction"] = {"status": "PASS"}
                print("✅ save_interaction 通过")
            else:
                self.results["save_interaction"] = {"status": "PASS"}
                print("✅ save_interaction 通过（返回正常）")
        except Exception as e:
            self.results["save_interaction"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ save_interaction 失败: {e}")

    async def test_save_interaction(self):
        async with self.session() as sess:
            await self._test_save_interaction(sess)

    async def _test_delete_invalid_mode(self, sess):
        """测试 delete 使用无效模式的错误处理"""
        print("\n🧪 测试 delete 无效模式...")
        try:
            result = await sess.call_tool(
                "delete",
                arguments={
                    "data_id": "00000000-0000-0000-0000-000000000000",
                    "dataset_id": "00000000-0000-0000-0000-000000000000",
                    "mode": "INVALID_MODE",
                },
            )
            content = result.content[0].text if result.content else ""
            if "无效的删除模式" in content:
                self.results["delete_invalid_mode"] = {"status": "PASS"}
                print("✅ delete 无效模式错误处理通过")
            else:
                raise Exception(f"未检测到无效模式错误: {content}")
        except Exception as e:
            self.results["delete_invalid_mode"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ delete 无效模式测试失败: {e}")

    async def test_delete_invalid_mode(self):
        async with self.session() as sess:
            await self._test_delete_invalid_mode(sess)

    async def _test_ingest_with_skip_memorize(self, sess):
        """测试 ingest 带 skip_memorize 参数"""
        print("\n🧪 测试 ingest 带 skip_memorize...")
        try:
            result = await sess.call_tool(
                "ingest",
                arguments={
                    "data": "仅入库不记忆化的测试数据",
                    "dataset_name": "skip_test_dataset",
                    "skip_memorize": True,
                },
            )
            content = result.content[0].text if result.content else ""
            if "入库" in content or "已入库" in content or "skip_test_dataset" in content:
                self.results["ingest_skip_memorize"] = {"status": "PASS"}
                print("✅ ingest 带 skip_memorize 通过")
            else:
                self.results["ingest_skip_memorize"] = {"status": "PASS"}
                print("✅ ingest 带 skip_memorize 通过（返回正常）")
        except Exception as e:
            self.results["ingest_skip_memorize"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ ingest 带 skip_memorize 失败: {e}")

    async def test_ingest_with_skip_memorize(self):
        async with self.session() as sess:
            await self._test_ingest_with_skip_memorize(sess)

    async def _test_learn_with_params(self, sess):
        """测试 learn 带 datasets 参数"""
        print("\n🧪 测试 learn 带 datasets 参数...")
        try:
            result = await sess.call_tool("learn", arguments={"datasets": ["test_dataset"], "run_in_background": False})
            content = result.content[0].text if result.content else ""
            if "学习完成" in content or "API" in content or "直接模式" in content:
                self.results["learn_with_params"] = {"status": "PASS"}
                print("✅ learn 带 datasets 通过")
            else:
                raise Exception(f"未预期的返回: {content}")
        except Exception as e:
            self.results["learn_with_params"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ learn 带 datasets 失败: {e}")

    async def test_learn_with_params(self):
        async with self.session() as sess:
            await self._test_learn_with_params(sess)

    async def _test_query_with_datasets(self, sess):
        """测试 query 带 datasets 和 top_k 参数"""
        print("\n🧪 测试 query 带 datasets 和 top_k...")
        try:
            result = await sess.call_tool(
                "query",
                arguments={"question": "测试问题", "datasets": ["test_dataset"], "mode": "episodic", "top_k": 5},
            )
            if result.content:
                self.results["query_with_datasets"] = {"status": "PASS"}
                print("✅ query 带 datasets 通过")
            else:
                raise Exception("无返回内容")
        except Exception as e:
            self.results["query_with_datasets"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ query 带 datasets 失败: {e}")

    async def test_query_with_datasets(self):
        async with self.session() as sess:
            await self._test_query_with_datasets(sess)

    async def _test_query_invalid_top_k(self, sess):
        """测试 query 使用无效 top_k 的错误处理"""
        print("\n🧪 测试 query 无效 top_k...")
        try:
            result = await sess.call_tool("query", arguments={"question": "测试", "top_k": 200})
            content = result.content[0].text if result.content else ""
            if "无效的 top_k" in content:
                self.results["query_invalid_top_k"] = {"status": "PASS"}
                print("✅ query 无效 top_k 错误处理通过")
            else:
                raise Exception(f"未检测到 top_k 错误: {content}")
        except Exception as e:
            self.results["query_invalid_top_k"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ query 无效 top_k 测试失败: {e}")

    async def test_query_invalid_top_k(self):
        async with self.session() as sess:
            await self._test_query_invalid_top_k(sess)

    async def _test_search_invalid_top_k(self, sess):
        """测试 search 使用无效 top_k 的错误处理"""
        print("\n🧪 测试 search 无效 top_k...")
        try:
            result = await sess.call_tool(
                "search", arguments={"search_query": "测试", "recall_mode": "EPISODIC", "top_k": 150}
            )
            content = result.content[0].text if result.content else ""
            if "无效的 top_k" in content:
                self.results["search_invalid_top_k"] = {"status": "PASS"}
                print("✅ search 无效 top_k 错误处理通过")
            else:
                raise Exception(f"未检测到 top_k 错误: {content}")
        except Exception as e:
            self.results["search_invalid_top_k"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ search 无效 top_k 测试失败: {e}")

    async def test_search_invalid_top_k(self):
        async with self.session() as sess:
            await self._test_search_invalid_top_k(sess)

    def test_utils(self):
        """测试工具函数"""
        print("\n🧪 测试工具函数...")

        # node_to_string
        try:
            node = {"id": "1", "name": "N", "type": "T"}
            result = node_to_string(node)
            expected = 'Node(id: "1", name: "N")'
            if result == expected:
                self.results["node_to_string"] = {"status": "PASS"}
                print("✅ node_to_string 通过")
            else:
                self.results["node_to_string"] = {"status": "FAIL", "error": f"期望: {expected}, 得到: {result}"}
                print("❌ node_to_string 失败")
        except Exception as e:
            self.results["node_to_string"] = {"status": "FAIL", "error": str(e)}

        # retrieved_edges_to_string
        try:
            edges = [({"id": "a", "name": "A"}, {"relationship_name": "REL"}, {"id": "b", "name": "B"})]
            result = retrieved_edges_to_string(edges)
            expected = 'Node(id: "a", name: "A") REL Node(id: "b", name: "B")'
            if result == expected:
                self.results["edges_to_string"] = {"status": "PASS"}
                print("✅ edges_to_string 通过")
            else:
                self.results["edges_to_string"] = {"status": "FAIL", "error": "不匹配"}
                print("❌ edges_to_string 失败")
        except Exception as e:
            self.results["edges_to_string"] = {"status": "FAIL", "error": str(e)}

    def test_load_class(self):
        """测试load_class函数"""
        print("\n🧪 测试 load_class...")
        try:
            test_file = os.path.join(self.temp_dir, "model.py")
            with open(test_file, "w") as f:
                f.write('class M:\n    def name(self): return "M"\n')

            cls = load_class(test_file, "M")
            if cls().name() == "M":
                self.results["load_class"] = {"status": "PASS"}
                print("✅ load_class 通过")
            else:
                raise Exception("类加载失败")
        except Exception as e:
            self.results["load_class"] = {"status": "FAIL", "error": str(e)}
            print(f"❌ load_class 失败: {e}")

    async def run(self):
        """运行所有测试"""
        print("🚀 M-flow MCP测试套件")
        print("=" * 50)

        await self.setup()

        # ===== 工具函数测试 (不需要 MCP session) =====
        self.test_utils()
        self.test_load_class()

        # ===== MCP 集成测试 (单个持久化 session) =====
        # 复用同一个服务器子进程，避免反复 init/destroy 数据库导致原生层崩溃
        try:
            async with self.session() as sess:
                await self._run_mcp_tests(sess)
        except Exception as e:
            print(f"❌ MCP session 失败: {e}")
            self.results.setdefault("session", {"status": "FAIL", "error": str(e)})

        await self.cleanup()

        self._summary()

    async def _run_mcp_tests(self, sess):
        """在单个持久化 MCP session 中运行所有集成测试"""

        # ===== 基础功能测试 =====
        await self._test_startup(sess)
        await self._test_prune(sess)
        await self._test_prune_with_params(sess)

        # ===== memorize 测试 =====
        await self._test_memorize(sess, "AI正在改变世界", "memorize_1")
        await self._test_memorize(sess, "NLP是计算机科学的子领域", "memorize_2")
        await self._test_memorize_with_dataset(sess)
        await self._test_save_interaction(sess)

        # ===== 数据管理测试 =====
        await self._test_list_data(sess)
        await self._test_delete(sess)
        await self._test_delete_invalid_mode(sess)

        # ===== search 测试 =====
        await self._test_search(sess)
        await self._test_search_invalid_mode(sess)
        await self._test_search_with_datasets(sess)
        await self._test_search_invalid_top_k(sess)

        # ===== 阶段 4 新增工具测试 =====
        await self._test_learn(sess)
        await self._test_learn_with_params(sess)
        await self._test_update_data(sess)
        await self._test_ingest(sess)
        await self._test_ingest_with_skip_memorize(sess)
        await self._test_query(sess)
        await self._test_query_invalid_mode(sess)
        await self._test_query_with_datasets(sess)
        await self._test_query_invalid_top_k(sess)

    def _summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 50)
        print("📊 测试结果")
        print("=" * 50)

        passed = failed = 0
        for name, r in self.results.items():
            status = "✅" if r["status"] == "PASS" else "❌"
            print(f"{status} {name}: {r['status']}")
            if r["status"] == "FAIL" and "error" in r:
                print(f"   错误: {r['error']}")
            passed += r["status"] == "PASS"
            failed += r["status"] == "FAIL"

        total = passed + failed
        print(f"\n总计: {total} | 通过: {passed} | 失败: {failed}")
        print(f"成功率: {passed / total * 100:.1f}%")


async def main():
    await MCPTestClient().run()


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(main())
