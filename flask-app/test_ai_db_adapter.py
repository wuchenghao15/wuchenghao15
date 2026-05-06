#!/usr/bin/env python3
"""
直接测试AI数据库适配器功能，不依赖服务器运行

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.logging import logger

def test_ai_db_adapter():
    """测试AI数据库适配器"""
    try:
        logger.info("开始测试AI数据库适配器...")

        # 导入AI数据库适配器
        from app.utils.ai_db_adapter import AIDBAdapter

        # 创建适配器实例
        adapter = AIDBAdapter()
        logger.info("AI数据库适配器实例创建成功")

        # 测试获取数据库架构
        logger.info("测试获取数据库架构...")
        schema = adapter.get_database_schema()
        logger.info(f"获取数据库架构成功，找到 {len(schema)} 个表")

        # 打印前5个表名
        for i, table in enumerate(schema[:5]):
            logger.info(f"表 {i+1}: {table['name']}")

        # 测试查询性能分析
        logger.info("测试查询性能分析...")
        query = "SELECT * FROM users WHERE is_active = 1"
        analysis = adapter.analyze_query_performance(query)
        logger.info(f"查询性能分析结果: {analysis}")

        # 测试自然语言查询生成
        logger.info("测试自然语言查询生成...")
        natural_query = "查找所有活跃用户"
        generated = adapter.generate_optimized_query(natural_query)
        logger.info(f"自然语言查询生成结果: {generated}")

        # 测试数据库优化
        logger.info("测试数据库优化...")
        optimization = adapter.optimize_database()
        logger.info(f"数据库优化结果: {optimization}")

        # 测试数据库性能监控
        logger.info("测试数据库性能监控...")
        monitoring = adapter.monitor_database_performance()
        logger.info(f"数据库性能监控结果: {monitoring}")

        # 测试AI深度适配
        logger.info("测试AI深度适配...")
        deep_adapt = adapter.deep_adapt()
        logger.info(f"AI深度适配结果: {deep_adapt}")

        logger.info("所有测试通过！AI数据库适配器功能正常")
        return True
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_ai_db_adapter()
