# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI数据库适配器模块
用于实现AI与数据库的深度适配
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Any
from app.utils.db import db_manager
from app.utils.logging import logger
import logging


class AIDBAdapter:
    """AI数据库适配器: 负责管理AI与数据库的深度交互"""

    def __init__(self):
        """初始化AI数据库适配器"""
        self.db_manager = db_manager
        self.database_type = 'sqlite'
        self.database_path = self.db_manager.db_path
        logger.info(f"AI数据库适配器初始化成功,数据库类型: {self.database_type}, 数据库路径: {self.database_path}")

    def get_database_schema(self) -> List[Dict[str, Any]]:
        """获取数据库架构"""
        try:
            tables = []
            cursor = self.db_manager.execute("SELECT name FROM sqlite_master WHERE type='table';")
            if cursor:
                for table_name in cursor.fetchall():
                    table_name = table_name[0]
                    table_info = {
                        'name': table_name,
                        'columns': []
                    }

                    col_cursor = self.db_manager.execute(f"PRAGMA table_info({table_name});")
                    if col_cursor:
                        for col in col_cursor.fetchall():
                            table_info['columns'].append({
                                'id': col[0],
                                'name': col[1],
                                'type': col[2],
                                'notnull': col[3],
                                'default': col[4],
                                'pk': col[5]
                            })

                    tables.append(table_info)
            logger.info(f"获取数据库架构成功, 找到 {len(tables)} 个表")
            return tables
        except Exception as e:
            logger.error(f"获取数据库架构失败: {str(e)}")
            return []
