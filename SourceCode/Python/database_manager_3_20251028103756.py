# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:29
#!/usr/bin/env python3

"""
数据库管理器模块
提供带异步锁的数据库连接和操作功能，支持并发访问控制
"""
import os
import sys
import logging
import threading
import time
# JSON import removed - using database
from contextlib import contextmanager

# pyodbc将在需要时动态导入

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_manager')


class DatabaseManager:
    """数据库管理器，提供带异步锁的数据库操作"""

    # 单例模式实例
    _instance = None
    _lock = threading.Lock()

    # 表级别的锁字典
    _table_locks = {}
    _table_lock_creation_lock = threading.Lock()

    # 连接池相关配置
    _max_connections = 10
    _connection_pool = []
    _pool_lock = threading.Lock()

    def __new__(cls):
        """确保单例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化数据库管理器"""
        with self._lock:
            if not self._initialized:
                self._conn_str = ""
                self._connection_timeout = 30
                self._retry_attempts = 3
                self._retry_delay = 2
                self._initialized = True
                self.load_connection_string()

    def load_connection_string(self):
        """从配置文件加载数据库连接字符串"""
        try:
            # 尝试从多个可能的位置加载连接字符串
            possible_paths = [
                os.path.join('MyData', 'db_connection_string.txt'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'MyData', 'db_connection_string.txt'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'MyData', 'db_connection_string.txt')
            ]

            for config_file in possible_paths:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines:
                            line = line.strip()
                            if not line.startswith('#') and line:
                                # 寻找包含服务器信息的连接字符串
                                if 'Driver=' in line.lower() or 'Server=' in line or 'SERVER=' in line:
                                    self._conn_str = line
                                    logger.info(f'成功从配置文件读取数据库连接信息: {config_file}')
                                    return

            # 如果没有找到配置文件，使用默认连接字符串
            self._conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=wuchenghao15.xicp.net,33693;DATABASE=MyData;UID=sa;PWD=LoginMe15;"
            logger.info('使用默认数据库连接信息')
        except Exception as e:
            logger.error(f'加载数据库连接字符串失败: {str(e)}')
            # 使用默认连接字符串作为后备
            self._conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=wuchenghao15.xicp.net,33693;DATABASE=MyData;UID=sa;PWD=LoginMe15;"

        """手动设置连接字符串"""
        self._conn_str = conn_str
        logger.info('数据库连接字符串已手动更新')

    def _get_table_lock(self, table_name):
        """获取指定表的锁，如果不存在则创建"""
        with self._table_lock_creation_lock:
            if table_name not in self._table_locks:
                self._table_locks[table_name] = threading.RLock()
        return self._table_locks[table_name]

    def _get_connection(self):
        """从连接池获取连接，如果没有可用连接则创建新连接"""
        try:
            # 尝试从连接池获取连接
            with self._pool_lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop()
                    # 检查连接是否仍然有效
                    try:
                        import pyodbc
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.close()
                        logger.debug('从连接池获取到有效连接')
                        return conn
                    except:
                        # 连接无效，关闭并创建新连接
                        conn.close()
                        logger.debug('连接池中的连接已失效，将创建新连接')

            # 导入pyodbc模块
            import pyodbc

            # 创建新连接
            logger.info('创建新的数据库连接')
            return conn
        except Exception as e:
            logger.error(f'获取数据库连接失败: {str(e)}')
            raise
    def _return_connection(self, conn):
        """将连接返回到连接池"""
        try:
            with self._pool_lock:
                # 检查连接池大小，避免连接泄漏
                if len(self._connection_pool) < self._max_connections:
                    logger.debug('连接已返回连接池')
                else:
                    conn.close()
                    logger.debug('连接池已满，关闭多余连接')
        except Exception as e:
            logger.error(f'返回连接到连接池失败: {str(e)}')
            try:
                conn.close()
            except:
                pass

    @contextmanager
    def get_connection(self, table_name=None, timeout=60):
        """
        Args:
            table_name: 要操作的表名，如果提供则获取表级锁
            timeout: 锁获取超时时间（秒）

        Yields:
            数据库连接对象
        """
        lock = None
        acquired = False

        try:
            # 如果指定了表名，尝试获取表级锁
            if table_name:
                lock = self._get_table_lock(table_name)
                logger.debug(f'尝试获取表 {table_name} 的锁')
                acquired = lock.acquire(timeout=timeout)

                if not acquired:
                    raise TimeoutError(f'获取表 {table_name} 的锁超时')
                logger.debug(f'成功获取表 {table_name} 的锁')

            # 获取数据库连接
            conn = self._get_connection()

            # 提供连接给调用者
            yield conn

            # 如果一切正常，提交事务
            if conn:
                conn.commit()
                logger.debug('数据库事务已提交')

        except Exception as e:
            # 发生错误时回滚事务
            if conn:
                try:
                    conn.rollback()
                    logger.debug('数据库事务已回滚')
                except:
                    pass
            raise
        finally:
            # 归还连接到连接池
                self._return_connection(conn)

                if lock and acquired:
                lock.release()
                logger.debug(f'已释放表 {table_name} 的锁')
    def execute_query(self, query, params=None, table_name=None, timeout=60):
        """

            query: SQL查询语句
            params: 查询参数（可选）
            table_name: 操作的表名（可选，用于获取表级锁）
            timeout: 锁超时时间

        Returns:
            查询结果列表
        """

        with self.get_connection(table_name=table_name, timeout=timeout) as conn:
            try:
                logger.debug(f'执行查询: {query}')

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # 获取列名

                # 将结果转换为字典列表
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                cursor.close()
                logger.debug(f'查询完成，返回 {len(results)} 条记录')
                return results

            except Exception as e:
                logger.error(f'执行查询失败: {query}, 错误: {str(e)}')
                raise

    def execute_non_query(self, query, params=None, table_name=None, timeout=60):
        """
        Args:
            query: SQL语句
            params: 查询参数（可选）
            table_name: 操作的表名（可选，用于获取表级锁）
            timeout: 锁超时时间

        Returns:
            受影响的行数
        """
        with self.get_connection(table_name=table_name, timeout=timeout) as conn:
            try:
                cursor = conn.cursor()
                logger.debug(f'执行非查询: {query}')

                if params:
                    cursor.execute(query, params)
                    cursor.execute(query)

                affected_rows = cursor.rowcount
                cursor.close()
                logger.debug(f'非查询完成，影响 {affected_rows} 行')
            except Exception as e:
                raise
    def execute_scalar(self, query, params=None, table_name=None, timeout=60):
        """

        Args:
            query: SQL查询语句
            table_name: 操作的表名（可选，用于获取表级锁）
            timeout: 锁超时时间
        Returns:
            查询结果的第一行第一列的值
        """
            try:
                cursor = conn.cursor()

                else:
                    cursor.execute(query)
                result = cursor.fetchone()
                cursor.close()

                value = result[0] if result else None

            except Exception as e:
                logger.error(f'执行标量查询失败: {query}, 错误: {str(e)}')
                raise

        """
        Args:
            operations: 操作列表，每个操作是(查询语句, 参数)的元组

        Returns:
        """

        with self.get_connection(table_name=table_name, timeout=timeout) as conn:
            try:
                cursor = conn.cursor()
                logger.debug(f'开始执行事务，包含 {len(operations)} 个操作')
                for i, (query, params) in enumerate(operations):
                    logger.debug(f'执行事务操作 {i+1}/{len(operations)}: {query}')

                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    # 如果是SELECT语句，保存结果
                    if query.strip().upper().startswith('SELECT'):
                        results = []
                            results.append(dict(zip(columns, row)))
                    else:
                        last_result = cursor.rowcount

                cursor.close()
                logger.debug('事务执行完成')
                return last_result

            except Exception as e:
                logger.error(f'执行事务失败: {str(e)}')

    def test_connection(self):
        """
        Returns:
            bool: 连接是否成功
        """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                result = cursor.fetchone()
                cursor.close()
                return True
            logger.error(f'数据库连接测试失败: {str(e)}')
            return False

    def close_all_connections(self):
        """关闭所有连接池中的连接"""
        with self._pool_lock:
            for conn in self._connection_pool:
                try:
                    conn.close()
                except:


# 全局数据库管理器实例
if __name__ == "__main__":
    print("测试数据库管理器...")

    # 测试连接
        print("数据库连接成功!")

        # 测试简单查询
        try:
            result = db_manager.execute_scalar("SELECT 1 + 1")
            print(f"简单查询结果: {result}")
            print(f"查询测试失败: {str(e)}")
    else:

    db_manager.close_all_connections()
