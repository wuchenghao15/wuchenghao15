#!/usr/bin/env python3
"""
初始化本地存储表
"""

import os
import sys
from app.models.local_storage import LocalStorage
from app.utils.logging import logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        logger.info("开始初始化本地存储表...")
        
        # 创建本地存储表
        success = LocalStorage.create_table()
        if success:
            logger.info("本地存储表创建成功")
        else:
            logger.error("本地存储表创建失败")
            sys.exit(1)
        
        # 测试本地存储功能
        logger.info("测试本地存储功能...")
        
        # 测试设置值
        test_key = "test_key"
        test_value = "test_value"
        success = LocalStorage.set(test_key, test_value)
        if success:
            logger.info(f"设置值成功: {test_key} = {test_value}")
        else:
            logger.error("设置值失败")
            sys.exit(1)
        
        # 测试获取值
        retrieved_value = LocalStorage.get(test_key)
        if retrieved_value == test_value:
            logger.info(f"获取值成功: {test_key} = {retrieved_value}")
        else:
            logger.error(f"获取值失败: 期望 {test_value}, 实际 {retrieved_value}")
            sys.exit(1)
        
        # 测试删除值
        success = LocalStorage.remove(test_key)
        if success:
            logger.info(f"删除值成功: {test_key}")
        else:
            logger.error("删除值失败")
            sys.exit(1)
        
        # 测试获取已删除的值
        retrieved_value = LocalStorage.get(test_key)
        if retrieved_value is None:
            logger.info(f"获取已删除值成功: {test_key} = {retrieved_value}")
        else:
            logger.error(f"获取已删除值失败: 期望 None, 实际 {retrieved_value}")
            sys.exit(1)
        
        logger.info("本地存储功能测试完成，所有测试通过！")
        sys.exit(0)
    except Exception as e:
        logger.error(f"初始化本地存储失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
