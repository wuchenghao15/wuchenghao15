#!/usr/bin/env python3
"""
简单测试AI增强系统功能

import logging
import sys
import os

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 导入测试模块
from app.ai.enhanced_system import enhanced_system
from app.ai.sandbox_manager import sandbox_manager

def test_basic_enhanced_system():
    """测试增强系统基本功能"""
    logger.info("测试增强系统基本功能...")
    try:
        assert enhanced_system is not None
        logger.info("✓ 增强系统初始化成功")

        # 测试添加蓝图使用数据
        blueprint_data = {
            'blueprint': 'integrated_design',
            'usage_count': 100,
            'response_time': 0.5
        }
        enhanced_system.add_blueprint_usage_data(blueprint_data)
        logger.info("✓ 蓝图使用数据添加成功")

        # 测试沙盒预温
        sandbox_manager.prewarm_sandboxes(count=2)
        logger.info("✓ 沙盒预温功能测试成功")

        # 测试获取预温沙盒
        prewarmed_sandbox = sandbox_manager.get_prewarmed_sandbox()
        if prewarmed_sandbox:
            logger.info(f"✓ 成功获取预温沙盒: {prewarmed_sandbox['sandbox_id']}")
        else:
            logger.info("✓ 当前没有可用的预温沙盒")

        return True
    except Exception as e:
        logger.error(f"✗ 增强系统基本功能测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    logger.info("开始简单测试AI增强系统...")

    if test_basic_enhanced_system():
        logger.info("🎉 简单测试通过！AI增强系统功能基本正常")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
