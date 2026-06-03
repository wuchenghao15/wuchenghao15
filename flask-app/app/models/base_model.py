# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
基础数据模型
"""

import logging

logger = logging.getLogger(__name__)


class BaseModel:
    """基础模型类"""

    table_name = None
    fields = {}

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create_table(cls):
        """创建表"""
        logger.info(f"创建表 {cls.table_name}")

    @classmethod
    def get_all(cls):
        """获取所有记录"""
        return []

    @classmethod
    def get_by_id(cls, id):
        """通过ID获取记录"""
        return None

    def save(self):
        """保存记录"""
        logger.info(f"保存 {self.__class__.__name__}")
        return True

    def delete(self):
        """删除记录"""
        logger.info(f"删除 {self.__class__.__name__}")
        return True

    def to_dict(self):
        """转换为字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
