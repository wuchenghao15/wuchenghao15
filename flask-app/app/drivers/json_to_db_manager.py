# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON到数据库迁移管理器
负责管理从JSON到数据库的迁移
"""

import os
import sys
import time
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('json_to_db_manager')


class JsonToDbManager:
    """JSON到数据库迁移管理器"""

    def __init__(self):
        """初始化迁移管理器"""
        self.manager_version = "1.0.0"
        self.db_path = "data/mtscos_ai_project.db"
        self.ensure_database_exists()
        logger.info(f"JSON到数据库迁移管理器初始化完成,版本: {self.manager_version}")

    def ensure_database_exists(self):
        """确保数据库存在"""
        if not os.path.exists('data'):
            os.makedirs('data')

    def get_ai_engine_config(self, engine_name: str) -> Dict:
        """
        获取AI引擎配置

        Args:
            engine_name: 引擎名称

        Returns:
            Dict: 配置信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_engine_config WHERE engine_name = ?', (engine_name,))
                row = cursor.fetchone()

            if row:
                return dict(row)
            return {}
        except Exception as e:
            logger.error(f"获取AI引擎配置失败: {e}")
            return {}
