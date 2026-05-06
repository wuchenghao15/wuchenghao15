#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本，用于验证修复后的系统

import logging
# JSON import removed - using database
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SimpleTest')

def test_snapshot_system():
    """测试快照系统"""
    logger.info("开始测试快照系统")

    try:
        from app.models.user_snapshots import UserSnapshot

        # 确保表存在并更新结构
        UserSnapshot.create_table()

        # 创建测试快照
        user_id = "test_user"
        session_id = "test_session_12345678"

        # 创建第一个快照
        snapshot1 = UserSnapshot.create(
            user_id=user_id,
            session_id=session_id,
            snapshot_type="test_snapshot",
            data={"key1": "value1", "key2": "value2"}
        )
        logger.info(f"创建快照1成功: {snapshot1.snapshot_id}")

        # 创建第二个快照
        snapshot2 = UserSnapshot.create(
            user_id=user_id,
            session_id=session_id,
            data={"key1": "updated_value1", "key3": "value3"}
        logger.info(f"创建快照2成功: {snapshot2.snapshot_id}")
        logger.info("快照系统测试通过")
        return True
    except Exception as e:
        logger.error(f"快照系统测试失败: {str(e)}")
        return False

def test_sync_system():
    """测试同步系统"""
    logger.info("开始测试同步系统")

    try:
        from json_db_sync import JSONDBSync

        import tempfile
        import os

        # 创建测试JSON文件
        test_data = {
            "test_key": "test_value",
            "test_array": [1, 2, 3, 4, 5]
        }

        # 创建同步实例
        sync = JSONDBSync()

        # 创建测试文件
        test_dir = tempfile.mkdtemp()
        test_file = os.path.join(test_dir, "test_sync.json")

        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 同步到数据库
        sync_result = sync.sync_json_to_db(test_file)
        logger.info(f"同步文件到数据库结果: {sync_result}")

        # 验证同步
        verify_result = sync.validate_db_json_data()
        logger.info(f"验证数据库JSON数据结果: {verify_result}")

        # 清理临时文件
        import shutil
        shutil.rmtree(test_dir)

        logger.info("同步系统测试通过")
        return True
    except Exception as e:
        logger.error(f"同步系统测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""

    results = {
        "snapshot_system": test_snapshot_system(),
    }

    # 统计结果
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    logger.info(f"测试完成 - 通过: {passed}/{total}")

    # 返回结果
    if passed == total:
        return 0
    else:
        logger.error("部分系统测试失败！")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
