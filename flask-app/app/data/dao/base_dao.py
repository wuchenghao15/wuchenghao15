# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础数据访问对象类
提供通用的数据访问方法
"""

from typing import Dict, List, Optional, Any, Type
from uuid import uuid4

from app.utils.db import db_manager


class BaseDAO:
    """基础数据访问对象"""
    
    _db = None
    _table_name = ''
    _primary_key = 'id'
    
    @classmethod
    def set_db_manager(cls, db_manager_instance):
        """设置数据库管理器"""
        cls._db = db_manager_instance
    
    @classmethod
    def get_db(cls):
        """获取数据库管理器"""
        return cls._db or db_manager
    
    @classmethod
    def create(cls, data: Dict) -> Optional[str]:
        """创建记录"""
        if not cls._table_name:
            return None
        
        try:
            data = data.copy()
            if cls._primary_key not in data:
                data[cls._primary_key] = str(uuid4())
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())
            
            query = f"INSERT INTO {cls._table_name} ({columns}) VALUES ({placeholders})"
            cls.get_db().execute(query, values)
            return data[cls._primary_key]
        except Exception as e:
            import logging
            logging.error(f"创建记录失败: {str(e)}")
            return None
    
    @classmethod
    def get(cls, identifier: Any) -> Optional[Dict]:
        """获取单条记录"""
        if not cls._table_name:
            return None
        
        try:
            query = f"SELECT * FROM {cls._table_name} WHERE {cls._primary_key} = ?"
            result = cls.get_db().fetch_one(query, (identifier,))
            return result
        except Exception as e:
            import logging
            logging.error(f"获取记录失败: {str(e)}")
            return None
    
    @classmethod
    def update(cls, identifier: Any, data: Dict) -> bool:
        """更新记录"""
        if not cls._table_name:
            return False
        
        try:
            data = data.copy()
            if cls._primary_key in data:
                del data[cls._primary_key]
            
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            values = tuple(data.values()) + (identifier,)
            
            query = f"UPDATE {cls._table_name} SET {set_clause} WHERE {cls._primary_key} = ?"
            cls.get_db().execute(query, values)
            return True
        except Exception as e:
            import logging
            logging.error(f"更新记录失败: {str(e)}")
            return False
    
    @classmethod
    def delete(cls, identifier: Any) -> bool:
        """删除记录"""
        if not cls._table_name:
            return False
        
        try:
            query = f"DELETE FROM {cls._table_name} WHERE {cls._primary_key} = ?"
            cls.get_db().execute(query, (identifier,))
            return True
        except Exception as e:
            import logging
            logging.error(f"删除记录失败: {str(e)}")
            return False
    
    @classmethod
    def list(cls, filters: Optional[Dict] = None, page: int = 1, page_size: int = 20) -> Dict:
        """列出记录"""
        if not cls._table_name:
            return {'total': 0, 'page': page, 'page_size': page_size, 'records': []}
        
        try:
            conditions = []
            params = []
            
            if filters:
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
            
            where_str = " AND ".join(conditions) if conditions else "1=1"
            
            count_query = f"SELECT COUNT(*) FROM {cls._table_name} WHERE {where_str}"
            total = cls.get_db().fetch_scalar(count_query, tuple(params)) or 0
            
            offset = (page - 1) * page_size
            query = f"SELECT * FROM {cls._table_name} WHERE {where_str} ORDER BY {cls._primary_key} DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            
            rows = cls.get_db().fetch_all(query, tuple(params))
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'records': rows
            }
        except Exception as e:
            import logging
            logging.error(f"列出记录失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'records': []}
    
    @classmethod
    def count(cls, filters: Optional[Dict] = None) -> int:
        """统计记录数"""
        if not cls._table_name:
            return 0
        
        try:
            conditions = []
            params = []
            
            if filters:
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
            
            where_str = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT COUNT(*) FROM {cls._table_name} WHERE {where_str}"
            
            return cls.get_db().fetch_scalar(query, tuple(params)) or 0
        except Exception as e:
            import logging
            logging.error(f"统计记录失败: {str(e)}")
            return 0
