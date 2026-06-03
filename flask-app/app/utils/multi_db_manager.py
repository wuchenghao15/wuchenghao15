# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库管理器 - 支持数据分离和读写分离
"""

import sqlite3
import os
import logging
from flask import current_app
import sys

logger = logging.getLogger(__name__)

class DatabaseManager:
    """多数据库管理类"""
    
    _connections = {}
    
    @classmethod
    def get_connection(cls, db_name):
        """获取数据库连接"""
        if db_name in cls._connections:
            return cls._connections[db_name]
        
        # 获取数据库路径
        db_path = cls._get_db_path(db_name)
        if not db_path:
            logger.error(f"数据库 {db_name} 配置不存在")
            return None
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cls._connections[db_name] = conn
            logger.debug(f"建立数据库连接: {db_name}")
            return conn
        except Exception as e:
            logger.error(f"连接数据库 {db_name} 失败: {e}")
            return None
    
    @classmethod
    def _get_db_path(cls, db_name):
        """获取数据库文件路径"""
        try:
            # 从Flask配置获取
            if hasattr(current_app, 'config'):
                db_dir = current_app.config.get('DATABASE_DIR', 'databases')
                databases = current_app.config.get('DATABASES', {})
                if db_name in databases:
                    return os.path.join(db_dir, databases[db_name]['file'])
        except Exception:
            pass
        
        # 默认路径
        return os.path.join('databases', f"{db_name}.db")
    
    @classmethod
    def execute(cls, db_name, sql, params=None):
        """执行SQL语句"""
        conn = cls.get_connection(db_name)
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor
        except Exception as e:
            logger.error(f"执行SQL失败 [{db_name}]: {e}")
            conn.rollback()
            return None
    
    @classmethod
    def query(cls, db_name, sql, params=None):
        """查询数据"""
        conn = cls.get_connection(db_name)
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询失败 [{db_name}]: {e}")
            return []
    
    @classmethod
    def close_all(cls):
        """关闭所有连接"""
        for db_name, conn in cls._connections.items():
            try:
                conn.close()
                logger.debug(f"关闭数据库连接: {db_name}")
            except Exception as e:
                logger.error(f"关闭连接失败 [{db_name}]: {e}")
        cls._connections.clear()
    
    @classmethod
    def get_master_databases(cls):
        """获取主数据库列表"""
        try:
            if hasattr(current_app, 'config'):
                databases = current_app.config.get('DATABASES', {})
                return [name for name, info in databases.items() if info.get('role') == 'master']
        except Exception:
            pass
        return ['users', 'system']
    
    @classmethod
    def get_slave_databases(cls):
        """获取从数据库列表"""
        try:
            if hasattr(current_app, 'config'):
                databases = current_app.config.get('DATABASES', {})
                return [name for name, info in databases.items() if info.get('role') == 'slave']
        except Exception:
            pass
        return ['questions', 'exams', 'api', 'route', 'customs']

# 便捷函数
def get_db(db_name):
    """获取数据库连接"""
    return DatabaseManager.get_connection(db_name)

def db_execute(db_name, sql, params=None):
    """执行SQL"""
    return DatabaseManager.execute(db_name, sql, params)

def db_query(db_name, sql, params=None):
    """查询数据"""
    return DatabaseManager.query(db_name, sql, params)
