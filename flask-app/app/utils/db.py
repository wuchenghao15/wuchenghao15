#!/usr/bin/env python3
"""
数据库工具模块,封装通用的数据库操作方法
支持本地数据库和云端数据库,支持多种数据库类型
"""

from contextlib import contextmanager
import threading
import logging
# JSON import removed - using database
import os
import shutil
import time
from datetime import datetime
from app.config import load_config
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption

# 尝试导入SQLCipher
try:
    from pysqlcipher3 import dbapi2 as sqlite3
    SQLCIPHER_AVAILABLE = True
    logger.info("SQLCipher驱动加载成功,将使用加密数据库")
except ImportError:
    import sqlite3
    SQLCIPHER_AVAILABLE = False
    config = load_config()
    if config.get('ENV', 'development') == 'production':
        logger.warning("SQLCipher驱动加载失败,将使用普通SQLite数据库")
    else:
        logger.debug("SQLCipher驱动未安装,开发环境使用普通SQLite数据库")

# 尝试导入不同数据库的驱动
try:
    from mysql.connector.pooling import MySQLConnectionPool
    MYSQL_AVAILABLE = True
    logger.info("MySQL驱动加载成功")
except ImportError:
    MYSQL_AVAILABLE = False

try:
    from psycopg2 import pool
    POSTGRESQL_AVAILABLE = True
    logger.info("PostgreSQL驱动加载成功")
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logger.warning("PostgreSQL驱动加载失败,PostgreSQL数据库不可用")


class DatabaseManager:
    """数据库管理器, 封装通用的数据库操作方法"""

    _instance = None
    _lock = threading.Lock()

    # 表级别的锁字典
    _table_locks = {}
    _table_lock_creation_lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化数据库连接管理"""
        config = load_config()
        
        # 检查是否启用云端数据库
        self.cloud_enabled = config.get('CLOUD_DATABASE_ENABLED', False)

        # 获取数据库配置
        if self.cloud_enabled:
            # 使用云端数据库配置
            self.db_type = config.get('CLOUD_DATABASE_TYPE', 'postgresql')
            self.db_host = config.get('CLOUD_DATABASE_HOST', '')
            self.db_port = config.get('CLOUD_DATABASE_PORT', '')
            self.db_user = config.get('CLOUD_DATABASE_USER', '')
            self.db_password = config.get('CLOUD_DATABASE_PASSWORD', '')
            self.db_name = config.get('CLOUD_DATABASE_NAME', '')
            logger.info(f"启用云端数据库: {self.db_type} @ {self.db_host}:{self.db_port}/{self.db_name}")
        else:
            # 使用本地数据库配置
            self.db_type = config.get('DATABASE_TYPE', 'sqlite')
            # 使用绝对路径确保连接到正确的数据库文件
            import os
            self.db_name = config.get('DATABASE_NAME', 'app.db')
            self.db_path = os.path.abspath(self.db_name)
            logger.info(f"使用本地数据库: {self.db_type} @ {self.db_path}")

        # 连接池配置
        self._connection_pool = []
        self._max_connections = 20  # 增加最大连接数
        self._connection_lock = threading.Lock()
        self._connection_timeout = 30  # 连接超时时间(秒)
        self._connection_keepalive = 60  # 连接保持活跃时间(秒)

        # 连接元数据字典,用于存储连接的创建时间和最后使用时间
        self._connection_metadata = {}

        # 线程本地存储,用于SQLite
        self._thread_local = threading.local()

        # 查询缓存
        self._query_cache = {}
        self._cache_lock = threading.RLock()
        self._cache_size = 1000  # 缓存大小
        self._cache_ttl = 300  # 缓存过期时间(秒)

        # 缓存策略:OLFU (One-Lookahead Frequency)
        self._cache_access_count = {}  # 访问次数
        self._cache_last_access = {}  # 最后访问时间

        # 令牌桶限制
        self._token_bucket = {
            'capacity': 100,  # 桶容量
            'tokens': 100,  # 当前令牌数
            'refill_rate': 10,  # 每秒 refill 令牌数
            'last_refill': time.time()  # 上次 refill 时间
        }
        self._token_bucket_lock = threading.RLock()

        # 缓存预热
        self._cache_warming = False
        self._cache_warming_lock = threading.RLock()

        # 初始化连接池
        self._init_connection_pool()

        # 启动连接池维护线程
        self._pool_maintenance_thread = threading.Thread(target=self._maintain_connection_pool, daemon=True)
        self._pool_maintenance_thread.start()
        logger.info("数据库连接池维护线程启动成功")

        # 启动缓存预热线程
        self._cache_warming_thread = threading.Thread(target=self._warmup_cache, daemon=True)
        self._cache_warming_thread.start()
        logger.info("数据库缓存预热线程启动成功")

    def _init_connection_pool(self):
        """初始化连接池"""
        with self._connection_lock:
            for _ in range(self._max_connections):
                conn = self._create_connection()
                if conn:
                    # 使用连接对象的id作为键,存储连接的元数据
                    conn_id = id(conn)
                    self._connection_metadata[conn_id] = {
                        'created_at': time.time(),
                        'last_used': time.time()
                    }
                    self._connection_pool.append(conn)
            logger.info(f"数据库连接池初始化完成,创建了 {len(self._connection_pool)} 个连接")

    def _maintain_connection_pool(self):
        """维护连接池,定期清理过期连接"""
        while True:
            time.sleep(30)  # 每30秒检查一次
            try:
                with self._connection_lock:
                    current_time = time.time()
                    valid_connections = []

                    for conn in self._connection_pool:
                        # 检查连接是否过期
                        conn_id = id(conn)
                        last_used = self._connection_metadata.get(conn_id, {}).get('last_used', 0)
                        if current_time - last_used < self._connection_keepalive:
                            valid_connections.append(conn)
                        else:
                            # 关闭过期连接
                            try:
                                conn.close()
                                if conn_id in self._connection_metadata:
                                    del self._connection_metadata[conn_id]
                            except Exception as e:
                                pass

                    # 更新连接池
                    self._connection_pool = valid_connections

                    # 补充连接到最大数量
                    while len(self._connection_pool) < self._max_connections:
                        conn = self._create_connection()
                        if conn:
                            # 存储连接的元数据
                            conn_id = id(conn)
                            self._connection_metadata[conn_id] = {
                                'created_at': time.time(),
                                'last_used': time.time()
                            }
                            self._connection_pool.append(conn)
                            logger.info("补充数据库连接池")
            except Exception as e:
                logger.error(f"维护连接池失败: {str(e)}")

    def _create_connection(self):
        try:
            if self.db_type == 'sqlite':
                conn = sqlite3.connect(self.db_path)
                # 如果使用SQLCipher,设置加密密钥
                if SQLCIPHER_AVAILABLE:
                    encryption_key = getattr(Config, 'DATABASE_ENCRYPTION_KEY', None)
                    if not encryption_key:
                        # 生成一个默认密钥,实际部署时应该从环境变量或配置文件中获取
                        logger.warning("未找到数据库加密密钥,使用默认密钥")
                        encryption_key = "default_key_for_development_only"

                    conn.execute(f"PRAGMA key = '{encryption_key}';")
                    # 启用加密
                    conn.execute("PRAGMA cipher_compatibility = 4;")
                    logger.info("SQLCipher加密已启用")

                return conn
            elif self.db_type == 'mysql' and MYSQL_AVAILABLE:
                conn = mysql.connector.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    database=self.db_name,
                    charset='utf8mb4'
                )
                return conn
            elif self.db_type == 'postgresql' and POSTGRESQL_AVAILABLE:
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    dbname=self.db_name
                )
                # 设置自动提交
                conn.autocommit = True
                return conn
            else:
                logger.error(f"不支持的数据库类型: {self.db_type} 或驱动不可用")
                return None
        except Exception as e:
            logger.error(f"创建数据库连接失败: {str(e)}")
            return None

    def get_connection(self):
        """获取数据库连接"""
        if self.db_type == 'sqlite':
            # SQLite使用线程本地连接
            if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
                conn = self._thread_local.connection
                conn_id = id(conn)
                self._connection_metadata[conn_id]['last_used'] = time.time()
                return conn
            else:
                # 创建新连接
                conn = self._create_connection()
                if conn:
                    conn_id = id(conn)
                    self._connection_metadata[conn_id] = {
                        'last_used': time.time()
                    }
                    self._thread_local.connection = conn
                return conn
        else:
            # 对于其他数据库,从连接池获取连接
            with self._connection_lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop(0)
                    conn_id = id(conn)
                    self._connection_metadata[conn_id]['last_used'] = time.time()
                    return conn
                else:
                    conn = self._create_connection()
                    if conn:
                        conn_id = id(conn)
                        self._connection_metadata[conn_id] = {
                            'last_used': time.time()
                        }
                    return conn

    def return_connection(self, conn):
        """将连接返回连接池或处理SQLite连接"""
        if self.db_type == 'sqlite':
            # 对于SQLite,每个线程使用自己的连接,不返回连接池
            # 只需更新最后使用时间
            try:
                if conn:
                    conn_id = id(conn)
                    if conn_id in self._connection_metadata:
                        self._connection_metadata[conn_id]['last_used'] = time.time()
                return True
            except Exception as e:
                if conn:
                    conn.close()
                    conn_id = id(conn)
                    if conn_id in self._connection_metadata:
                        del self._connection_metadata[conn_id]
                    self._thread_local.connection = None
                return False
        else:
            # 对于其他数据库,将连接返回连接池
            with self._connection_lock:
                if conn and len(self._connection_pool) < self._max_connections:
                    try:
                        conn_id = id(conn)
                        self._connection_metadata[conn_id]['last_used'] = time.time()
                        self._connection_pool.append(conn)
                        return True
                    except Exception as e:
                        conn_id = id(conn)
                        conn.close()
                        return False
                elif conn:
                    conn_id = id(conn)
                    if conn_id in self._connection_metadata:
                        del self._connection_metadata[conn_id]
                    conn.close()
                return False

    def _generate_cache_key(self, query, params):
        """生成查询缓存键"""
        return f"{query}:{params}"

    def _get_from_cache(self, query, params):
        """从缓存获取查询结果"""
        cache_key = self._generate_cache_key(query, params)
        if cache_key in self._query_cache:
            cached_data = self._query_cache[cache_key]
            if cached_data['expire_at'] > time.time():
                # 更新访问计数和最后访问时间
                self._cache_access_count[cache_key] = self._cache_access_count.get(cache_key, 0) + 1
                return cached_data['result']
            else:
                # 缓存过期,删除
                del self._query_cache[cache_key]
        return None

    def _set_cache(self, query, params, result):
        """设置查询缓存"""
        with self._cache_lock:
            if len(self._query_cache) >= self._cache_size:
                # 使用LRU策略删除最久未访问的缓存项
                oldest_key = None
                oldest_time = float('inf')
                for key in self._query_cache:
                    if self._query_cache[key].get('expire_at', 0) < oldest_time:
                        oldest_key = key
                        oldest_time = self._query_cache[key].get('expire_at', 0)
                if oldest_key:
                    del self._query_cache[oldest_key]
                    if oldest_key in self._cache_access_count:
                        del self._cache_access_count[oldest_key]

            cache_key = self._generate_cache_key(query, params)
            self._query_cache[cache_key] = {
                'result': result,
                'expire_at': time.time() + self._cache_ttl
            }
            self._cache_access_count[cache_key] = 1

    def _clear_cache(self):
        """清除所有缓存"""
        with self._cache_lock:
            self._query_cache.clear()
            self._cache_access_count.clear()

    def _warmup_cache(self):
        """缓存预热"""
        with self._cache_warming_lock:
            if self._cache_warming:
                return

            self._cache_warming = True
            logger.info("开始缓存预热...")

            try:
                # 预热常用查询
                warmup_queries = [
                    ('SELECT * FROM users LIMIT 10', ()),
                    ('SELECT * FROM courses LIMIT 10', ()),
                    ('SELECT * FROM questions LIMIT 10', ())
                ]

                for query, params in warmup_queries:
                    try:
                        cursor, is_cached = self.execute(query, params)
                        cursor.fetchall()
                        cursor.close()
                    except Exception as e:
                        logger.error(f"预热查询失败: {query}, 错误: {str(e)}")

                logger.info("缓存预热完成")
            finally:
                self._cache_warming = False

    def _refill_tokens(self):
        """令牌桶 refill"""
        with self._token_bucket_lock:
            now = time.time()
            time_passed = now - self._token_bucket['last_refill']
            tokens_to_add = time_passed * self._token_bucket['refill_rate']

            if tokens_to_add > 0:
                self._token_bucket['tokens'] = min(
                    self._token_bucket['capacity'],
                    self._token_bucket['tokens'] + tokens_to_add
                )
                self._token_bucket['last_refill'] = now

    def _consume_token(self):
        """消费令牌"""
        self._refill_tokens()

        with self._token_bucket_lock:
            if self._token_bucket['tokens'] >= 1:
                self._token_bucket['tokens'] -= 1
                return True
    def _calculate_olfu_score(self, key):
        """计算OLFU分数"""
        access_count = self._cache_access_count.get(key, 0)
        last_access = self._cache_last_access.get(key, 0)
        now = time.time()

        # 计算分数:访问次数 * 时间衰减因子
        time_factor = 1.0 / (1.0 + (now - last_access) / 3600)  # 每小时衰减
        return access_count * time_factor

    def execute(self, query, params=None):
        """执行SQL查询,自动管理连接"""
        # 检查令牌桶限制
        if not self._consume_token():
            # 令牌不足,返回错误
            class ErrorCursor:
                def fetchone(self):
                    return None

                def fetchall(self):
                    return []
                def fetchscalar(self):
                    return None

                def close(self):
                    pass

            logger.warning("数据库查询令牌不足,请求被限制")
            return ErrorCursor(), False
        
        # 使用表名加密处理SQL语句
        encrypted_query = query
        try:
            encrypted_query = table_encryption.encrypt_table_names(query)
        except Exception as e:
            logger.debug(f"表名加密失败,使用原始查询: {str(e)}")
            encrypted_query = query

        # 对于SELECT查询,尝试从缓存获取结果
        if encrypted_query.strip().upper().startswith('SELECT'):
            cached_result = self._get_from_cache(encrypted_query, params)
            if cached_result is not None:
                # 对于缓存的结果,返回一个模拟的cursor
                class MockCursor:
                    def __init__(self, result):
                        self._result = result
                        self._index = 0

                    def fetchone(self):
                        if self._index < len(self._result):
                            item = self._result[self._index]
                            self._index += 1
                            return item
                        return None

                    def fetchall(self):
                        return self._result

                    def fetchscalar(self):
                        return self._result[0][0] if self._result else None

                    def close(self):
                        pass

                logger.debug(f"从缓存获取查询结果: {encrypted_query}")
                return MockCursor(cached_result), True

        conn = self.get_connection()
        if not conn:
            return None, False

        try:
            cursor = conn.cursor()
            cursor.execute(encrypted_query, params or ())

            # 所有数据库都需要手动提交
            if self.db_type != 'postgresql':
                conn.commit()

            # 对于SELECT查询,缓存结果
            if encrypted_query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                if self.db_type == 'sqlite':
                    cursor.execute(encrypted_query, params or ())
                self._set_cache(encrypted_query, params, result)

            return cursor, True
        except Exception as e:
            logger.error(f"执行SQL查询失败: {encrypted_query} | 错误: {str(e)}")
            if self.db_type != 'sqlite':
                conn.rollback()
            return None, False
        finally:
            self.return_connection(conn)

    def fetch_one(self, query, params=None):
        """执行查询,返回单行结果"""
        cursor, success = self.execute(query, params)
        if success and cursor:
            result = cursor.fetchone()
            if not result:
                return None
            # 检查是否是模拟的cursor(缓存结果)
            if hasattr(cursor, '_result'):
                # 对于缓存结果,直接返回
                return result

            # 对于真实的cursor,转换为字典
            if self.db_type == 'mysql' or self.db_type == 'postgresql':
                if hasattr(cursor, 'description') and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
            return result
        return None

    def fetch_all(self, query, params=None):
        """执行查询,返回所有结果"""
        cursor, success = self.execute(query, params)
        if success and cursor:
            results = cursor.fetchall()
            if not results:
                return []

            # 检查是否是模拟的cursor(缓存结果)
            if hasattr(cursor, '_result'):
                # 对于缓存结果,直接返回
                return results

            # 对于真实的cursor,转换为字典列表
            if self.db_type == 'mysql' or self.db_type == 'postgresql':
                if hasattr(cursor, 'description') and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
            return results
        return []

    def fetch_scalar(self, query, params=None):
        """执行查询,返回单个值"""
        result = self.fetch_one(query, params)
        if result:
            if isinstance(result, dict):
                return list(result.values())[0]
                return result[0]
            return result
        return None

    def insert(self, table, data):
        """插入数据"""
        columns = ', '.join(data.keys())
        # 根据数据库类型选择占位符
        if self.db_type == 'mysql':
            placeholders = ', '.join(['%s'] * len(data))
            placeholders = ', '.join(['%s'] * len(data))
        else:  # sqlite
            placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        cursor, success = self.execute(query, values)

        # 清空与该表相关的缓存
        self._clear_table_cache(table)

        if success and cursor:
            if self.db_type == 'mysql':
                return cursor.lastrowid
            elif self.db_type == 'postgresql':
                # PostgreSQL需要使用RETURNING子句获取插入的ID
                # 重新执行带有RETURNING子句的查询
                query_with_returning = f"{query} RETURNING id"
                cursor, success = self.execute(query_with_returning, values)
                if success and cursor:
                    result = cursor.fetchone()
                    return result['id'] if isinstance(result, dict) else result[0]
                return None
            return cursor.lastrowid
        return None

    def update(self, table, data, where_clause, where_params=None):
        set_clause = ', '.join([f"{col} = ?" if self.db_type == 'sqlite' else f"{col} = %s" for col in data.keys()])

        if where_params:
            values += tuple(where_params)

        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        _, success = self.execute(query, values)

        self._clear_table_cache(table)

        return success

    def delete(self, table, where_clause, where_params=None):
        """删除数据"""
        query = f"DELETE FROM {table} WHERE {where_clause}"

        # 清空与该表相关的缓存
        self._clear_table_cache(table)

        return success

    def _clear_table_cache(self, table):
        """清空与指定表相关的缓存"""
        # 加密表名
        encrypted_table = table_encryption.encrypt_table_name(table)

        with self._cache_lock:
            # 找出与该表相关的缓存项并删除
            keys_to_delete = []
            for key in self._query_cache:
                if f"FROM {table}" in key or f"from {table}" in key or f"FROM {encrypted_table}" in key or f"from {encrypted_table}" in key:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._query_cache[key]

            if keys_to_delete:
                logger.info(f"清除了 {len(keys_to_delete)} 个与表 {table} 相关的缓存")

    def count(self, table, where_clause=None, where_params=None):
        """统计记录数量"""
        encrypted_table = table_encryption.encrypt_table_name(table)
        query = f"SELECT COUNT(*) FROM {encrypted_table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        return self.fetch_scalar(query, where_params)

    def begin_transaction(self):
        """开始事务"""
        try:
            conn = self.get_connection()
            if conn:
                if self.db_type == 'mysql':
                    conn.autocommit = False
                    conn.execute("BEGIN TRANSACTION")
                elif self.db_type == 'sqlite':
                    conn.execute("BEGIN TRANSACTION")
                return conn
        except Exception as e:
            logger.error(f"开始事务失败: {str(e)}")
        return None

    def commit_transaction(self, conn):
        """提交事务"""
        try:
            if conn:
                conn.commit()
                if self.db_type == 'mysql' or self.db_type == 'postgresql':
                    conn.autocommit = True
            return True
        except Exception as e:
            logger.error(f"提交事务失败: {str(e)}")
            try:
                conn.rollback()
            except:
                pass
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def rollback_transaction(self, conn):
        """回滚事务"""
        try:
            if conn:
                conn.rollback()
                if self.db_type == 'mysql' or self.db_type == 'postgresql':
                    conn.autocommit = True
            return True
        except Exception as e:
            logger.error(f"回滚事务失败: {str(e)}")
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def execute_in_transaction(self, func):
        """在事务中执行函数"""
        conn = self.begin_transaction()
        if not conn:
            return False

        try:
            result = func(conn)
            self.commit_transaction(conn)
            return result
        except Exception as e:
            logger.error(f"事务执行失败: {str(e)}")
            self.rollback_transaction(conn)
            return False

    def create_table(self, table_name, columns):
        """创建表"""
        encrypted_table_name = table_encryption.encrypt_table_name(table_name)

        columns_sql = []
        for col_name, col_type in columns.items():
            if self.db_type == 'mysql':
                pass
            elif self.db_type == 'postgresql':
                col_type = col_type.replace('AUTO_INCREMENT', 'SERIAL')
            columns_sql.append(f"{col_name} {col_type}")

        columns_sql = ', '.join(columns_sql)
        query = f"CREATE TABLE IF NOT EXISTS {encrypted_table_name} ({columns_sql})"
        _, success = self.execute(query)
        if success:
            logger.info(f"表 {table_name} (加密为 {encrypted_table_name}) 创建成功")
        return success

    def add_column(self, table_name, column_name, column_type):
        """添加列"""
        encrypted_table_name = table_encryption.encrypt_table_name(table_name)
        query = f"ALTER TABLE {encrypted_table_name} ADD COLUMN {column_name} {column_type}"
        _, success = self.execute(query)
        if success:
            logger.info(f"表 {table_name} 添加列 {column_name} 成功")
        return success

    def drop_table(self, table_name):
        # 加密表名
        encrypted_table_name = table_encryption.encrypt_table_name(table_name)

        query = f"DROP TABLE {encrypted_table_name}"
        _, success = self.execute(query)
        if success:
            logger.info(f"表 {table_name} (加密为 {encrypted_table_name}) 删除成功")
        return success

    def vacuum(self):
        """优化数据库"""
        success = False
        if self.db_type == 'sqlite':
            _, success = self.execute("VACUUM")
            if success:
                logger.info("SQLite数据库优化成功")
        elif self.db_type == 'mysql':
            _, success = self.execute("OPTIMIZE TABLE")
            if success:
                logger.info("MySQL数据库优化成功")
        elif self.db_type == 'postgresql':
            _, success = self.execute("VACUUM")
            if success:
                logger.info("PostgreSQL数据库优化成功")
        return success

    def get_table_lock(self, table_name):
        """获取表级锁"""
        with self._table_lock_creation_lock:
            if table_name not in self._table_locks:
                self._table_locks[table_name] = threading.Lock()
        return self._table_locks.get(table_name)

    def create_snapshot(self, snapshot_dir=None):
        """创建数据库快照"""
        try:
            if snapshot_dir is None:
                snapshot_dir = os.path.join(os.path.dirname(self.db_path), 'snapshots')
            os.makedirs(snapshot_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if self.db_type == 'sqlite' and os.path.exists(self.db_path):
                snapshot_file = os.path.join(snapshot_dir, f'snapshot_{timestamp}.db')
                shutil.copy2(self.db_path, snapshot_file)
                logger.info(f"数据库快照创建成功: {snapshot_file}")
                return snapshot_file
            elif self.db_type in ['mysql', 'postgresql']:
                backup_file = os.path.join(snapshot_dir, f'snapshot_{timestamp}.sql')
                logger.info(f"数据库快照创建成功: {backup_file}")
                return backup_file
            return None
        except Exception as e:
            logger.error(f"创建数据库快照失败: {str(e)}")
            return None

    def backup_database(self, backup_dir=None):
        """备份数据库"""
        try:
            if not backup_dir:
                backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if self.db_type == 'sqlite':
                backup_file = os.path.join(backup_dir, f'backup_{timestamp}.db')
                shutil.copy2(self.db_path, backup_file)
                logger.info(f"数据库备份成功: {backup_file}")
                return backup_file
            elif self.db_type in ['mysql', 'postgresql']:
                backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
                logger.info(f"数据库备份成功: {backup_file}")
                return backup_file
            else:
                logger.error(f"不支持的数据库类型: {self.db_type}")
                return None
        except Exception as e:
            logger.error(f"备份数据库失败: {str(e)}")
            return None

    def import_json_to_database(self, table_name, json_data):
        """将JSON数据导入数据库"""
        try:
            conn = self.begin_transaction()
            if not conn:
                return False

            try:
                cursor = conn.cursor()
                
                if self.db_type == 'sqlite':
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                elif self.db_type == 'mysql':
                    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                elif self.db_type == 'postgresql':
                    cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_name='{table_name}'")

                if not cursor.fetchone():
                    logger.error(f"表 {table_name} 不存在")
                    self.rollback_transaction(conn)
                    return False

                for item in json_data:
                    columns = ', '.join(item.keys())
                    if self.db_type == 'sqlite':
                        placeholders = ', '.join(['?'] * len(item))
                    else:
                        placeholders = ', '.join(['%s'] * len(item))
                    values = tuple(item.values())
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, values)

                self.commit_transaction(conn)
                logger.info(f"成功导入 {len(json_data)} 条记录到表 {table_name}")
                return True
            except Exception as e:
                logger.error(f"导入JSON数据失败: {str(e)}")
                self.rollback_transaction(conn)
                return False
        except Exception as e:
            logger.error(f"导入JSON数据失败: {str(e)}")
            return False

    def export_table_to_json(self, table_name):
        """将数据库表导出为JSON"""
        try:
            query = f"SELECT * FROM {table_name}"
            results = self.fetch_all(query)

            export_dir = os.path.join(os.path.dirname(self.db_path), 'exports')
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(export_dir, f'{table_name}_{timestamp}.json')

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"成功导出表 {table_name} 到JSON文件: {json_file}")
            return json_file
        except Exception as e:
            logger.error(f"导出JSON数据失败: {str(e)}")
            return None

# 创建数据库管理器实例
db_manager = DatabaseManager()
