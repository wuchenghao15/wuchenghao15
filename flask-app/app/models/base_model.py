#!/usr/bin/env python3
"""
基础模型类，提供通用的数据库操作方法

from app.utils.db import db_manager
from app.utils.logging import logger
from app.utils.encryption import encryption_manager
from datetime import datetime

class BaseModel:
    """基础模型类，提供通用的数据库操作方法"""

    # 子类必须定义这些属性
    table_name = None
    primary_key = 'id'
    columns = {}
    # 需要加密的字段
    encrypted_fields = []

    def __init__(self, **kwargs):
        """初始化模型实例"""
        self._data = {}
        self._dirty = set()  # 记录修改过的字段

        # 获取所有列名
        table_columns = getattr(self.__class__, 'columns', None) or getattr(self.__class__, 'fields', None)

        # 初始化所有字段
        if table_columns:
            for col_name in table_columns.keys():
                if col_name in kwargs:
                    value = kwargs[col_name]
                    # 解密敏感字段
                    if col_name in self.encrypted_fields and value:
                        value = encryption_manager.decrypt(value)
                    self._data[col_name] = value
                else:
                    # 设置默认值
                    col_def = table_columns[col_name]
                    if isinstance(col_def, dict):
                        # 处理 fields 格式
                        default_value = col_def.get('default')
                    else:
                        col_type = col_def
                        default_value = None
                        if 'DEFAULT' in col_type:
                            # 处理默认值
                            if 'CURRENT_TIMESTAMP' in col_type:
                                default_value = datetime.now().isoformat()
                            else:
                                default_value = col_type.split('DEFAULT')[1].strip()
                                if default_value.startswith("'" or '"'):
                                    default_value = default_value[1:-1]
                                elif default_value.isdigit():
                                    default_value = int(default_value)

                    self._data[col_name] = default_value

    @classmethod
    def create_table(cls):
        """创建表"""
        # 支持 fields 和 columns 属性
        table_columns = getattr(cls, 'columns', None) or getattr(cls, 'fields', None)

        if not cls.table_name or not table_columns:
            logger.error(f"模型 {cls.__name__} 没有定义 table_name 或 columns/fields 属性")
            return False

        # 转换 fields 格式为 columns 格式
        columns_dict = {}
        for col_name, col_def in table_columns.items():
            if isinstance(col_def, dict):
                # 处理 fields 格式
                col_type = col_def.get('type', 'TEXT')
                    if col_def.get('auto_increment'):
                    else:
                if col_def.get('unique'):
                    col_type += " UNIQUE"
                if col_def.get('not_null'):
                    col_type += " NOT NULL"
                if 'default' in col_def:
                    default_val = col_def['default']
                    if isinstance(default_val, str):
                        col_type += f" DEFAULT '{default_val}'"
                    else:
                columns_dict[col_name] = col_type
            else:
                columns_dict[col_name] = col_def

        # 添加主键约束
        if cls.primary_key and cls.primary_key not in columns_dict:
            columns_dict[cls.primary_key] = "INTEGER PRIMARY KEY AUTOINCREMENT"

        return db_manager.create_table(cls.table_name, columns_dict)
    def save(self):
        """保存模型实例，自动判断是插入还是更新"""
        if not self.table_name:
            logger.error(f"模型 {self.__class__.__name__} 没有定义 table_name 属性")
            return False

        # 检查主键
        if self.primary_key and self._data.get(self.primary_key):
            # 更新现有记录
            return self._update()
        else:
            return self._insert()

    def _insert(self):
        """插入新记录"""
        # 准备插入数据
        insert_data = {}
        # 获取所有列名
        if table_columns:
                if col_name != self.primary_key:  # 主键由数据库自动生成
                    # 加密敏感字段
                        value = encryption_manager.encrypt(value)
                    insert_data[col_name] = value

        # 执行插入
        if primary_key_value:
            # 设置主键值
            self._data[self.primary_key] = primary_key_value
            self._dirty.clear()  # 清除脏标记
            logger.info(f"插入 {self.table_name} 记录成功，主键: {primary_key_value}")
            return True
        else:
            logger.error(f"插入 {self.table_name} 记录失败")
            return False

    def _update(self):
        """更新现有记录"""
        update_data = {}
        for col_name in self._dirty:
            value = self._data.get(col_name)
            # 加密敏感字段
            if col_name in self.encrypted_fields and value:
                value = encryption_manager.encrypt(value)
            update_data[col_name] = value

        if not update_data:
            return True

        # 执行更新
        where_clause = f"{self.primary_key} = ?"
        where_params = (self._data[self.primary_key],)

        if db_manager.update(self.table_name, update_data, where_clause, where_params):
            self._dirty.clear()  # 清除脏标记
            logger.info(f"更新 {self.table_name} 记录成功，主键: {self._data[self.primary_key]}")
        else:
            return False

        """删除记录"""
        if not self.primary_key or not self._data.get(self.primary_key):
            return False

        where_clause = f"{self.primary_key} = ?"

        if db_manager.delete(self.table_name, where_clause, where_params):
            logger.info(f"删除 {self.table_name} 记录成功，主键: {self._data[self.primary_key]}")
            return True
        else:
            logger.error(f"删除 {self.table_name} 记录失败，主键: {self._data[self.primary_key]}")

    @classmethod
        """通过主键获取记录"""
        result = db_manager.fetch_one(query, (primary_key_value,))
        if result:
            return cls(**dict(result))
        return None

    @classmethod
    def get_all(cls, order_by=None):
        """获取所有记录"""
        query = f"SELECT * FROM {cls.table_name}"
        if order_by:
            query += f" ORDER BY {order_by}"
        results = db_manager.fetch_all(query)
    @classmethod
    def filter(cls, where_clause=None, where_params=None, order_by=None, limit=None, offset=None):
        """根据条件过滤记录"""
        query = f"SELECT * FROM {cls.table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"

        results = db_manager.fetch_all(query, where_params)
        return [cls(**dict(result)) for result in results]

    @classmethod
    def count(cls, where_clause=None, where_params=None):
        """统计记录数量"""
        return db_manager.count(cls.table_name, where_clause, where_params)

    @classmethod
    def find_one(cls, where_clause, where_params=None):
        """查找单个记录"""
        query = f"SELECT * FROM {cls.table_name} WHERE {where_clause} LIMIT 1"
        result = db_manager.fetch_one(query, where_params)
        if result:
            return cls(**dict(result))

    def __getattr__(self, name):
        """获取属性值"""
        if name in self._data:
            return self._data[name]

        """设置属性值"""
        if name in ['_data', '_dirty']:
            # 处理内部属性
            super().__setattr__(name, value)
        else:
            # 检查是否是模型字段
            table_columns = getattr(self.__class__, 'columns', None) or getattr(self.__class__, 'fields', None)
            if table_columns and name in table_columns:
                    self._data[name] = value
                    self._dirty.add(name)
                # 处理其他属性
                super().__setattr__(name, value)

    def to_dict(self):
        """将模型实例转换为字典"""
        return self._data.copy()
    def add_column(cls, column_name, column_type):
        if not cls.table_name:
            return False

        # 更新模型的 columns 属性
        cls.columns[column_name] = column_type

        # 执行添加列操作
        return db_manager.add_column(cls.table_name, column_name, column_type)
