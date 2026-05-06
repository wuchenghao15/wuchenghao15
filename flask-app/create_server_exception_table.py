#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建服务器异常表脚本
用于创建server_exceptions表，存储服务器异常和修复结果

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.utils.logging import logger
from app.utils.db import db_manager

def create_server_exception_table():
    """创建服务器异常表"""
    table_name = "server_exceptions"

    # 定义表结构
    columns = {
        "id": "INTEGER PRIMARY KEY AUTO_INCREMENT",
        "exception_id": "VARCHAR(50) NOT NULL",
        "exception_type": "VARCHAR(50) NOT NULL",
        "exception_level": "VARCHAR(20) NOT NULL",
        "description": "TEXT NOT NULL",
        "occurred_at": "DATETIME NOT NULL",
        "repair_success": "BOOLEAN NOT NULL",
        "repair_action": "VARCHAR(50) NOT NULL",
        "repair_message": "TEXT NOT NULL",
        "repair_details": "TEXT",
        "server_stats": "TEXT",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }

    # 创建表
    success = db_manager.create_table(table_name, columns)

    if success:
        logger.info(f"表 {table_name} 创建成功")
        return True
    else:
        logger.error(f"表 {table_name} 创建失败")
        return False

def add_indexes():
    """添加索引"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_exception_id ON server_exceptions(exception_id)",
        "CREATE INDEX IF NOT EXISTS idx_exception_type ON server_exceptions(exception_type)",
        "CREATE INDEX IF NOT EXISTS idx_occurred_at ON server_exceptions(occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_repair_success ON server_exceptions(repair_success)"
    ]

    for index_sql in indexes:
        cursor, success = db_manager.execute(index_sql)
        if success:
        else:
            logger.error(f"索引创建失败: {index_sql}")
if __name__ == "__main__":
    logger.info("开始创建服务器异常表...")

    # 创建表
        # 添加索引
        add_indexes()
        logger.info("服务器异常表创建完成")
    else:
        logger.error("服务器异常表创建失败")
        sys.exit(1)
    sys.exit(0)
