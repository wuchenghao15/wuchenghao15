# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库存储服务 - 替代JSON功能
所有数据存储都通过数据库完成,不再使用JSON文件
"""

import sqlite3
from contextlib import contextmanager
import threading
import time
import hashlib
from datetime import datetime
from app.utils.logging import logger
import logging
import json
import os


class DatabaseStorageService:
    """数据库存储服务 - 替代JSON功能"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseStorageService, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化数据库存储服务"""
        self.db_path = 'flask-app/app.db'
        self._create_tables()
        logger.info("数据库存储服务初始化完成")

    def _create_tables(self):
        """创建必要的数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS serialized_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_key TEXT UNIQUE NOT NULL,
                data_type TEXT NOT NULL,
                string_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS complex_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_key TEXT NOT NULL,
                object_type TEXT NOT NULL,
                element_key TEXT,
                element_type TEXT NOT NULL,
                string_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value INTEGER,
                parent_id INTEGER,
                index_pos INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_complex_data_key ON complex_data(data_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_complex_data_parent ON complex_data(parent_id)')

            conn.commit()

    def _generate_key(self, prefix, *args):
        """生成唯一键"""
        key_str = "_".join(str(arg) for arg in args)
        hash_key = hashlib.md5(key_str.encode()).hexdigest()[:16]
        return f"{prefix}_{hash_key}"

    def set(self, key, value):
        """存储任意类型数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            self.delete(key)

            if isinstance(value, str):
                cursor.execute(
                    "INSERT INTO serialized_data (data_key, data_type, string_value) VALUES (?, ?, ?)",
                    (key, 'string', value)
                )
            elif isinstance(value, int):
                cursor.execute(
                    "INSERT INTO serialized_data (data_key, data_type, int_value) VALUES (?, ?, ?)",
                    (key, 'int', value)
                )
            elif isinstance(value, float):
                cursor.execute(
                    "INSERT INTO serialized_data (data_key, data_type, float_value) VALUES (?, ?, ?)",
                    (key, 'float', value)
                )
            elif isinstance(value, bool):
                cursor.execute(
                    "INSERT INTO serialized_data (data_key, data_type, bool_value) VALUES (?, ?, ?)",
                    (key, 'bool', 1 if value else 0)
                )
            elif isinstance(value, (dict, list)):
                self._store_complex_data(key, value)
            else:
                cursor.execute(
                    "INSERT INTO serialized_data (data_key, data_type, string_value) VALUES (?, ?, ?)",
                    (key, 'string', str(value))
                )

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"存储数据失败: {str(e)}")
            return False
        finally:
            conn.close()

    def get(self, key, default=None):
        """从数据库获取数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('SELECT data_type, string_value, int_value, float_value, bool_value FROM serialized_data WHERE data_key = ?', (key,))
                row = cursor.fetchone()

                if row:
                    data_type, string_val, int_val, float_val, bool_val = row
                    return self._convert_from_db(data_type, string_val, int_val, float_val, bool_val)

                return default
            except Exception as e:
                logger.error(f"获取数据失败: {str(e)}")
                return default

    def delete(self, key):
        """删除指定键的数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('DELETE FROM serialized_data WHERE data_key = ?', (key,))
                cursor.execute('DELETE FROM complex_data WHERE data_key = ?', (key,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"删除数据失败: {str(e)}")
                return False

    def exists(self, key):
        """检查键是否存在"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('SELECT COUNT(*) FROM serialized_data WHERE data_key = ?', (key,))
                if cursor.fetchone()[0] > 0:
                    return True

                cursor.execute('SELECT COUNT(*) FROM complex_data WHERE data_key = ?', (key,))
                if cursor.fetchone()[0] > 0:
                    return True

                return False
            except Exception as e:
                logger.error(f"检查键存在失败: {str(e)}")
                return False

    def _convert_from_db(self, data_type, string_val, int_val, float_val, bool_val):
        """从数据库格式转换为Python类型"""
        if data_type == 'string':
            return string_val
        elif data_type == 'int':
            return int_val
        elif data_type == 'float':
            return float_val
        elif data_type == 'bool':
            return bool(bool_val)
        return None

    def _store_complex_data(self, key, value):
        """存储复杂对象(dict或list)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                object_type = 'dict' if isinstance(value, dict) else 'list'

                if isinstance(value, dict):
                    self._store_dict(cursor, key, value, None)
                else:
                    self._store_list(cursor, key, value, None)

                conn.commit()
            except Exception as e:
                logger.error(f"存储复杂数据失败 {key}: {str(e)}")
                conn.rollback()

    def _store_dict(self, cursor, key, data, parent_id):
        """存储字典数据"""
        for element_key, element_value in data.items():
            self._store_element(cursor, key, 'dict', element_key, element_value, parent_id)

    def _store_list(self, cursor, key, data, parent_id):
        """存储列表数据"""
        for index, element_value in enumerate(data):
            self._store_element(cursor, key, 'list', str(index), element_value, parent_id, index)

    def _store_element(self, cursor, key, object_type, element_key, value, parent_id, index_pos=None):
        """存储单个元素"""
        if isinstance(value, str):
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, string_value, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'string', value, parent_id, index_pos)
            )
        elif isinstance(value, int):
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, int_value, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'int', value, parent_id, index_pos)
            )
        elif isinstance(value, float):
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, float_value, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'float', value, parent_id, index_pos)
            )
        elif isinstance(value, bool):
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, bool_value, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'bool', 1 if value else 0, parent_id, index_pos)
            )
        elif isinstance(value, dict):
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'nested_dict', parent_id, index_pos)
            )
            nested_parent_id = cursor.lastrowid
            self._store_dict(cursor, key, value, nested_parent_id)
        elif isinstance(value, list):
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'nested_list', parent_id, index_pos)
            )
            nested_parent_id = cursor.lastrowid
            self._store_list(cursor, key, value, nested_parent_id)
        else:
            cursor.execute(
                "INSERT INTO complex_data (data_key, object_type, element_key, element_type, string_value, parent_id, index_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, object_type, element_key, 'string', str(value), parent_id, index_pos)
            )

    def _load_complex_data(self, key, object_type):
        """加载复杂对象"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('SELECT * FROM complex_data WHERE data_key = ? AND parent_id IS NULL ORDER BY index_pos', (key,))
                rows = cursor.fetchall()

                if object_type == 'dict':
                    result = {}
                    for row in rows:
                        element_key = row[2]
                        value = self._load_element(cursor, row, key)
                        result[element_key] = value
                    return result
                else:
                    result = []
                    for row in rows:
                        value = self._load_element(cursor, row, key)
                        result.append(value)
                    return result
            except Exception as e:
                logger.error(f"加载复杂数据失败: {str(e)}")
                return None

    def _load_element(self, cursor, row, key):
        """加载单个元素"""
        element_type = row[4]
        string_val = row[5]
        int_val = row[6]
        float_val = row[7]
        bool_val = row[8]
        parent_id = row[9]

        if element_type == 'string':
            return string_val
        elif element_type == 'int':
            return int_val
        elif element_type == 'float':
            return float_val
        elif element_type == 'bool':
            return bool(bool_val)
        elif element_type == 'nested_dict':
            return self._load_nested(cursor, parent_id, key, 'dict')
        elif element_type == 'nested_list':
            return self._load_nested(cursor, parent_id, key, 'list')
        return None

    def _load_nested(self, cursor, parent_id, key, object_type):
        """加载嵌套对象"""
        cursor.execute('SELECT * FROM complex_data WHERE parent_id = ? ORDER BY index_pos', (parent_id,))
        rows = cursor.fetchall()

        if object_type == 'dict':
            result = {}
            for row in rows:
                element_key = row[2]
                value = self._load_element(cursor, row, key)
                result[element_key] = value
            return result
        else:
            result = []
            for row in rows:
                value = self._load_element(cursor, row, key)
                result.append(value)
            return result

    def batch_set(self, items):
        """批量设置数据"""
        try:
            for key, value in items.items():
                self.delete(key)
                self.set(key, value)
            return True
        except Exception as e:
            logger.error(f"批量设置数据失败: {str(e)}")
            return False

    def batch_get(self, keys):
        """批量获取数据"""
        result = {}
        for key in keys:
            result[key] = self.get(key)
        return result

    def dumps(self, obj):
        """模拟json.dumps - 存储对象并返回key"""
        key = self._generate_key('json', str(id(obj)), int(time.time()))
        self.set(key, obj)
        return key

    def loads(self, key):
        """模拟json.loads - 根据key获取对象"""
        return self.get(key)


db_storage_service = DatabaseStorageService()
