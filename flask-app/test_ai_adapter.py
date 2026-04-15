#!/usr/bin/env python3
"""
测试AI数据库适配器功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db import db_manager
from app.utils.logging import logger

def test_db_connection():
    """测试数据库连接"""
    try:
        # 执行简单查询
        result = db_manager.fetch_one("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        if result:
            logger.info(f"数据库连接成功，找到表: {result[0]}")
            return True
        else:
            logger.error("数据库连接失败，未找到表")
            return False
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False

def test_ai_adapter():
    """测试AI数据库适配器"""
    try:
        # 导入AI数据库适配器管理器
        from app import ai_db_adapter_manager
        
        logger.info("AI数据库适配器管理器导入成功")
        
        # 测试获取数据库架构
        schema = ai_db_adapter_manager.get_database_schema()
        logger.info(f"获取数据库架构成功，找到 {len(schema)} 个表")
        
        # 打印前5个表名
        for i, table in enumerate(schema[:5]):
            logger.info(f"表 {i+1}: {table['name']}")
        
        # 测试查询分析
        query = "SELECT * FROM users WHERE is_active = 1"
        analysis = ai_db_adapter_manager.analyze_query(query)
        logger.info(f"查询分析成功: {analysis}")
        
        # 测试自然语言查询生成
        natural_query = "查找所有活跃用户"
        generated = ai_db_adapter_manager.generate_query(natural_query)
        logger.info(f"自然语言查询生成成功: {generated}")
        
        # 测试数据库优化
        optimization = ai_db_adapter_manager.optimize_database()
        logger.info(f"数据库优化成功: {optimization}")
        
        # 测试数据库监控
        monitoring = ai_db_adapter_manager.monitor_performance()
        logger.info(f"数据库监控成功: {monitoring}")
        
        # 测试AI深度适配
        deep_adapt = ai_db_adapter_manager.deep_adapt()
        logger.info(f"AI深度适配成功: {deep_adapt}")
        
        return True
    except Exception as e:
        logger.error(f"AI适配器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    logger.info("开始测试AI数据库适配器")
    
    # 测试数据库连接
    if not test_db_connection():
        sys.exit(1)
    
    # 测试AI适配器
    if test_ai_adapter():
        logger.info("所有测试通过！AI数据库适配器工作正常")
        sys.exit(0)
    else:
        logger.error("测试失败！")
        sys.exit(1)
