#!/usr/bin/env python3
# MTSCOS AI Project 缓存系统测试脚本
"""
测试缓存系统的基本功能

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.filesystem import file_system
from app.utils.logging import logger


def test_system_upgrade_cache():
    测试系统升级包缓存
    print("=== 测试系统升级包缓存 ===")

    # 测试系统升级包缓存设置
    version = "1.0.0"
    upgrade_data = {
        "files": ["file1.txt", "file2.txt"],
        "size": 1024,
        "checksum": "abc123def456"
    }

    print(f"设置系统升级包缓存: 版本 {version}")
    result = file_system.set_system_upgrade_cache(version, upgrade_data)
    print(f"✓ 系统升级包缓存设置: {'成功' if result else '失败'}")

    # 测试系统升级包缓存获取
    print(f"获取系统升级包缓存: 版本 {version}")
    cached_data = file_system.get_system_upgrade_cache(version)
    print(f"✓ 系统升级包缓存获取: {'成功' if cached_data == upgrade_data else '失败'}")

    # 测试列出系统升级包缓存
    print("列出所有系统升级包缓存")
    upgrades = file_system.list_system_upgrade_caches()
    print(f"✓ 列出系统升级包缓存: {'成功' if len(upgrades) > 0 else '失败'}")
    print(f"  系统升级包缓存数量: {len(upgrades)}")

    # 测试系统升级包缓存删除
    print(f"删除系统升级包缓存: 版本 {version}")
    result = file_system.delete_system_upgrade_cache(version)
    print(f"✓ 系统升级包缓存删除: {'成功' if result else '失败'}")

    # 验证删除
    cached_data = file_system.get_system_upgrade_cache(version)
    print(f"✓ 删除验证: {'成功' if cached_data is None else '失败'}")



def test_user_file_cache():
    测试用户文件缓存
    print("=== 测试用户文件缓存 ===")

    # 测试用户文件缓存设置
    user_id = "test_user"
    file_id = "file_123"
    file_data = {
        "name": "test.txt",
        "content": "这是测试文件内容",
        "size": 100,
        "type": "text/plain"
    }

    print(f"设置用户文件缓存: 用户 {user_id}, 文件 {file_id}")
    result = file_system.set_user_file_cache(user_id, file_id, file_data)
    print(f"✓ 用户文件缓存设置: {'成功' if result else '失败'}")
    # 测试用户文件缓存获取
    print(f"获取用户文件缓存: 用户 {user_id}, 文件 {file_id}")
    cached_data = file_system.get_user_file_cache(user_id, file_id)
    print(f"✓ 用户文件缓存获取: {'成功' if cached_data == file_data else '失败'}")

    # 测试列出用户文件缓存
    print(f"列出用户 {user_id} 的文件缓存")
    files = file_system.list_user_file_caches(user_id)
    print(f"✓ 列出用户文件缓存: {'成功' if len(files) > 0 else '失败'}")
    print(f"  用户文件缓存数量: {len(files)}")

    # 测试用户文件缓存删除
    print(f"删除用户文件缓存: 用户 {user_id}, 文件 {file_id}")
    result = file_system.delete_user_file_cache(user_id, file_id)
    print(f"✓ 用户文件缓存删除: {'成功' if result else '失败'}")

    # 验证删除
    cached_data = file_system.get_user_file_cache(user_id, file_id)
    print(f"✓ 删除验证: {'成功' if cached_data is None else '失败'}")

    print("=== 用户文件缓存测试完成 ===\n")


    测试缓存统计信息
    print("获取缓存统计信息")
    stats = file_system.get_cache_stats()
    print(f"✓ 缓存统计信息获取: {'成功' if isinstance(stats, dict) else '失败'}")

    print("  缓存统计信息:")
    print(f"  - 系统缓存文件数量: {stats['system_cache']['file_count']}")
    print(f"  - 系统缓存总大小: {stats['system_cache']['total_size']} 字节")
    print(f"  - 用户缓存文件数量: {stats['user_cache']['file_count']}")
    print(f"  - 用户缓存总大小: {stats['user_cache']['total_size']} 字节")
    print(f"  - 用户数量: {stats['user_cache']['user_count']}")
    print(f"  - 总缓存大小: {stats['total_cache_size']} 字节")

    print("=== 缓存统计信息测试完成 ===\n")


def test_cache_expiry():
    测试缓存过期功能
    print("=== 测试缓存过期功能 ===")

    # 设置一个短期过期的缓存
    version = "expiry_test"
    upgrade_data = {
        "files": ["test.txt"],
        "size": 100
    }

    # 设置1秒后过期
    print(f"设置短期过期缓存: 版本 {version}, 过期时间 1秒")
    result = file_system.set_system_upgrade_cache(version, upgrade_data, expiry=1)
    print(f"✓ 短期过期缓存设置: {'成功' if result else '失败'}")
    # 立即获取，应该存在
    print("立即获取缓存")
    cached_data = file_system.get_system_upgrade_cache(version)

    # 等待2秒，让缓存过期
    print("等待2秒，让缓存过期")
    time.sleep(2)

    # 再次获取，应该不存在
    print("过期后获取缓存")
    cached_data = file_system.get_system_upgrade_cache(version)
    print(f"✓ 缓存过期验证: {'成功' if cached_data is None else '失败'}")



def test_clear_cache():
    测试清空缓存功能
    print("=== 测试清空缓存功能 ===")

    # 先设置一些测试数据
    file_system.set_system_upgrade_cache("clear_test_1", {"test": "data1"})
    file_system.set_user_file_cache("test_user", "file_456", {"test": "data3"})

    # 获取初始统计信息
    initial_stats = file_system.get_cache_stats()

    # 测试清空系统缓存
    print("清空系统缓存")
    result = file_system.clear_cache("system")
    print(f"✓ 清空系统缓存: {'成功' if result else '失败'}")

    # 验证系统缓存已清空
    after_system_clear_stats = file_system.get_cache_stats()
    print(f"✓ 系统缓存清空验证: {'成功' if after_system_clear_stats['system_cache']['file_count'] == 0 else '失败'}")

    # 测试清空用户缓存
    print("清空用户缓存")
    result = file_system.clear_cache("user")
    print(f"✓ 清空用户缓存: {'成功' if result else '失败'}")

    # 验证用户缓存已清空
    after_user_clear_stats = file_system.get_cache_stats()
    print(f"✓ 用户缓存清空验证: {'成功' if after_user_clear_stats['user_cache']['file_count'] == 0 else '失败'}")

    print("=== 清空缓存功能测试完成 ===\n")


def main():
    主测试函数
    print("MTSCOS AI Project 缓存系统测试脚本")
    print("=" * 50)

    try:
        # 初始化文件系统
        print("初始化文件系统...")
        file_system.initialize()
        print("✓ 文件系统初始化完成")
        print()

        # 运行各项测试
        test_system_upgrade_cache()
        test_user_file_cache()
        test_cache_stats()
        test_cache_expiry()
        test_clear_cache()

        print("=" * 50)
        print("✓ 所有缓存测试完成！")
        print("缓存系统工作正常")

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        logger.error(f"缓存系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""