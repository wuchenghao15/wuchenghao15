#!/usr/bin/env python3
"""
本地存储模型 - 用于替代localStorage功能,统一由数据库管理本地数据
"""

from app.models.base_model import BaseModel
from datetime import datetime

class LocalStorage(BaseModel):
    """本地存储模型: 替代localStorage功能"""

    table_name = 'local_storage'
    primary_key = 'id'
    columns = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'key': 'TEXT NOT NULL UNIQUE',
        'value': 'TEXT',
        'user_id': 'INTEGER',
        'ttl': 'INTEGER',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }

    def __init__(self, **kwargs):
        """初始化模型实例"""
        super().__init__(**kwargs)

    @classmethod
    def create_table(cls):
        """创建表"""
        result = super().create_table()
        if result:
            from app.utils.logging import logger
            logger.info(f"表 {cls.table_name} 创建成功")
        return result

    @classmethod
    def get(cls, key, user_id=None):
        try:
            if user_id is not None:
                record = cls.find_one("key = ? AND user_id = ?", (key, user_id))
            else:
                record = cls.find_one("key = ?", (key,))

            from app.utils.logging import logger
            logger.info(f"查询结果: {record}")
            if not record:
                return None
            return record
        except Exception as e:
            return None

    @classmethod
    def remove(cls, key, user_id=None):
        try:
            if user_id is not None:
                record = cls.find_one("key = ? AND user_id = ?", (key, user_id))
            else:
                record = cls.find_one("key = ?", (key,))
            if record:
                return record.delete()
            return False
        except Exception as e:
            return False

    @classmethod
    def clear(cls, user_id=None):
        try:
            from app.utils.db import db_manager
            if user_id is not None:
                query = f"DELETE FROM {cls.table_name} WHERE user_id = ?"
                params = (user_id,)
            else:
                query = f"DELETE FROM {cls.table_name}"
                params = None

            success = db_manager.execute(query, params)
            return success
        except Exception as e:
            return False

    @classmethod
    def get_all(cls, user_id=None):
        try:
            result = {}
            if user_id is not None:
                records = cls.find_all("user_id = ?", (user_id,))
            else:
                records = cls.find_all()

            for record in records:
                ttl = record.get('ttl')
                if ttl and int(ttl) < int(datetime.now().timestamp()):
                    continue

                value = record.get('value')
                if value:
                    result[record.get('key')] = eval(value)

            return result
        except Exception as e:
            return {}
