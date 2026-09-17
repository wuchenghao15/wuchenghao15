"""
按ID删除测试 - 测试删除端点的权限和数据隔离
"""

from __future__ import annotations

import asyncio
import os
import pathlib
from uuid import uuid4

import m_flow
from m_flow.adapters.graph import get_graph_provider
from m_flow.api.v1.exceptions import DatasetNotFoundError, DocumentNotFoundError
from m_flow.auth.exceptions import PermissionDeniedError
from m_flow.auth.methods import create_user, get_seed_user
from m_flow.auth.permissions.methods import authorized_give_permission_on_datasets
from m_flow.data.methods import fetch_dataset_items, get_datasets_by_name
from m_flow.data.models import Dataset
from m_flow.shared.logging_utils import get_logger

log = get_logger()

_TEXTS = {
    "apple": "Apple Inc.是美国跨国科技公司，专注于消费电子、软件和在线服务。自2021年起成为全球最有价值的公司。",
    "microsoft": "Microsoft Corporation是美国跨国科技公司，生产计算机软件、消费电子产品和相关服务。其最著名的产品是Windows操作系统和Office套件。",
    "google": "Google LLC是美国跨国科技公司，专注于互联网相关服务和产品，包括在线广告技术、搜索引擎、云计算、软件和硬件。",
}


def _get_ds_id(result: dict):
    """从memorize结果提取数据集ID"""
    return next(iter(result.keys()), None)


async def run_delete_by_id_tests():
    """运行删除测试"""
    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "True"

    # 设置测试目录
    base = pathlib.Path(__file__).parent
    m_flow.config.data_root_directory(str(base / ".data_storage/test_delete_by_id"))
    m_flow.config.system_root_directory(str(base / ".mflow/system/test_delete_by_id"))

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    from m_flow.core.domain.operations.setup import setup

    await setup()

    print("🧪 删除端点测试")
    print("=" * 60)

    # 创建用户
    default_user = await get_seed_user()
    test_user = await create_user("test_delete@test.com", "test@test.com")
    iso_user = await create_user("isolation@test.com", "iso@test.com")

    # 添加数据
    await m_flow.add([_TEXTS["apple"]], dataset_name="ds1", user=default_user)
    await m_flow.add([_TEXTS["microsoft"]], dataset_name="ds2", user=test_user)
    await m_flow.add([_TEXTS["google"]], dataset_name="ds3", user=iso_user)

    r1 = await m_flow.memorize(["ds1"], user=default_user)
    r2 = await m_flow.memorize(["ds2"], user=test_user)
    r3 = await m_flow.memorize(["ds3"], user=iso_user)

    ds_id1, ds_id2, ds_id3 = _get_ds_id(r1), _get_ds_id(r2), _get_ds_id(r3)
    print(f"数据集: ds1={ds_id1}, ds2={ds_id2}, ds3={ds_id3}")

    data1 = await fetch_dataset_items(ds_id1)
    data2 = await fetch_dataset_items(ds_id2)
    data3 = await fetch_dataset_items(ds_id3)
    print(f"数据量: ds1={len(data1)}, ds2={len(data2)}, ds3={len(data3)}")

    data_id1 = data1[0].id if data1 else None
    data_id2 = data2[0].id if data2 else None

    ds1 = Dataset(id=ds_id1, name="ds1", owner_id=default_user.id)
    ds2 = Dataset(id=ds_id2, name="ds2", owner_id=test_user.id)

    # 测试1: 正常删除
    print("\n📝 测试1: 所有者删除自己的数据")
    r = await m_flow.delete(data_id=data_id1, dataset_id=ds1.id)
    assert r["status"] == "success"
    print("✅ 通过")

    # 测试2: 无权限删除
    print("\n📝 测试2: 无权限删除应失败")
    try:
        await m_flow.delete(data_id=data_id2, dataset_id=ds2.id, user=default_user)
        raise AssertionError("应抛出异常")
    except (PermissionDeniedError, DatasetNotFoundError):
        print("✅ 通过")

    # 测试3: 不存在的数据ID
    print("\n📝 测试3: 删除不存在的数据")
    try:
        await m_flow.delete(data_id=uuid4(), dataset_id=ds1.id, user=default_user)
        raise AssertionError
    except DocumentNotFoundError:
        print("✅ 通过")

    # 测试4: 不存在的数据集ID
    print("\n📝 测试4: 删除不存在的数据集")
    try:
        await m_flow.delete(data_id=data_id2, dataset_id=uuid4(), user=test_user)
        raise AssertionError
    except (DatasetNotFoundError, PermissionDeniedError):
        print("✅ 通过")

    # 测试5: 数据不属于指定数据集
    print("\n📝 测试5: 数据不在指定数据集中")
    await m_flow.add([_TEXTS["apple"]], dataset_name="other_ds", user=default_user)
    await m_flow.memorize(["other_ds"], user=default_user)
    other_dss = await get_datasets_by_name(["other_ds"], default_user.id)
    try:
        await m_flow.delete(data_id=data_id2, dataset_id=other_dss[0].id, user=default_user)
        raise AssertionError
    except DocumentNotFoundError:
        print("✅ 通过")

    # 测试6: 授权后删除
    print("\n📝 测试6: 授权后删除")
    await authorized_give_permission_on_datasets(default_user.id, [ds2.id], "delete", test_user.id)
    r = await m_flow.delete(data_id=data_id2, dataset_id=ds2.id, user=default_user)
    assert r["status"] == "success"
    print("✅ 通过")

    # 测试7: 图数据库状态
    print("\n📝 测试7: 图数据库状态检查")
    graph = await get_graph_provider()
    nodes, edges = await graph.get_graph_data()
    print(f"✅ 节点: {len(nodes)}, 边: {len(edges)}")

    # 测试8: 数据隔离
    print("\n📝 测试8: 隔离用户数据完整性")
    iso_data = await fetch_dataset_items(ds_id3)
    assert len(iso_data) == len(data3), "数据量不变"
    assert {str(d.id) for d in iso_data} == {str(d.id) for d in data3}, "数据ID不变"
    results = await m_flow.search("Google technology", user=iso_user)
    assert len(results) > 0, "数据可搜索"
    print("✅ 通过")

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_delete_by_id_tests())
