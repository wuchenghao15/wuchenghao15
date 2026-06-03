# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""系统参数配置模型"""

from app.models.base_model import BaseModel
from app.utils.db import DatabaseManager
import sys

db_manager = DatabaseManager()


class SystemConfig(BaseModel):
    """系统参数配置模型"""

    table_name = "system_config"

    fields = {
        "id": {"type": "INTEGER", "primary_key": True, "auto_increment": True},
        "config_key": {"type": "VARCHAR(100)", "unique": True, "not_null": True},
        "config_value": {"type": "TEXT"},
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
        """通过键获取配置"""
        return None

    @classmethod
    def get_all_configs(cls):
        """获取所有配置"""
        return []

    @classmethod
    def set_config(cls, key: str, value: str):
        """设置配置"""
        pass
