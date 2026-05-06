#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON到数据库迁移管理器
负责管理从JSON到数据库的迁移

import os
import sys
import time
# JSON import removed - using database
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

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
        logger.info(f"JSON到数据库迁移管理器初始化完成，版本: {self.manager_version}")

    def ensure_database_exists(self):
        """确保数据库存在"""
        if not os.path.exists('data'):
            os.makedirs('data')

    def get_ai_engine_config(self, engine_name: str) -> Dict:
        """获取AI引擎配置

        Args:
            engine_name: 引擎名称

        Returns:
            Dict: 配置信息
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM ai_engine_config WHERE engine_name = ?', (engine_name,))
            row = cursor.fetchone()

            conn.close()

            if row:
                return {
                    "success": True,
                    "data": {
                        'id': row[0],
                        'engine_name': row[1],
                        'api_key': row[2],
                        'endpoint': row[3],
                        'model': row[4],
                        'is_enabled': bool(row[5]),
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "引擎配置不存在"
                }

        except Exception as e:
            logger.error(f"获取AI引擎配置失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_system_config(self, config_key: str) -> Dict:
        """获取系统配置

        Args:
            config_key: 配置键
        Returns:
            Dict: 配置信息
        try:
            conn = sqlite3.connect(self.db_path)

            cursor.execute('SELECT * FROM system_config WHERE config_key = ?', (config_key,))


                return {
                    "success": True,
                    "data": {
                        'config_key': row[1],
                        'config_value': row[2],
                        'description': row[3],
                        'created_at': row[4],
                    }
                }
            else:
                return {
                    "error": "配置不存在"
                }

        except Exception as e:
            logger.error(f"获取系统配置失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)

    def get_service_config(self, service_name: str) -> Dict:
        """获取服务配置

        Args:
            service_name: 服务名称

            Dict: 配置信息
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            row = cursor.fetchone()

            conn.close()
            if row:
                return {
                    "data": {
                        'id': row[0],
                        'config': eval(row[2]) if row[2] else {},
                        'status': row[3],
                        'created_at': row[4],
                        'updated_at': row[5]
                }
            else:
                return {
                    "success": False,
                    "error": "服务配置不存在"

        except Exception as e:
            logger.error(f"获取服务配置失败: {str(e)}")
            return {
                "success": False,
            }

    def get_error_cases(self) -> Dict:
        """获取错误案例

        Returns:
        try:

            cursor.execute('SELECT * FROM error_cases')
            rows = cursor.fetchall()

            error_cases = []
            for row in rows:
                    'id': row[0],
                    'case_id': row[1],
                    'title': row[2],
                    'solution': row[4],
                    'affected_files': eval(row[5]) if row[5] else [],
                    'fix_date': row[6],
                    'created_at': row[8],
                    'updated_at': row[9]
                })

            conn.close()

            return {
                "success": True,
                "data": error_cases
            }

        except Exception as e:
            logger.error(f"获取错误案例失败: {str(e)}")
            return {
                "error": str(e)
            }

    def update_ai_engine_config(self, engine_name: str, config: Dict) -> Dict:
        """更新AI引擎配置

        Args:
            config: 配置信息

        Returns:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            sql = "UPDATE ai_engine_config SET api_key = ?, endpoint = ?, model = ?, is_enabled = ?, updated_at = ? WHERE engine_name = ?"
            cursor.execute(sql, (
                config.get('api_key', ''),
                config.get('endpoint', ''),
                config.get('model', ''),
                1 if config.get('is_enabled', False) else 0,
                datetime.now().isoformat(),
                engine_name

            conn.commit()
            conn.close()

                "success": True,
                "message": "AI引擎配置更新成功"
            }

            logger.error(f"更新AI引擎配置失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_system_config(self, config_key: str, config_value: str) -> Dict:
        """更新系统配置

        Args:
            config_key: 配置键
            config_value: 配置值

        Returns:
            Dict: 更新结果
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            sql = "UPDATE system_config SET config_value = ?, updated_at = ? WHERE config_key = ?"
            cursor.execute(sql, (
                config_value,
                datetime.now().isoformat(),
                config_key
            ))

            conn.commit()
            conn.close()

                "success": True,
                "message": "系统配置更新成功"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

        """获取数据库状态

        Returns:
            Dict: 数据库状态
        try:
            cursor = conn.cursor()

            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # 获取各表记录数
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_status[table_name] = count
            conn.close()

                "success": True,
                "data": {
                    'table_status': table_status,
                    'timestamp': time.time()
            }

            return {
                "success": False,
                "error": str(e)
            }

# 全局迁移管理器实例
json_to_db_manager = JsonToDbManager()

def get_json_to_db_manager() -> JsonToDbManager:
    """获取迁移管理器实例

    Returns:
        JsonToDbManager: 迁移管理器实例
    return json_to_db_manager
