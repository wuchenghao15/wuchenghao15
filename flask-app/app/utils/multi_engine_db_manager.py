#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多引擎数据库连接管理器 - 支持主从库使用不同数据库引擎
主库：SQLite（轻量级，适合写操作）
从库：PostgreSQL（高性能，适合读操作）
"""

import sqlite3
import threading
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime

logger = __import__('logging').getLogger(__name__)


class DatabaseEngine(Enum):
    """数据库引擎类型"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DBStatus(Enum):
    """数据库状态"""
    ACTIVE = "active"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


class MultiEngineDBManager:
    """多引擎数据库管理器"""
    
    def __init__(self, config_path: str = None):
        self._master_conn = None
        self._master_engine = None
        self._slave_conn = None
        self._slave_engine = None
        self._fallback_conn = None
        
        self._master_status = DBStatus.DOWN
        self._slave_status = DBStatus.DOWN
        self._fallback_status = DBStatus.DOWN
        
        self._lock = threading.RLock()
        
        if config_path:
            self._load_config(config_path)
        
        logger.info("多引擎数据库管理器初始化完成")
    
    def _load_config(self, config_path: str):
        """加载数据库配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"数据库配置加载成功: {config_path}")
        except Exception as e:
            logger.error(f"数据库配置加载失败: {str(e)}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "master": {
                "engine": "sqlite",
                "connection_string": "sqlite:///databases/master.db"
            },
            "slave": {
                "engine": "postgresql",
                "connection_string": "postgresql://admin:password@localhost:5432/mtscos_slave"
            },
            "fallback": {
                "engine": "sqlite",
                "connection_string": "sqlite:///databases/fallback.db"
            }
        }
    
    def _parse_connection_string(self, conn_str: str) -> Dict:
        """解析连接字符串"""
        parts = conn_str.split('://')
        engine = parts[0]
        
        if engine == 'sqlite':
            db_path = parts[1]
            return {
                'engine': DatabaseEngine.SQLITE,
                'path': db_path
            }
        elif engine == 'postgresql':
            # postgresql://username:password@host:port/database
            auth_part = parts[1].split('@')
            credentials = auth_part[0].split(':')
            host_part = auth_part[1].split('/')
            
            return {
                'engine': DatabaseEngine.POSTGRESQL,
                'username': credentials[0],
                'password': credentials[1] if len(credentials) > 1 else '',
                'host': host_part[0].split(':')[0],
                'port': int(host_part[0].split(':')[1]) if ':' in host_part[0] else 5432,
                'database': host_part[1]
            }
        return {}
    
    def connect_master(self) -> bool:
        """连接主库（SQLite）"""
        try:
            with self._lock:
                config = self._config.get('master', {})
                conn_info = self._parse_connection_string(config.get('connection_string', 'sqlite:///master.db'))
                
                if conn_info['engine'] == DatabaseEngine.SQLITE:
                    db_path = conn_info['path']
                    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
                    self._master_conn = sqlite3.connect(db_path)
                    self._master_conn.row_factory = sqlite3.Row
                    self._master_engine = DatabaseEngine.SQLITE
                    self._master_status = DBStatus.HEALTHY
                    logger.info("主库(SQLite)连接成功")
                    return True
                else:
                    logger.error("主库必须使用SQLite引擎")
                    return False
        except Exception as e:
            logger.error(f"主库连接失败: {str(e)}")
            self._master_status = DBStatus.DOWN
            return False
    
    def connect_slave(self) -> bool:
        """连接从库（PostgreSQL）"""
        try:
            with self._lock:
                config = self._config.get('slave', {})
                conn_info = self._parse_connection_string(config.get('connection_string', ''))
                
                if conn_info['engine'] == DatabaseEngine.POSTGRESQL:
                    try:
                        import psycopg2
                        self._slave_conn = psycopg2.connect(
                            host=conn_info['host'],
                            port=conn_info['port'],
                            dbname=conn_info['database'],
                            user=conn_info['username'],
                            password=conn_info['password']
                        )
                        self._slave_conn.autocommit = True
                        self._slave_engine = DatabaseEngine.POSTGRESQL
                        self._slave_status = DBStatus.HEALTHY
                        logger.info("从库(PostgreSQL)连接成功")
                        return True
                    except ImportError:
                        logger.warning("psycopg2未安装，回退到SQLite")
                        return self._connect_slave_fallback()
                    except Exception as e:
                        logger.warning(f"PostgreSQL连接失败，尝试回退: {str(e)}")
                        return self._connect_slave_fallback()
                else:
                    return self._connect_slave_fallback()
        except Exception as e:
            logger.error(f"从库连接失败: {str(e)}")
            self._slave_status = DBStatus.DOWN
            return False
    
    def _connect_slave_fallback(self) -> bool:
        """从库回退到SQLite"""
        try:
            db_path = 'databases/slave_fallback.db'
            os.makedirs('databases', exist_ok=True)
            self._slave_conn = sqlite3.connect(db_path)
            self._slave_conn.row_factory = sqlite3.Row
            self._slave_engine = DatabaseEngine.SQLITE
            self._slave_status = DBStatus.HEALTHY
            logger.info("从库回退到SQLite连接成功")
            return True
        except Exception as e:
            logger.error(f"从库回退连接失败: {str(e)}")
            return False
    
    def connect_fallback(self) -> bool:
        """连接备用数据库"""
        try:
            with self._lock:
                config = self._config.get('fallback', {})
                conn_str = config.get('connection_string', 'sqlite:///fallback.db')
                conn_info = self._parse_connection_string(conn_str)
                
                db_path = conn_info.get('path', 'fallback.db')
                os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
                self._fallback_conn = sqlite3.connect(db_path)
                self._fallback_conn.row_factory = sqlite3.Row
                self._fallback_status = DBStatus.HEALTHY
                logger.info("备用数据库连接成功")
                return True
        except Exception as e:
            logger.error(f"备用数据库连接失败: {str(e)}")
            self._fallback_status = DBStatus.DOWN
            return False
    
    def disconnect_all(self):
        """断开所有连接"""
        with self._lock:
            if self._master_conn:
                self._master_conn.close()
                self._master_status = DBStatus.DOWN
            if self._slave_conn:
                self._slave_conn.close()
                self._slave_status = DBStatus.DOWN
            if self._fallback_conn:
                self._fallback_conn.close()
                self._fallback_status = DBStatus.DOWN
            logger.info("所有数据库连接已断开")
    
    def execute_write(self, query: str, params: tuple = ()) -> Any:
        """执行写操作（主库）"""
        return self._execute(self._master_conn, self._master_engine, query, params, write=True)
    
    def execute_read(self, query: str, params: tuple = ()) -> Any:
        """执行读操作（从库，失败时回退到主库）"""
        result = self._execute(self._slave_conn, self._slave_engine, query, params, write=False)
        if result is None and self._slave_status != DBStatus.HEALTHY:
            logger.warning("从库不可用，使用主库进行读操作")
            return self._execute(self._master_conn, self._master_engine, query, params, write=False)
        return result
    
    def _execute(self, conn, engine: DatabaseEngine, query: str, params: tuple, write: bool) -> Any:
        """执行查询"""
        if not conn:
            logger.error("数据库连接未建立")
            return None
        
        try:
            cursor = conn.cursor()
            
            if engine == DatabaseEngine.POSTGRESQL:
                # PostgreSQL参数使用%s占位符
                pg_query = query.replace('?', '%s')
                cursor.execute(pg_query, params)
            else:
                cursor.execute(query, params)
            
            if write:
                conn.commit()
            
            return cursor
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            if write and conn:
                conn.rollback()
            return None
    
    def fetch_one(self, query: str, params: tuple = (), read_only: bool = True) -> Optional[Dict[str, Any]]:
        """获取单条记录"""
        if read_only:
            cursor = self.execute_read(query, params)
        else:
            cursor = self.execute_write(query, params)
        
        if cursor:
            row = cursor.fetchone()
            if row:
                if self._slave_engine == DatabaseEngine.POSTGRESQL:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return dict(row)
        return None
    
    def fetch_all(self, query: str, params: tuple = (), read_only: bool = True) -> List[Dict[str, Any]]:
        """获取多条记录"""
        if read_only:
            cursor = self.execute_read(query, params)
        else:
            cursor = self.execute_write(query, params)
        
        if cursor:
            rows = cursor.fetchall()
            if self._slave_engine == DatabaseEngine.POSTGRESQL:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return [dict(row) for row in rows]
        return []
    
    def get_status(self) -> Dict[str, str]:
        """获取数据库状态"""
        return {
            'master': self._master_status.value,
            'master_engine': self._master_engine.value if self._master_engine else 'unknown',
            'slave': self._slave_status.value,
            'slave_engine': self._slave_engine.value if self._slave_engine else 'unknown',
            'fallback': self._fallback_status.value
        }
    
    def replicate_to_slave(self, table_name: str):
        """将主库表数据复制到从库"""
        if self._master_status != DBStatus.HEALTHY or self._slave_status != DBStatus.HEALTHY:
            logger.error("主库或从库不可用，无法复制")
            return False
        
        try:
            # 从主库读取数据
            cursor = self.execute_read(f"SELECT * FROM {table_name}", read_only=False)
            if not cursor:
                return False
            
            rows = cursor.fetchall()
            if not rows:
                logger.info(f"表 {table_name} 没有数据")
                return True
            
            # 获取列名
            if self._master_engine == DatabaseEngine.SQLITE:
                columns = [desc[0] for desc in cursor.description]
            else:
                columns = [desc[0] for desc in cursor.description]
            
            # 在从库创建表并插入数据
            placeholders = ','.join(['?' if self._slave_engine == DatabaseEngine.SQLITE else '%s'] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                self.execute_write(insert_query, tuple(row))
            
            logger.info(f"成功复制 {len(rows)} 条记录到从库表 {table_name}")
            return True
        except Exception as e:
            logger.error(f"数据复制失败: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, bool]:
        """执行健康检查"""
        results = {}
        
        # 检查主库
        try:
            if self._master_conn:
                cursor = self._master_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                self._master_status = DBStatus.HEALTHY
                results['master'] = True
            else:
                results['master'] = False
        except Exception as e:
            self._master_status = DBStatus.DOWN
            results['master'] = False
        
        # 检查从库
        try:
            if self._slave_conn:
                cursor = self._slave_conn.cursor()
                cursor.execute("SELECT 1" if self._slave_engine == DatabaseEngine.SQLITE else "SELECT 1;")
                cursor.fetchone()
                self._slave_status = DBStatus.HEALTHY
                results['slave'] = True
            else:
                results['slave'] = False
        except Exception as e:
            self._slave_status = DBStatus.DOWN
            results['slave'] = False
        
        # 检查备用库
        try:
            if self._fallback_conn:
                cursor = self._fallback_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                self._fallback_status = DBStatus.HEALTHY
                results['fallback'] = True
            else:
                results['fallback'] = False
        except Exception as e:
            self._fallback_status = DBStatus.DOWN
            results['fallback'] = False
        
        return results
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect_all()


# 创建全局实例
multi_db_manager = MultiEngineDBManager(
    config_path=os.path.join(os.path.dirname(__file__), '..', '..', 'databases', 'database_config.json')
)


def init_multi_engine_db():
    """初始化多引擎数据库"""
    logger.info("初始化多引擎数据库...")
    
    success = True
    
    # 连接主库（SQLite）
    if not multi_db_manager.connect_master():
        logger.error("主库连接失败")
        success = False
    
    # 连接从库（PostgreSQL优先）
    if not multi_db_manager.connect_slave():
        logger.warning("从库连接失败")
    
    # 连接备用库
    if not multi_db_manager.connect_fallback():
        logger.warning("备用库连接失败")
    
    if success:
        logger.info("多引擎数据库初始化完成")
        logger.info(f"数据库状态: {multi_db_manager.get_status()}")
    
    return success