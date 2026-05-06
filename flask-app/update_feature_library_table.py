#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新特征库表，添加分析相关字段

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.utils.db import db_manager
from app.utils.logging import logger

def update_feature_library_table():
    """更新特征库表，添加分析相关字段"""
    logger.info("开始更新特征库表...")

    try:
        # 添加analysis字段
        add_analysis_sql = """
        ALTER TABLE ai_feature_library ADD COLUMN analysis TEXT
        db_manager.execute(add_analysis_sql)
        logger.info("✓ 添加analysis字段成功")

        # 添加analyzed_at字段
        add_analyzed_at_sql = """
        ALTER TABLE ai_feature_library ADD COLUMN analyzed_at DATETIME
        db_manager.execute(add_analyzed_at_sql)
        logger.info("✓ 添加analyzed_at字段成功")

        logger.info("特征库表更新完成")
        return True
    except Exception as e:
        # 如果字段已存在，忽略错误
        if "duplicate column name" in str(e) or "already exists" in str(e):
            logger.info("✓ 特征库表字段已存在")
            return True
        else:
            logger.error(f"更新特征库表失败: {str(e)}")

if __name__ == "__main__":
    update_feature_library_table()
