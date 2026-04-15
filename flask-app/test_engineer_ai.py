#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工程师AI功能
"""

import os
import sys
import logging
from app.ai.engineer_ai import EngineerAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_engineer_ai')

def test_engineer_ai():
    """测试工程师AI"""
    try:
        logger.info("开始测试工程师AI...")
        
        # 创建工程师AI实例
        engineer_ai = EngineerAI('test-engineer-ai')
        
        # 初始化工程师AI
        logger.info("初始化工程师AI...")
        if engineer_ai.initialize():
            logger.info("工程师AI初始化成功")
        else:
            logger.error("工程师AI初始化失败")
            return False
        
        # 测试错误检测和修复
        logger.info("测试错误检测和修复...")
        test_error = "404 Not Found: The requested URL was not found on the server."
        fix_result = engineer_ai.detect_and_fix_errors(test_error)
        logger.info(f"错误修复结果: {fix_result}")
        
        # 测试维护建议
        logger.info("测试维护建议...")
        suggestions = engineer_ai.provide_maintenance_suggestions()
        logger.info("维护建议:")
        for suggestion in suggestions:
            logger.info(f"- {suggestion['title']}: {suggestion['description']} (优先级: {suggestion['priority']})")
        
        # 测试知识库
        logger.info("测试知识库...")
        knowledge_base = engineer_ai.get_knowledge_base()
        logger.info(f"知识库类别: {list(knowledge_base.keys())}")
        for category, items in knowledge_base.items():
            logger.info(f"{category} 类别包含 {len(items)} 项知识")
        
        # 测试修复历史
        logger.info("测试修复历史...")
        fix_history = engineer_ai.get_fix_history()
        logger.info(f"修复历史记录数: {len(fix_history)}")
        for i, fix in enumerate(fix_history):
            logger.info(f"修复记录 {i+1}: {fix['type']} - {fix['issue']} (状态: {fix['status']})")
        
        # 关闭工程师AI
        logger.info("关闭工程师AI...")
        engineer_ai.shutdown()
        logger.info("工程师AI测试完成")
        return True
    except Exception as e:
        logger.error(f"测试工程师AI时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 测试工程师AI
    success = test_engineer_ai()
    if success:
        logger.info("工程师AI测试成功")
    else:
        logger.error("工程师AI测试失败")
        sys.exit(1)