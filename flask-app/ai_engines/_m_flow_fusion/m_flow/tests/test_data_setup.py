"""
测试数据准备脚本
================
m_flow.tests.test_data_setup

提供测试数据的创建和清理功能，支持隔离的测试环境。

使用方法:
    # 准备测试数据
    python -m m_flow.tests.test_data_setup

    # 清理测试数据
    python -m m_flow.tests.test_data_setup cleanup

    # 获取测试运行 ID
    python -m m_flow.tests.test_data_setup --get-run-id
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime


def get_test_run_id() -> str:
    """
    生成唯一的测试运行 ID，用于并行测试隔离。

    Returns:
        str: 格式为 run_{timestamp}_{uuid[:8]} 的唯一标识
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"run_{timestamp}_{unique_id}"


def get_isolated_dataset_name(base_name: str, run_id: str | None = None) -> str:
    """
    生成隔离的测试数据集名称。

    Args:
        base_name: 基础数据集名称
        run_id: 可选的测试运行 ID

    Returns:
        str: 格式为 test_{run_id}_{base_name} 或 test_{base_name}
    """
    if run_id:
        return f"test_{run_id}_{base_name}"
    return f"test_{base_name}"


async def setup_test_data(run_id: str | None = None):
    """
    准备测试数据

    Args:
        run_id: 可选的测试运行 ID，用于并行测试隔离
    """
    import m_flow
    from m_flow import add, memorize

    # 验证环境
    mflow_env = os.environ.get("MFLOW_ENV", "")
    if mflow_env != "test":
        print("⚠️  警告: MFLOW_ENV 未设置为 'test'，建议在测试环境中运行")

    # 创建测试数据集
    base_datasets = ["basic", "edge", "performance"]

    print(f"🔧 准备测试数据 (run_id: {run_id or 'default'})...")

    for base_name in base_datasets:
        ds_name = get_isolated_dataset_name(base_name, run_id)

        content = f"""
这是 {ds_name} 的测试内容，用于自动化测试。

关键概念:
- 测试用例验证: 确保系统功能正常
- 知识图谱构建: 验证实体和关系提取
- 向量搜索: 验证语义检索能力

测试人员: 自动化测试框架
创建时间: {datetime.now().isoformat()}
"""

        try:
            await add(content, dataset_name=ds_name)
            print(f"  ✅ 创建数据集: {ds_name}")
        except Exception as e:
            print(f"  ❌ 创建数据集失败 {ds_name}: {e}")
            continue

    # 执行 memorize 处理
    # 测试数据是简单文本，禁用 content_routing 避免需要声明 content_type
    try:
        test_datasets = [get_isolated_dataset_name(n, run_id) for n in base_datasets]
        print("🔄 执行 memorize 处理...")
        await memorize(datasets=test_datasets, enable_content_routing=False)
        print("  ✅ Memorize 完成")
    except Exception as e:
        print(f"  ⚠️  Memorize 部分失败 (某些数据集可能不存在): {e}")

    print("\n✅ 测试数据准备完成")


async def cleanup_test_data(run_id: str | None = None, force: bool = False):
    """
    清理测试数据

    Args:
        run_id: 可选的测试运行 ID，仅清理该 ID 的数据
        force: 是否强制清理所有 test_ 前缀的数据
    """
    try:
        from m_flow.adapters.graph.get_graph_adapter import get_graph_provider
        from m_flow.adapters.vector.get_vector_adapter import get_vector_provider
        from m_flow.adapters.relational.get_db_adapter import get_db_adapter
    except ImportError as e:
        print(f"❌ 无法导入必要模块: {e}")
        print("   请确保已安装 m_flow 包")
        return

    print(f"🧹 清理测试数据 (run_id: {run_id or 'all test_*'})...")

    try:
        rel_engine = get_db_adapter()

        from sqlalchemy import select
        from m_flow.core.domain.models import Dataset

        session = rel_engine.get_session()

        # 构建查询条件
        if run_id:
            pattern = f"test_{run_id}_%"
        else:
            pattern = "test_%"

        result = session.execute(select(Dataset).where(Dataset.name.like(pattern)))
        test_datasets = result.scalars().all()

        if not test_datasets:
            print("  ℹ️  没有找到需要清理的测试数据集")
            session.close()
            return

        cleaned_count = 0
        for ds in test_datasets:
            try:
                # 1. 清理图数据库中的节点
                graph_engine = await get_graph_provider()
                if hasattr(graph_engine, "query"):
                    try:
                        await graph_engine.query(
                            "MATCH (n) WHERE n.dataset_id = $ds_id DETACH DELETE n", {"ds_id": str(ds.id)}
                        )
                    except Exception as ge:
                        print(f"    ⚠️  图数据库清理失败 {ds.name}: {ge}")

                # 2. 清理向量库中的向量
                vector_engine = get_vector_provider()
                if hasattr(vector_engine, "delete_by_dataset"):
                    try:
                        await vector_engine.delete_by_dataset(str(ds.id))
                    except Exception as ve:
                        print(f"    ⚠️  向量库清理失败 {ds.name}: {ve}")

                # 3. 删除数据集记录
                session.delete(ds)
                cleaned_count += 1
                print(f"  ✅ 清理数据集: {ds.name}")

            except Exception as e:
                print(f"  ❌ 清理数据集失败 {ds.name}: {e}")

        session.commit()
        session.close()

        print(f"\n✅ 清理了 {cleaned_count} 个测试数据集")

    except Exception as e:
        print(f"❌ 清理过程出错: {e}")
        import traceback

        traceback.print_exc()


async def verify_test_data(run_id: str | None = None) -> bool:
    """
    验证测试数据是否存在

    Args:
        run_id: 可选的测试运行 ID

    Returns:
        bool: 测试数据是否完整
    """
    try:
        from m_flow.adapters.relational.get_db_adapter import get_db_adapter
        from sqlalchemy import select, func
        from m_flow.core.domain.models import Dataset

        rel_engine = get_db_adapter()
        session = rel_engine.get_session()

        if run_id:
            pattern = f"test_{run_id}_%"
        else:
            pattern = "test_%"

        result = session.execute(select(func.count()).select_from(Dataset).where(Dataset.name.like(pattern)))
        count = result.scalar()
        session.close()

        print(f"📊 测试数据集数量: {count}")
        return count > 0

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    """命令行入口"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        run_id = None

        # 解析参数
        if "--run-id" in sys.argv:
            idx = sys.argv.index("--run-id")
            if idx + 1 < len(sys.argv):
                run_id = sys.argv[idx + 1]

        if command == "cleanup":
            asyncio.run(cleanup_test_data(run_id))
        elif command == "verify":
            asyncio.run(verify_test_data(run_id))
        elif command == "--get-run-id":
            print(get_test_run_id())
        elif command == "setup":
            asyncio.run(setup_test_data(run_id))
        else:
            print(f"未知命令: {command}")
            print("用法: python -m m_flow.tests.test_data_setup [setup|cleanup|verify|--get-run-id] [--run-id ID]")
    else:
        asyncio.run(setup_test_data())


if __name__ == "__main__":
    main()
