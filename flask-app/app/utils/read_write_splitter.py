# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库读写分离管理器 - 实现自动路由读写操作到主从数据库
"""

import os
import re
import time
import sqlite3
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from contextlib import contextmanager
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('read_write_split')

class OperationType(Enum):
    """操作类型"""
    READ = "read"
    WRITE = "write"
    UNKNOWN = "unknown"

class ReadWriteSplitter:
    """数据库读写分离管理器"""
    
    # SQL关键字映射
    READ_KEYWORDS = [
        'SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'PRAGMA'
    ]
    
    WRITE_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 
        'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE'
    ]
    
    def __init__(self, config: Dict = None):
        """初始化读写分离管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or self._default_config()
        
        # 主从数据库映射
        self.master_databases = self.config.get('master_databases', ['users', 'system'])
        self.slave_databases = self.config.get('slave_databases', 
            ['questions', 'exams', 'api', 'route', 'customs'])
        
        # 连接池
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'read_operations': 0,
            'write_operations': 0,
            'read_from_master': 0,
            'read_from_slave': 0,
            'write_to_master': 0,
            'transaction_count': 0,
            'errors': 0
        }
        
        # 读写分离开关
        self.enabled = self.config.get('enabled', True)
        self.force_master_read = self.config.get('force_master_read', False)
        self.read_replication_lag = self.config.get('read_replication_lag', 1)  # 秒
        
        logger.info("读写分离管理器初始化完成")
        logger.info(f"主数据库: {self.master_databases}")
        logger.info(f"从数据库: {self.slave_databases}")
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'enabled': True,
            'force_master_read': False,
            'read_replication_lag': 1,
            'master_databases': ['users', 'system'],
            'slave_databases': ['questions', 'exams', 'api', 'route', 'customs'],
            'database_dir': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/databases',
            'connection_pool_size': 5,
            'connection_timeout': 30
        }
    
    def _identify_operation(self, sql: str) -> OperationType:
        """识别SQL操作类型
        
        Args:
            sql: SQL语句
        
        Returns:
            操作类型
        """
        sql_upper = sql.strip().upper()
        
        # 检查是否包含写操作关键字
        for keyword in self.WRITE_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                return OperationType.WRITE
        
        # 检查是否包含读操作关键字
        for keyword in self.READ_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                return OperationType.READ
        
        return OperationType.UNKNOWN
    
    def _determine_database_role(self, db_name: str, operation: OperationType) -> str:
        """确定数据库角色
        
        Args:
            db_name: 数据库名称
            operation: 操作类型
        
        Returns:
            'master' 或 'slave'
        """
        # 写操作必须使用主数据库
        if operation == OperationType.WRITE:
            return 'master'
        
        # 读操作判断
        if operation == OperationType.READ:
            # 如果强制使用主数据库
            if self.force_master_read:
                return 'master'
            
            # 如果是从数据库
            if db_name in self.slave_databases:
                return 'slave'
            
            # 如果是主数据库
            if db_name in self.master_databases:
                # 可以选择使用主库或从库
                return 'slave' if not self.force_master_read else 'master'
        
        # 未知操作默认使用主数据库
        return 'master'
    
    def _get_db_path(self, db_name: str, role: str) -> str:
        """获取数据库文件路径
        
        Args:
            db_name: 数据库名称
            role: 角色(master/slave)
        
        Returns:
            数据库文件路径
        """
        db_dir = self.config.get('database_dir')
        return os.path.join(db_dir, f"{db_name}.db")
    
    def _get_connection(self, db_name: str, role: str) -> Optional[sqlite3.Connection]:
        """获取数据库连接
        
        Args:
            db_name: 数据库名称
            role: 角色(master/slave)
        
        Returns:
            数据库连接
        """
        key = f"{db_name}_{role}"
        
        with self.lock:
            if key in self.connections and self.connections[key]['connection']:
                conn_info = self.connections[key]
                # 检查连接是否有效
                try:
                    conn_info['connection'].execute("SELECT 1")
                    return conn_info['connection']
                except Exception:
                    # 连接无效,重新创建
                    pass
            
            # 创建新连接
            db_path = self._get_db_path(db_name, role)
            if not os.path.exists(db_path):
                logger.error(f"数据库文件不存在: {db_path}")
                return None
            
            try:
                conn = sqlite3.connect(db_path, timeout=30)
                conn.row_factory = sqlite3.Row
                
                self.connections[key] = {
                    'connection': conn,
                    'created_at': time.time(),
                    'last_used': time.time()
                }
                
                logger.debug(f"创建数据库连接: {key}")
                return conn
            
            except Exception as e:
                logger.error(f"创建数据库连接失败 [{key}]: {e}")
                self.stats['errors'] += 1
                return None
    
    def execute(self, db_name: str, sql: str, params: Tuple = None, 
                force_master: bool = False) -> Optional[Any]:
        """执行SQL语句
        
        Args:
            db_name: 数据库名称
            sql: SQL语句
            params: 参数元组
            force_master: 强制使用主数据库
        
        Returns:
            执行结果
        """
        if not self.enabled:
            return self._execute_simple(db_name, sql, params)
        
        operation = self._identify_operation(sql)
        role = self._determine_database_role(db_name, operation)
        
        # 如果强制使用主数据库
        if force_master:
            role = 'master'
        
        conn = self._get_connection(db_name, role)
        if not conn:
            logger.error(f"无法获取数据库连接: {db_name}")
            return None
        
        try:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # 根据操作类型更新统计
            if operation == OperationType.WRITE:
                self.stats['write_operations'] += 1
                self.stats['write_to_master'] += 1
                conn.commit()
            else:
                self.stats['read_operations'] += 1
                if role == 'master':
                    self.stats['read_from_master'] += 1
                else:
                    self.stats['read_from_slave'] += 1
            
            return cursor
        
        except Exception as e:
            logger.error(f"SQL执行失败 [{db_name}/{role}]: {e}")
            logger.error(f"SQL: {sql}")
            conn.rollback()
            self.stats['errors'] += 1
            return None
    
    def _execute_simple(self, db_name: str, sql: str, params: Tuple = None) -> Optional[Any]:
        """简单执行(不进行读写分离)"""
        db_dir = self.config.get('database_dir')
        db_path = os.path.join(db_dir, f"{db_name}.db")
        
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            return None
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            conn.commit()
            return cursor
        
        except Exception as e:
            logger.error(f"SQL执行失败 [{db_name}]: {e}")
            conn.rollback()
            return None
    
    def query(self, db_name: str, sql: str, params: Tuple = None,
              force_master: bool = False) -> List:
        """查询数据
        
        Args:
            db_name: 数据库名称
            sql: SQL语句
            params: 参数元组
            force_master: 强制使用主数据库
        
        Returns:
            查询结果列表
        """
        cursor = self.execute(db_name, sql, params, force_master)
        
        if cursor:
            try:
                return cursor.fetchall()
            except Exception:
                return []
        
        return []
    
    def insert(self, db_name: str, table: str, data: Dict) -> bool:
        """插入数据
        
        Args:
            db_name: 数据库名称
            table: 表名
            data: 数据字典
        
        Returns:
            是否成功
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.keys()])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.execute(db_name, sql, tuple(data.values()))
        return cursor is not None
    
    def update(self, db_name: str, table: str, data: Dict, where: str,
               where_params: Tuple = ()) -> int:
        """更新数据
        
        Args:
            db_name: 数据库名称
            table: 表名
            data: 数据字典
            where: WHERE条件
            where_params: WHERE参数
        
        Returns:
            影响的行数
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        params = tuple(data.values()) + where_params
        cursor = self.execute(db_name, sql, params)
        
        if cursor:
            return cursor.rowcount
        
        return 0
    
    def delete(self, db_name: str, table: str, where: str,
               where_params: Tuple = ()) -> int:
        """删除数据
        
        Args:
            db_name: 数据库名称
            table: 表名
            where: WHERE条件
            where_params: WHERE参数
        
        Returns:
            影响的行数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(db_name, sql, where_params)
        
        if cursor:
            return cursor.rowcount
        
        return 0
    
    @contextmanager
    def transaction(self, db_name: str):
        """事务上下文管理器
        
        Args:
            db_name: 数据库名称
        
        Yields:
            数据库连接
        """
        conn = self._get_connection(db_name, 'master')
        
        if not conn:
            raise Exception(f"无法获取数据库连接: {db_name}")
        
        self.stats['transaction_count'] += 1
        start_time = time.time()
        
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
            logger.debug(f"事务提交成功 [{db_name}]: {time.time() - start_time:.3f}秒")
        except Exception as e:
            conn.rollback()
            logger.error(f"事务回滚 [{db_name}]: {e}")
            raise
        finally:
            pass
    
    def get_stats(self) -> Dict:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        total_reads = self.stats['read_operations']
        total_writes = self.stats['write_operations']
        total_ops = total_reads + total_writes
        
        read_ratio = (total_reads / total_ops * 100) if total_ops > 0 else 0
        write_ratio = (total_writes / total_ops * 100) if total_ops > 0 else 0
        
        slave_usage = (self.stats['read_from_slave'] / total_reads * 100) if total_reads > 0 else 0
        
        return {
            'total_operations': total_ops,
            'read_operations': total_reads,
            'write_operations': total_writes,
            'read_ratio': f"{read_ratio:.2f}%",
            'write_ratio': f"{write_ratio:.2f}%",
            'read_from_master': self.stats['read_from_master'],
            'read_from_slave': self.stats['read_from_slave'],
            'slave_usage': f"{slave_usage:.2f}%",
            'write_to_master': self.stats['write_to_master'],
            'transaction_count': self.stats['transaction_count'],
            'errors': self.stats['errors'],
            'active_connections': len(self.connections)
        }
    
    def close_all(self):
        """关闭所有连接"""
        with self.lock:
            for key, conn_info in self.connections.items():
                try:
                    if conn_info['connection']:
                        conn_info['connection'].close()
                        logger.debug(f"关闭数据库连接: {key}")
                except Exception as e:
                    logger.error(f"关闭连接失败 [{key}]: {e}")
            
            self.connections.clear()

# 全局实例
read_write_splitter = ReadWriteSplitter()

def get_read_write_splitter() -> ReadWriteSplitter:
    """获取读写分离管理器实例"""
    return read_write_splitter

# 便捷函数
def rw_execute(db_name: str, sql: str, params: Tuple = None):
    """执行SQL(自动读写分离)"""
    return read_write_splitter.execute(db_name, sql, params)

def rw_query(db_name: str, sql: str, params: Tuple = None):
    """查询数据"""
    return read_write_splitter.query(db_name, sql, params)

def rw_insert(db_name: str, table: str, data: Dict):
    """插入数据"""
    return read_write_splitter.insert(db_name, table, data)

def rw_update(db_name: str, table: str, data: Dict, where: str, where_params: Tuple = ()):
    """更新数据"""
    return read_write_splitter.update(db_name, table, data, where, where_params)

def rw_delete(db_name: str, table: str, where: str, where_params: Tuple = ()):
    """删除数据"""
    return read_write_splitter.delete(db_name, table, where, where_params)

def rw_stats():
    """获取统计信息"""
    return read_write_splitter.get_stats()

if __name__ == '__main__':
    # 测试读写分离
    splitter = ReadWriteSplitter()
    
    print("🚀 读写分离测试")
    print("=" * 50)
    
    # 测试读取(应该路由到从数据库)
    print("\n📝 测试1: 读取questions数据库")
    result = splitter.query('questions', 'SELECT * FROM questions LIMIT 3')
    print(f"  查询结果数: {len(result)}")
    stats = splitter.get_stats()
    print(f"  读操作: {stats['read_operations']}")
    print(f"  从从库读取: {stats['read_from_slave']}")
    
    # 测试写入(应该路由到主数据库)
    print("\n📝 测试2: 写入users数据库")
    success = splitter.insert('users', 'users', {
        'username': 'test_user',
        'email': 'test@example.com',
        'password_hash': 'hashed_password'
    })
    print(f"  插入结果: {'成功' if success else '失败'}")
    stats = splitter.get_stats()
    print(f"  写操作: {stats['write_operations']}")
    print(f"  写入主库: {stats['write_to_master']}")
    
    # 最终统计
    print("\n📊 最终统计:")
    stats = splitter.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    splitter.close_all()
    print("\n🎉 测试完成!")
