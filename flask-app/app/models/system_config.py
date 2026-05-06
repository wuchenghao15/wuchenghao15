#!/usr/bin/env python3
"""系统参数配置模型"""

from app.models.base_model import BaseModel
from app.utils.db import DatabaseManager

db_manager = DatabaseManager()

class SystemConfig(BaseModel):
    """系统参数配置模型"""

    table_name = "system_config"

    fields = {
        "id": {"type": "INTEGER", "primary_key": True, "auto_increment": True},
        "key": {"type": "VARCHAR(100)", "unique": True, "not_null": True},
        "value": {"type": "TEXT"},
        "description": {"type": "VARCHAR(255)"},
        "category": {"type": "VARCHAR(50)"},
        "data_type": {"type": "VARCHAR(20)"},
        "is_active": {"type": "BOOLEAN", "default": True},
        "created_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
        "updated_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_by_key(cls, key: str):
        """根据key获取配置"""
        result = db_manager.fetch_one(f"SELECT * FROM {cls.table_name} WHERE key = ?", (key,))
        if result:
            return cls(**result)
        return None

    @classmethod
    def set_value(cls, key: str, value: str, description: str = None):
        """设置配置值"""
        existing = cls.get_by_key(key)
        if existing:
            data = {"value": value}
            if description:
                data["description"] = description
            existing.update(data)
        else:
            data = {"key": key, "value": value}
            if description:
                data["description"] = description
            cls.create(**data)

    @classmethod
    def get_all_by_category(cls, category: str):
        """根据类别获取所有配置"""
        results = db_manager.fetch_all(f"SELECT * FROM {cls.table_name} WHERE category = ?", (category,))
        return [cls(**result) for result in results]

    @classmethod
    def get_active_configs(cls):
        """获取所有启用的配置"""
        results = db_manager.fetch_all(f"SELECT * FROM {cls.table_name} WHERE is_active = ?", (True,))
        return {r.key: r.value for r in [cls(**result) for result in results]}