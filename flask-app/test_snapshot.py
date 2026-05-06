#!/usr/bin/env python3
"""
测试用户快照功能

from app.models.user_snapshots import UserSnapshot

print("开始测试用户快照功能...")

# 1. 创建快照表
UserSnapshot.create_table()
print("1. 快照表创建成功")

# 2. 创建快照
test_user_id = "test_user_123"
test_session_id = "test_session_456"
test_data = {
    "key1": "value1",
    "key2": "value2",
    "key3": ["item1", "item2", "item3"],
    "key4": {"subkey1": "subvalue1", "subkey2": "subvalue2"}
}

print(f"\n2. 创建测试快照，用户ID: {test_user_id}, 会话ID: {test_session_id}")
snapshot = UserSnapshot.create(
    user_id=test_user_id,
    session_id=test_session_id,
    snapshot_type="test_snapshot",
    data=test_data,
    metadata={"test": "metadata"}
)
print(f"   快照创建成功，ID: {snapshot.snapshot_id}, 大小: {snapshot.size}字节, 压缩: {'是' if snapshot.compressed else '否'}")

# 3. 通过ID查询快照
print(f"\n3. 通过ID查询快照: {snapshot.snapshot_id}")
fetched_snapshot = UserSnapshot.get_by_id(snapshot.snapshot_id)
if fetched_snapshot:
    print(f"   查询成功，快照ID: {fetched_snapshot.snapshot_id}, 用户ID: {fetched_snapshot.user_id}")
    print(f"   数据内容: {fetched_snapshot.data}")

# 4. 通过会话ID查询快照
print(f"\n4. 通过会话ID查询快照: {test_session_id}")
snapshots_by_session = UserSnapshot.get_by_session(test_session_id)
print(f"   查询到 {len(snapshots_by_session)} 个快照")

# 5. 通过用户ID查询快照
print(f"\n5. 通过用户ID查询快照: {test_user_id}")
snapshots_by_user = UserSnapshot.get_by_user(test_user_id)
print(f"   查询到 {len(snapshots_by_user)} 个快照")

# 6. 获取最新快照
print(f"\n6. 获取最新快照")
latest_snapshots = UserSnapshot.get_latest(limit=5)
print(f"   查询到 {len(latest_snapshots)} 个最新快照")

# 7. 测试快照恢复功能
print(f"\n7. 测试快照恢复功能")
restore_result = snapshot.restore()
if restore_result:
    print(f"   快照恢复成功，当前状态: {snapshot.status}")

# 8. 获取已恢复的快照
print(f"\n8. 获取已恢复的快照")
restored_snapshots = UserSnapshot.get_restored_snapshots()
print(f"   查询到 {len(restored_snapshots)} 个已恢复快照")

# 9. 测试快照归档功能
print(f"\n9. 测试快照归档功能")
archive_result = snapshot.archive()
if archive_result:
    print(f"   快照归档成功，当前状态: {snapshot.status}")

# 10. 测试快照删除功能
print(f"\n10. 测试快照删除功能")
delete_result = snapshot.delete()
if delete_result:
    print(f"   快照删除成功")

# 验证删除结果
fetched_after_delete = UserSnapshot.get_by_id(snapshot.snapshot_id)
if not fetched_after_delete:
    print(f"   验证通过，快照已成功删除")

print("\n所有测试完成！")

"""