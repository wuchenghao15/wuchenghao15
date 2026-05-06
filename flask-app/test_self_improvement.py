#!/usr/bin/env python3
"""
测试AI自我提升系统

import logging
import os
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_self_improvement():
    """测试AI自我提升系统"""
    logger.info("开始测试AI自我提升系统...")

    try:
        # 导入AI自我提升系统
        from ai_self_improvement import get_ai_self_improvement

        # 获取AI自我提升系统实例
        ai_system = get_ai_self_improvement()
        logger.info("✓ 成功获取AI自我提升系统实例")

        # 启动AI自我提升系统
        ai_system.start()
        logger.info("✓ 成功启动AI自我提升系统")

        # 测试自动扩充知识库功能
        logger.info("✓ 开始测试自动扩充知识库功能...")
        ai_system.auto_expand_knowledge_base()
        logger.info("✓ 自动扩充知识库功能测试完成")

        # 测试自我修复功能
        logger.info("✓ 开始测试自我修复功能...")
        ai_system.self_repair()
        logger.info("✓ 自我修复功能测试完成")

        # 测试学习新技能功能
        logger.info("✓ 开始测试学习新技能功能...")
        ai_system.learn_new_skills()
        logger.info("✓ 学习新技能功能测试完成")

        # 测试升级组件功能
        logger.info("✓ 开始测试升级组件功能...")
        ai_system.upgrade_components()
        logger.info("✓ 升级组件功能测试完成")

        # 测试管理子AI功能
        logger.info("✓ 开始测试管理子AI功能...")
        ai_system.manage_child_ais()
        logger.info("✓ 管理子AI功能测试完成")

        # 测试能力评估功能
        logger.info("✓ 开始测试能力评估功能...")
        capabilities = ai_system.assess_capabilities()
        logger.info(f"✓ 能力评估功能测试完成，共评估{len(capabilities)}项能力")
        for cap in capabilities:
            logger.info(f"  - {cap['capability']}: {cap['score']:.2f}")

        # 停止AI自我提升系统
        ai_system.stop()
        logger.info("✓ 成功停止AI自我提升系统")

        logger.info("✓ 所有测试通过！")
        return True
    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_ai_self_improvement()
