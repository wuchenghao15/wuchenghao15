#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双数据库管理模块 - 支持主数据库和备份数据库的同步和备份
"""

from contextlib import contextmanager
import threading
import time
from datetime import datetime
from app.utils.db import DatabaseManager
from app.utils.logging import logger

class DatabaseManagerWithConfig:
    """带配置的数据库管理器: 支持自定义配置"""

    def __init__(self, db_type, db_path=None, db_host=None, db_port=None, db_user=None, db_password=None, db_name=None):
        """初始化数据库管理器"""
        # 初始化配置
        self.db_type = db_type
        self.db_path = db_path
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name

        # 尝试导入数据库驱动
        try:
            import mysql.connector
            from mysql.connector.pooling import MySQLConnectionPool
            self.MYSQL_AVAILABLE = True
        except ImportError:
            self.MYSQL_AVAILABLE = False

        try:
            from psycopg2 import pool
            self.POSTGRESQL_AVAILABLE = True
        except ImportError:
            self.POSTGRESQL_AVAILABLE = False

        if self.db_type == 'sqlite':
            # 对于SQLite,使用线程本地存储管理连接
            self._thread_local = threading.local()
        else:
            # 对于其他数据库,使用连接池
            self._connection_pool = []
            self._max_connections = 10
            self._connection_lock = threading.Lock()
            self._init_connection_pool()

        logger.info(f"数据库管理器初始化完成,类型: {self.db_type}")

    def _init_connection_pool(self):
        """初始化连接池"""
        with self._connection_lock:
            for _ in range(self._max_connections):
                conn = self._create_connection()
                if conn:
                    self._connection_pool.append(conn)
        logger.info(f"数据库连接池初始化完成, 创建了 {len(self._connection_pool)} 个连接")

    def _create_connection(self):
        """创建数据库连接"""
        try:
            if self.db_type == 'sqlite':
                import sqlite3
                conn = sqlite3.connect(self.db_path, timeout=30)
                conn.row_factory = sqlite3.Row
                return conn
            elif self.db_type == 'mysql' and self.MYSQL_AVAILABLE:
                import mysql.connector
                conn = mysql.connector.connect(
                    host=self.db_host,
                    user=self.db_user,
                    password=self.db_password,
                    database=self.db_name,
                    charset='utf8mb4'
                )
                return conn
            elif self.db_type == 'postgresql' and self.POSTGRESQL_AVAILABLE:
                from psycopg2 import pool
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    database=self.db_name
                )
                return conn
        except Exception as e:
            logger.error(f"创建数据库连接失败: {str(e)}")
            return None

    def execute(self, query, params=None):
        """执行SQL查询: 自动管理连接"""
        conn = self.get_connection()
        if not conn:
            return None, False
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor, True
        except Exception as e:
            logger.error(f"执行SQL失败: {str(e)}")
            return None, False

    def fetch_one(self, query, params=None):
        """执行查询: 返回单行结果"""
        cursor, success = self.execute(query, params)
        if success and cursor:
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
        return None

    def get_connection(self):
        """获取数据库连接"""
        if self.db_type == 'sqlite':
            if not hasattr(self._thread_local, 'connection'):
                self._thread_local.connection = self._create_connection()
            return self._thread_local.connection
        else:
            with self._connection_lock:
                if self._connection_pool:
                    return self._connection_pool.pop()
                return self._create_connection()


class DualDatabaseManager:
    """双数据库管理器: 支持主数据库和备份数据库的同步"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def _initialize(self):
        """初始化双数据库连接"""
        # 初始化主数据库管理器(使用默认配置)
        self.primary_db = DatabaseManager()
        logger.info("主数据库初始化完成")

        # 初始化备份数据库管理器
        self.backup_db = DatabaseManagerWithConfig(
            db_type='sqlite',
            db_path='instance/mtscos_backup.db'
        )

        self.sync_interval = 3600  # 默认1小时
        self.sync_thread = threading.Thread(target=self._auto_sync, daemon=True)
        self.sync_thread.start()

        self._init_tables()

    def _init_tables(self):
        """初始化表结构: 确保主数据库和备份数据库的表结构一致"""
        # 获取所有表名
        tables = self._get_all_tables()
        for table in tables:
            try:
                self._copy_table_structure(table)
            except Exception as e:
                logger.error(f"初始化表 {table} 结构失败: {str(e)}")

    def _copy_table_structure(self, table):
        """复制表结构到备份数据库"""
        if self.primary_db.db_type == 'sqlite':
            # 获取表结构
            columns = self.primary_db.fetch_all(f"PRAGMA table_info({table})")

            if not columns:
                logger.warning(f"无法获取表 {table} 的结构")
                return

            # 构建创建表语句
            columns_sql = []
            for col in columns:
                col_name = col['name']
                col_type = col['type']
                not_null = 'NOT NULL' if col['notnull'] else ''
                default = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] else ''
                primary_key = 'PRIMARY KEY' if col['pk'] else ''

                col_def = f"{col_name} {col_type} {not_null} {default} {primary_key}".strip()
                columns_sql.append(col_def)

            columns_sql = ', '.join(columns_sql)
            create_query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_sql})"

            # 在备份数据库中创建表
            self.backup_db.execute(create_query)
            logger.info(f"表 {table} 结构创建成功")

        elif self.primary_db.db_type == 'mysql':
            # MySQL的表结构复制
            query = f"SHOW CREATE TABLE {table}"
            result = self.primary_db.fetch_one(query)
            if result:
                create_query = result['Create Table']
                # 移除AUTO_INCREMENT部分,让数据库自动处理
                import re
                create_query = re.sub(r' AUTO_INCREMENT=\d+', '', create_query)
                # 执行创建表语句
                self.backup_db.execute(create_query)
                logger.info(f"表 {table} 结构创建成功")

        elif self.primary_db.db_type == 'postgresql':
            # PostgreSQL的表结构复制
            query = f"SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='{table}'"
            columns = self.primary_db.fetch_all(query)

            if not columns:
                logger.warning(f"无法获取表 {table} 的结构")
                return

            # 构建创建表语句
            columns_sql = []
            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']
                not_null = 'NOT NULL' if col['is_nullable'] == 'NO' else ''
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ''

                col_def = f"{col_name} {col_type} {not_null} {default}".strip()
                columns_sql.append(col_def)

            columns_sql = ', '.join(columns_sql)
            create_query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_sql})"

            # 在备份数据库中创建表
            self.backup_db.execute(create_query)
            logger.info(f"表 {table} 结构创建成功")

    def _auto_sync(self):
        """自动同步主数据库到备份数据库"""
        while True:
            try:
                self.sync_from_primary()
                logger.info("自动同步完成")
            except Exception as e:
                logger.error(f"自动同步失败: {str(e)}")

            # 等待下一次同步
            time.sleep(self.sync_interval)

    def sync_from_primary(self):
        """从主数据库同步到备份数据库"""
        # 获取所有表名
        tables = self._get_all_tables()

        for table in tables:
            try:
                self._sync_table(table)
            except Exception as e:
                logger.error(f"同步表 {table} 失败: {str(e)}")

    def _get_all_tables(self):
        """获取所有表名"""
        if self.primary_db.db_type == 'sqlite':
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        elif self.primary_db.db_type == 'mysql':
            query = "SHOW TABLES"
        elif self.primary_db.db_type == 'postgresql':
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        else:
            return []

        result = self.primary_db.fetch_all(query)
        if result:
            return [list(row.values())[0] for row in result]
        return []

    def _get_table_columns(self, table):
        """获取表的列名"""
        if self.primary_db.db_type == 'sqlite':
            query = f"PRAGMA table_info({table})"
            columns = self.primary_db.fetch_all(query)
            return [col['name'] for col in columns]
        return []

    def _sync_table(self, table):
        """同步单个表"""
        columns = self._get_table_columns(table)
        if not columns:
            return

        # 清空备份数据库中的表
        self.backup_db.execute(f"DELETE FROM {table}")

        # 获取主数据库中的所有数据
        column_names = ', '.join(columns)
        select_query = f"SELECT {column_names} FROM {table}"
        data = self.primary_db.fetch_all(select_query)

        # 同步到备份数据库
        placeholders = ', '.join(['?'] * len(columns))
        insert_query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"

        for row in data:
            if isinstance(row, dict):
                values = tuple(row[col] for col in columns)
            else:
                values = row
            self.backup_db.execute(insert_query, values)

        logger.info(f"表 {table} 同步完成, 同步了 {len(data)} 条记录")

    def sync_to_primary(self):
        """从备份数据库同步到主数据库(用于恢复)"""
        tables = self._get_all_tables()

        for table in tables:
            try:
                self._sync_table_from_backup(table)
            except Exception as e:
                logger.error(f"从备份恢复表 {table} 失败: {str(e)}")

    def _sync_table_from_backup(self, table):
        """从备份恢复单个表"""
        columns = self._get_table_columns(table)
        if not columns:
            return

        # 构建插入语句
        column_names = ', '.join(columns)
        placeholders = ', '.join(['?'] * len(columns))
        insert_query = f"INSERT OR REPLACE INTO {table} ({column_names}) VALUES ({placeholders})"

        # 获取备份数据库中的所有数据
        select_query = f"SELECT {column_names} FROM {table}"
        data = self.backup_db.fetch_all(select_query)

        # 同步到主数据库
        for row in data:
            # 处理不同数据库的结果格式
            if isinstance(row, dict):
                values = tuple(row[col] for col in columns)
            else:
                values = row

            self.primary_db.execute(insert_query, values)

        logger.info(f"表 {table} 从备份恢复完成, 恢复了 {len(data)} 条记录")

    def backup_now(self):
        """立即执行备份"""
        logger.info("开始手动执行备份")
        self.sync_from_primary()
        logger.info("手动备份完成")

    def restore_from_backup(self):
        """从备份恢复数据"""
        logger.info("开始从备份恢复数据")
        self.sync_to_primary()
        logger.info("从备份恢复完成")

    def get_primary_db(self):
        """获取主数据库管理器"""
        return self.primary_db

    def get_backup_db(self):
        """获取备份数据库管理器"""
        return self.backup_db

    def get_sync_status(self):
        """获取同步状态"""
        return {
            "last_sync": datetime.now().isoformat(),
            "sync_interval": self.sync_interval,
            "primary_db_type": self.primary_db.db_type if hasattr(self.primary_db, 'db_type') else 'sqlite',
            "backup_db_type": self.backup_db.db_type
        }
