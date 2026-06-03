# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密数据库管理器 - 实现数据表和列的自动加密
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import os
from app.utils.encryption import encryption_manager

class EncryptedDBManager:
    """加密数据库管理器"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.encrypt = encryption_manager.encrypt
        self.decrypt = encryption_manager.decrypt

        self.encrypted_tables = {
            'users': 't_aaef114130946f87',
            'session_data': 'certificate_data',
            'permission_data': 'ai_capabilities'
        }

        self.encrypted_columns = {
            'users': ['password', 'email'],
            't_aaef114130946f87': ['password', 'email'],
            'session_data': ['csrf_token', 'refresh_token'],
            'certificate_data': ['data', 'fingerprint'],
            'permission_data': ['permissions'],
            'ai_capabilities': ['description'],
            'logs': ['details'],
            'exam_questions': ['question_text', 'correct_answer', 'explanation'],
            'exam_papers': ['title'],
            'settings_approval': ['new_value', 'old_value']
        }

    def connect(self):
        """建立数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _encrypt_row(self, table_name, row):
        """加密行数据中的敏感列"""
        if table_name not in self.encrypted_columns:
            return row

        encrypted_row = row.copy()
        for col in self.encrypted_columns[table_name]:
            if col in encrypted_row and encrypted_row[col]:
                encrypted_row[col] = self.encrypt(str(encrypted_row[col]))
        return encrypted_row

    def _decrypt_row(self, table_name, row):
        """解密行数据中的敏感列"""
        if table_name not in self.encrypted_columns:
            return row

        decrypted_row = row.copy()
        for col in self.encrypted_columns[table_name]:
            if col in decrypted_row and decrypted_row[col]:
                try:
                    decrypted_row[col] = self.decrypt(decrypted_row[col])
                except Exception:
                    pass
        return decrypted_row

    def insert(self, table_name, data):
        """插入加密数据"""
        encrypted_data = self._encrypt_row(table_name, data)

        columns = ', '.join(encrypted_data.keys())
        placeholders = ', '.join(['?' for _ in encrypted_data.values()])
        values = list(encrypted_data.values())

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})', values)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return last_id

    def update(self, table_name, data, where_clause, where_params):
        """更新加密数据"""
        encrypted_data = self._encrypt_row(table_name, data)

        set_clause = ', '.join([f'{k} = ?' for k in encrypted_data.keys()])
        values = list(encrypted_data.values()) + list(where_params)

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE {table_name} SET {set_clause} WHERE {where_clause}', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected

    def select(self, table_name, columns='*', where_clause=None, where_params=None):
        """查询并解密数据"""
        conn = self.connect()
        cursor = conn.cursor()

        if where_clause:
            query = f'SELECT {columns} FROM {table_name} WHERE {where_clause}'
            cursor.execute(query, where_params if where_params else [])
        else:
            query = f'SELECT {columns} FROM {table_name}'
            cursor.execute(query)

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            row_dict = dict(row)
            decrypted_row = self._decrypt_row(table_name, row_dict)
            result.append(decrypted_row)

        return result

    def select_one(self, table_name, columns='*', where_clause=None, where_params=None):
        """查询单条并解密数据"""
        conn = self.connect()
        cursor = conn.cursor()

        if where_clause:
            query = f'SELECT {columns} FROM {table_name} WHERE {where_clause} LIMIT 1'
            cursor.execute(query, where_params if where_params else [])
        else:
            query = f'SELECT {columns} FROM {table_name} LIMIT 1'
            cursor.execute(query)

        row = cursor.fetchone()
        conn.close()

        if row:
            row_dict = dict(row)
            return self._decrypt_row(table_name, row_dict)
        return None

    def delete(self, table_name, where_clause, where_params):
        """删除数据"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table_name} WHERE {where_clause}', where_params)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected

    def execute(self, query, params=None):
        """执行原始SQL查询"""
        conn = self.connect()
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()
        conn.close()

    def query(self, query, params=None):
        """执行查询并返回结果"""
        conn = self.connect()
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def create_encrypted_table(self, table_name, columns):
        """创建带加密支持的表"""
        conn = self.connect()
        cursor = conn.cursor()

        column_defs = []
        for col_name, col_type in columns.items():
            if col_name in self.encrypted_columns.get(table_name, []):
                column_defs.append(f'{col_name} TEXT')
            else:
                column_defs.append(f'{col_name} {col_type}')

        create_query = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(column_defs)})'
        cursor.execute(create_query)
        conn.commit()
        conn.close()

    def encrypt_existing_data(self):
        """加密现有数据库中的敏感数据"""
        conn = self.connect()
        cursor = conn.cursor()

        for table_name, columns in self.encrypted_columns.items():
            try:
                cursor.execute(f'SELECT * FROM {table_name}')
                rows = cursor.fetchall()

                for row in rows:
                    row_dict = dict(row)
                    update_values = {}
                    for col in columns:
                        if col in row_dict and row_dict[col]:
                            encrypted_val = self.encrypt(row_dict[col])
                            if encrypted_val != row_dict[col]:
                                update_values[col] = encrypted_val

                    if update_values:
                        set_clause = ', '.join([f'{k} = ?' for k in update_values.keys()])
                        values = list(update_values.values()) + [row_dict['id']]
                        cursor.execute(f'UPDATE {table_name} SET {set_clause} WHERE id = ?', values)

                conn.commit()
            except Exception as e:
                print(f"加密表 {table_name} 时出错: {e}")

        conn.close()

    def get_encrypted_columns(self, table_name):
        """获取指定表的加密列列表"""
        return self.encrypted_columns.get(table_name, [])

    def add_encrypted_column(self, table_name, column_name):
        """添加新的加密列"""
        if table_name not in self.encrypted_columns:
            self.encrypted_columns[table_name] = []
        if column_name not in self.encrypted_columns[table_name]:
            self.encrypted_columns[table_name].append(column_name)

    def remove_encrypted_column(self, table_name, column_name):
        """移除加密列"""
        if table_name in self.encrypted_columns and column_name in self.encrypted_columns[table_name]:
            self.encrypted_columns[table_name].remove(column_name)


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
encrypted_db_manager = EncryptedDBManager(DB_PATH)
