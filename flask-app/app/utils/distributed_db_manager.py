# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式数据库管理器 - 支持分库分表、数据分片、分布式事务
"""

import os
import time
import hashlib
import json
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('distributed_db')

class ShardingStrategy(Enum):
    """分片策略枚举"""
    HASH = "hash"           # 按哈希分片
    RANGE = "range"         # 按范围分片
    MODULO = "modulo"       # 按取模分片
    GEO = "geo"             # 按地理区域分片
    TIME = "time"           # 按时间分片
    CUSTOM = "custom"       # 自定义分片

class DistributionMode(Enum):
    """分布模式"""
    HORIZONTAL = "horizontal"    # 水平分表
    VERTICAL = "vertical"        # 垂直分库
    HYBRID = "hybrid"            # 混合模式

class DistributedDatabaseManager:
    """分布式数据库管理器"""
    
    def __init__(self, config: Dict = None):
        """初始化分布式数据库管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or self._default_config()
        
        # 分片配置
        self.sharding_strategy = ShardingStrategy(self.config.get('sharding_strategy', 'hash'))
        self.shard_count = self.config.get('shard_count', 4)
        self.replica_count = self.config.get('replica_count', 2)
        
        # 数据库分片映射
        self.shards = self._init_shards()
        self.tables = self.config.get('tables', {})
        
        # 连接池
        self.connections: Dict[str, Any] = {}
        
        # 分布式事务
        self.transactions = {}
        
        # 统计信息
        self.stats = {
            'queries': 0,
            'transactions': 0,
            'cross_shard_queries': 0,
            'errors': 0,
            'data_distribution': {}
        }
        
        logger.info("分布式数据库管理器初始化完成")
        logger.info(f"分片策略: {self.sharding_strategy.value}")
        logger.info(f"分片数量: {self.shard_count}")
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'enabled': True,
            'sharding_strategy': 'hash',
            'shard_count': 4,
            'replica_count': 2,
            'database_dir': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/databases',
            'distributed_transactions': True,
            'cross_shard_query': True,
            'consistency_level': 'eventual',  # eventual, strong, session
            
            # 分表配置
            'tables': {
                'users': {
                    'sharded': True,
                    'shard_key': 'id',
                    'strategy': 'hash',
                    'shards': 4
                },
                'orders': {
                    'sharded': True,
                    'shard_key': 'user_id',
                    'strategy': 'hash',
                    'shards': 4
                },
                'logs': {
                    'sharded': True,
                    'shard_key': 'created_at',
                    'strategy': 'time',
                    'shards': 12  # 按月分片
                },
                'config': {
                    'sharded': False
                }
            },
            
            # 节点配置
            'nodes': {
                'node-1': {'host': '127.0.0.1', 'port': 5000, 'role': 'master'},
                'node-2': {'host': '127.0.0.1', 'port': 5001, 'role': 'replica'},
                'node-3': {'host': '127.0.0.1', 'port': 5002, 'role': 'replica'},
                'node-4': {'host': '127.0.0.1', 'port': 5003, 'role': 'replica'}
            }
        }
    
    def _init_shards(self) -> Dict:
        """初始化分片映射"""
        shards = {}
        
        for table_name, table_config in self.config.get('tables', {}).items():
            if not table_config.get('sharded', False):
                shards[table_name] = {'type': 'single', 'db': table_name}
                continue
            
            strategy = table_config.get('strategy', 'hash')
            num_shards = table_config.get('shards', 4)
            
            table_shards = []
            for i in range(num_shards):
                shard_name = f"{table_name}_shard_{i}"
                table_shards.append(shard_name)
            
            shards[table_name] = {
                'type': 'sharded',
                'strategy': strategy,
                'shards': table_shards,
                'shard_key': table_config.get('shard_key', 'id'),
                'num_shards': num_shards
            }
        
        return shards
    
    def _hash_shard(self, value, num_shards: int) -> int:
        """哈希分片"""
        if isinstance(value, int):
            return value % num_shards
        return int(hashlib.md5(str(value).encode()).hexdigest(), 16) % num_shards
    
    def _range_shard(self, value, num_shards: int) -> int:
        """范围分片"""
        ranges = [i * (100 // num_shards) for i in range(num_shards + 1)]
        for i in range(num_shards):
            if ranges[i] <= value < ranges[i + 1]:
                return i
        return num_shards - 1
    
    def _time_shard(self, value, num_shards: int) -> int:
        """时间分片(按月)"""
        import datetime
        if isinstance(value, str):
            value = datetime.datetime.fromisoformat(value)
        return value.month - 1
    
    def _geo_shard(self, value, num_shards: int) -> int:
        """地理分片"""
        region_map = {'asia': 0, 'europe': 1, 'america': 2, 'other': 3}
        return region_map.get(value.lower(), num_shards - 1)
    
    def get_shard(self, table_name: str, shard_key_value) -> str:
        """获取分片名称
        
        Args:
            table_name: 表名
            shard_key_value: 分片键值
        
        Returns:
            分片名称
        """
        table_info = self.shards.get(table_name)
        
        if not table_info or table_info['type'] == 'single':
            return table_info.get('db', table_name)
        
        strategy = table_info.get('strategy', 'hash')
        num_shards = table_info.get('num_shards', 4)
        shards = table_info.get('shards', [])
        
        if strategy == 'hash':
            index = self._hash_shard(shard_key_value, num_shards)
        elif strategy == 'range':
            index = self._range_shard(shard_key_value, num_shards)
        elif strategy == 'time':
            index = self._time_shard(shard_key_value, num_shards)
        elif strategy == 'geo':
            index = self._geo_shard(shard_key_value, num_shards)
        else:
            index = self._hash_shard(shard_key_value, num_shards)
        
        return shards[index]
    
    def get_all_shards(self, table_name: str) -> List[str]:
        """获取表的所有分片"""
        table_info = self.shards.get(table_name)
        
        if not table_info or table_info['type'] == 'single':
            return [table_info.get('db', table_name)]
        
        return table_info.get('shards', [])
    
    def _get_connection(self, db_name: str) -> Any:
        """获取数据库连接"""
        if db_name in self.connections:
            return self.connections[db_name]
        
        import sqlite3
        db_dir = self.config.get('database_dir')
        db_path = os.path.join(db_dir, f"{db_name}.db")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        self.connections[db_name] = conn
        
        # 初始化表结构(如果不存在)
        self._init_table_schema(db_name)
        
        return conn
    
    def _init_table_schema(self, db_name: str):
        """初始化表结构"""
        # 根据分片名称推断原始表名
        if '_shard_' in db_name:
            table_name = db_name.split('_shard_')[0]
        else:
            table_name = db_name
        
        # 创建对应的表(简化示例)
        conn = self.connections[db_name]
        cursor = conn.cursor()
        
        # 根据表名创建相应的表结构
        table_schemas = {
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'orders': '''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'logs': '''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        if table_name in table_schemas:
            cursor.execute(table_schemas[table_name])
            conn.commit()
    
    def insert(self, table_name: str, data: Dict, shard_key_value = None) -> bool:
        """插入数据
        
        Args:
            table_name: 表名
            data: 数据字典
            shard_key_value: 分片键值(可选,自动从data中提取)
        
        Returns:
            是否成功
        """
        # 获取分片键值
        if shard_key_value is None:
            table_info = self.shards.get(table_name)
            shard_key = table_info.get('shard_key', 'id') if table_info else 'id'
            shard_key_value = data.get(shard_key)
        
        # 获取目标分片
        shard = self.get_shard(table_name, shard_key_value)
        
        # 执行插入
        conn = self._get_connection(shard)
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.keys()])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor.execute(sql, tuple(data.values()))
            conn.commit()
            
            # 更新统计
            self.stats['queries'] += 1
            if shard not in self.stats['data_distribution']:
                self.stats['data_distribution'][shard] = 0
            self.stats['data_distribution'][shard] += 1
            
            return True
        except Exception as e:
            logger.error(f"插入失败 [{shard}]: {e}")
            conn.rollback()
            self.stats['errors'] += 1
            return False
    
    def query(self, table_name: str, sql: str, params: Tuple = None, 
              shard_key_value = None) -> List:
        """查询数据
        
        Args:
            table_name: 表名
            sql: SQL语句
            params: 参数元组
            shard_key_value: 分片键值(可选)
        
        Returns:
            查询结果
        """
        if shard_key_value is not None:
            # 单分片查询
            shard = self.get_shard(table_name, shard_key_value)
            conn = self._get_connection(shard)
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                self.stats['queries'] += 1
                return cursor.fetchall()
            except Exception as e:
                logger.error(f"查询失败 [{shard}]: {e}")
                self.stats['errors'] += 1
                return []
        else:
            # 跨分片查询
            results = []
            shards = self.get_all_shards(table_name)
            
            for shard in shards:
                conn = self._get_connection(shard)
                cursor = conn.cursor()
                
                try:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    results.extend(cursor.fetchall())
                except Exception as e:
                    logger.error(f"跨分片查询失败 [{shard}]: {e}")
            
            self.stats['queries'] += 1
            self.stats['cross_shard_queries'] += 1
            
            return results
    
    def update(self, table_name: str, data: Dict, where: str, where_params: Tuple = (),
               shard_key_value = None) -> int:
        """更新数据"""
        if shard_key_value is not None:
            shard = self.get_shard(table_name, shard_key_value)
            conn = self._get_connection(shard)
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
            
            params = tuple(data.values()) + where_params
            
            try:
                cursor.execute(sql, params)
                conn.commit()
                self.stats['queries'] += 1
                return cursor.rowcount
            except Exception as e:
                logger.error(f"更新失败 [{shard}]: {e}")
                conn.rollback()
                self.stats['errors'] += 1
                return 0
        else:
            # 跨分片更新
            total_updated = 0
            shards = self.get_all_shards(table_name)
            
            for shard in shards:
                conn = self._get_connection(shard)
                cursor = conn.cursor()
                
                set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
                params = tuple(data.values()) + where_params
                
                try:
                    cursor.execute(sql, params)
                    conn.commit()
                    total_updated += cursor.rowcount
                except Exception as e:
                    logger.error(f"跨分片更新失败 [{shard}]: {e}")
                    conn.rollback()
            
            self.stats['queries'] += 1
            self.stats['cross_shard_queries'] += 1
            return total_updated
    
    def delete(self, table_name: str, where: str, where_params: Tuple = (),
               shard_key_value = None) -> int:
        """删除数据"""
        if shard_key_value is not None:
            shard = self.get_shard(table_name, shard_key_value)
            conn = self._get_connection(shard)
            cursor = conn.cursor()
            
            sql = f"DELETE FROM {table_name} WHERE {where}"
            
            try:
                cursor.execute(sql, where_params)
                conn.commit()
                self.stats['queries'] += 1
                return cursor.rowcount
            except Exception as e:
                logger.error(f"删除失败 [{shard}]: {e}")
                conn.rollback()
                self.stats['errors'] += 1
                return 0
        else:
            # 跨分片删除
            total_deleted = 0
            shards = self.get_all_shards(table_name)
            
            for shard in shards:
                conn = self._get_connection(shard)
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {table_name} WHERE {where}"
                
                try:
                    cursor.execute(sql, where_params)
                    conn.commit()
                    total_deleted += cursor.rowcount
                except Exception as e:
                    logger.error(f"跨分片删除失败 [{shard}]: {e}")
                    conn.rollback()
            
            self.stats['queries'] += 1
            self.stats['cross_shard_queries'] += 1
            return total_deleted
    
    @contextmanager
    def distributed_transaction(self, transaction_id: str = None):
        """分布式事务上下文管理器"""
        if transaction_id is None:
            transaction_id = f"tx_{int(time.time())}_{id(threading.current_thread())}"
        
        self.stats['transactions'] += 1
        
        # 记录参与事务的连接
        participating_conns = []
        
        try:
            yield DistributedTransaction(transaction_id, participating_conns)
            # 提交
            for conn in participating_conns:
                conn.commit()
            logger.info(f"分布式事务提交成功: {transaction_id}")
        except Exception as e:
            # 回滚
            for conn in participating_conns:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"分布式事务回滚: {transaction_id}, 错误: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'sharding_strategy': self.sharding_strategy.value,
            'shard_count': self.shard_count,
            'tables': len(self.shards),
            'sharded_tables': sum(1 for info in self.shards.values() if info['type'] == 'sharded'),
            'queries': self.stats['queries'],
            'transactions': self.stats['transactions'],
            'cross_shard_queries': self.stats['cross_shard_queries'],
            'errors': self.stats['errors'],
            'data_distribution': self.stats['data_distribution']
        }
    
    def close_all(self):
        """关闭所有连接"""
        for db_name, conn in self.connections.items():
            try:
                conn.close()
            except Exception as e:
                logger.error(f"关闭连接失败 [{db_name}]: {e}")
        self.connections.clear()

class DistributedTransaction:
    """分布式事务"""
    
    def __init__(self, transaction_id: str, participating_conns: List):
        self.transaction_id = transaction_id
        self.participating_conns = participating_conns
    
    def add_connection(self, conn):
        """添加参与事务的连接"""
        if conn not in self.participating_conns:
            self.participating_conns.append(conn)

# 全局实例
distributed_db_manager = DistributedDatabaseManager()

def get_distributed_db_manager() -> DistributedDatabaseManager:
    """获取分布式数据库管理器实例"""
    return distributed_db_manager

# 便捷函数
def db_insert(table_name: str, data: Dict, shard_key_value = None):
    """插入数据"""
    return distributed_db_manager.insert(table_name, data, shard_key_value)

def db_query(table_name: str, sql: str, params: Tuple = None, shard_key_value = None):
    """查询数据"""
    return distributed_db_manager.query(table_name, sql, params, shard_key_value)

def db_update(table_name: str, data: Dict, where: str, where_params: Tuple = (), shard_key_value = None):
    """更新数据"""
    return distributed_db_manager.update(table_name, data, where, where_params, shard_key_value)

def db_delete(table_name: str, where: str, where_params: Tuple = (), shard_key_value = None):
    """删除数据"""
    return distributed_db_manager.delete(table_name, where, where_params, shard_key_value)

def db_stats():
    """获取统计信息"""
    return distributed_db_manager.get_stats()

if __name__ == '__main__':
    # 测试分布式数据库
    db = DistributedDatabaseManager()
    
    print("🚀 分布式数据库测试")
    print("=" * 60)
    
    # 测试1: 插入数据(自动分片)
    print("\n📝 测试1: 插入用户数据")
    for i in range(10):
        success = db.insert('users', {
            'id': i + 1,
            'username': f'user_{i + 1}',
            'email': f'user_{i + 1}@example.com',
            'password_hash': 'hashed'
        })
        print(f"  用户 {i+1}: {'成功' if success else '失败'}")
    
    # 测试2: 查询数据(单分片)
    print("\n📝 测试2: 单分片查询")
    result = db.query('users', 'SELECT * FROM users WHERE id = ?', (5,), shard_key_value=5)
    print(f"  查询结果: {len(result)} 条")
    if result:
        print(f"  用户信息: {dict(result[0])}")
    
    # 测试3: 跨分片查询
    print("\n📝 测试3: 跨分片查询")
    result = db.query('users', 'SELECT COUNT(*) as cnt FROM users')
    print(f"  总用户数: {dict(result[0])['cnt'] if result else 0}")
    
    # 测试4: 更新数据
    print("\n📝 测试4: 更新数据")
    rowcount = db.update('users', {'email': 'updated@example.com'}, 'username = ?', ('user_1',), shard_key_value=1)
    print(f"  更新行数: {rowcount}")
    
    # 测试5: 统计信息
    print("\n📊 统计信息:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    db.close_all()
    print("\n🎉 测试完成!")
