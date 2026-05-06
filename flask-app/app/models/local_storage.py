#!/usr/bin/env python3
"""
本地存储模型，用于替代localStorage功能，统一由数据库管理本地数据

from app.models.base_model import BaseModel
from datetime import datetime

class LocalStorage(BaseModel):
    """本地存储模型，替代localStorage功能"""

    table_name = 'local_storage'
    primary_key = 'id'
    columns = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'key': 'TEXT NOT NULL UNIQUE',  # 存储键
        'value': 'TEXT',  # 存储值（JSON格式）
        'user_id': 'INTEGER',  # 用户ID，可选
        'ttl': 'INTEGER',  # 过期时间戳，可选
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
        """设置存储值"""
        try:
            # JSON import removed - using database

            logger.info(f"设置本地存储值: key={key}, value={value}, user_id={user_id}, ttl={ttl}")

            # 检查是否已存在
            existing = cls.find_one(f"key = ?", (key,))

            if existing:
                # 更新现有记录
                existing.value = str(value)
                existing.updated_at = datetime.now().isoformat()
                if user_id is not None:
                    existing.user_id = user_id
                if ttl is not None:
                    existing.ttl = int(ttl)
                success = existing.save()
                logger.info(f"更新现有记录成功: {success}")
                return success
            else:
                # 创建新记录
                data = {
                    'key': key,
                    'value': str(value),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                    data['user_id'] = user_id
                if ttl is not None:
                new_record = cls(**data)
                success = new_record.save()
                return success
        except Exception as e:
            logger.error(f"设置本地存储失败: {str(e)}")
            return False
    @classmethod
    def get(cls, key, user_id=None):
        try:
            # JSON import removed - using database


                record = cls.find_one(f"key = ? AND user_id = ?", (key, user_id))
            else:
                record = cls.find_one(f"key = ?", (key,))

            logger.info(f"查询结果: {record}")
            if not record:
                return None

            # 检查是否过期
            ttl = record.ttl
            logger.info(f"TTL值: {ttl}")
            if ttl and int(ttl) < int(datetime.now().timestamp()):
                # 过期，删除记录
                record.delete()
                return None

            # 解析JSON值
            value = record.value
            logger.info(f"存储值: {value}")
            if value:
                try:
                    parsed_value = eval(value)
                    logger.info(f"解析后的值: {parsed_value}")
                    return parsed_value
                    return value
            return None
        except Exception as e:
            logger.error(f"获取本地存储失败: {str(e)}")
            return None

    @classmethod
    def remove(cls, key, user_id=None):
        try:
            if user_id is not None:
                record = cls.find_one(f"key = ? AND user_id = ?", (key, user_id))
                record = cls.find_one(f"key = ?", (key,))
            if record:
                return record.delete()
        except Exception as e:
            logger.error(f"删除本地存储失败: {str(e)}")
            return False

    @classmethod
    def clear(cls, user_id=None):
            from app.utils.db import db_manager

                query = f"DELETE FROM {cls.table_name} WHERE user_id = ?"
                params = (user_id,)
                query = f"DELETE FROM {cls.table_name}"
                params = None

            _, success = db_manager.execute(query, params)
        except Exception as e:
            return False

    @classmethod
    def get_all(cls, user_id=None):
        try:
            # JSON import removed - using database
if user_id is not None:
                records = cls.find_all(f"user_id = ?", (user_id,))
            else:
                records = cls.find_all()

            for record in records:
                ttl = record.get('ttl')
                if ttl and int(ttl) < int(datetime.now().timestamp()):
                    # 过期，删除记录
                    continue

                if value:
                    result[record.get('key')] = eval(value)

            return result
        except Exception as e:
            logger.error(f"获取所有本地存储失败: {str(e)}")
            return {}
