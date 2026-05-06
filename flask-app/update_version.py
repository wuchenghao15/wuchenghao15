#!/usr/bin/env python3
"""
系统版本更新脚本
用于升级系统版本号

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.logging import logger
from app.ai.version_manager import version_manager_ai

def update_system_version(new_version=None):
    升级系统版本号

    Args:
        new_version: 新的系统版本号，如果为None则自动递增
    try:
        logger.info("开始更新系统版本号...")

        # 获取当前版本信息
        current_versions = version_manager_ai.current_versions
        logger.info(f"当前版本: {current_versions}")

        if new_version is None:
            # 自动递增系统版本号（从1.0.0到1.1.0）
            system_version = current_versions['system_version']
            parts = list(map(int, system_version.split('.')))
            parts[1] += 1  # 递增中间位
            new_version = '.'.join(map(str, parts))

        # 更新系统版本号
        result = version_manager_ai.update_version('system_version', new_version)

        if result['success']:
            # 同时更新内部版本号
            internal_version = current_versions['internal_version']
            internal_parts = list(map(int, internal_version.split('.')))
            internal_parts[0] = int(new_version.split('.')[0])
            internal_parts[1] = int(new_version.split('.')[1])
            internal_parts[2] += 1  # 递增内部版本号的第三位
            new_internal_version = '.'.join(map(str, internal_parts))

            version_manager_ai.update_version('internal_version', new_internal_version)

            # 更新测试版本号
            new_test_version = f"{new_version}-beta"
            version_manager_ai.update_version('test_version', new_test_version)

            logger.info("系统版本号更新成功！")
            logger.info(f"新的系统版本: {new_version}")
            logger.info(f"新的内部版本: {new_internal_version}")
            logger.info(f"新的测试版本: {new_test_version}")

            return True
        else:
            logger.error(f"系统版本号更新失败: {result['message']}")
            return False

    except Exception as e:
        logger.error(f"更新系统版本号时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


    主函数
    success = update_system_version()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

"""