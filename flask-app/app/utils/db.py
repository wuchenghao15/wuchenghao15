#!/usr/bin/env python3
"""
数据库工具模块,封装通用的数据库操作方法
支持本地数据库和云端数据库,支持多种数据库类型
优化连接池管理,防止池干涸
"""

from contextlib import contextmanager
import threading
import logging
import os
import shutil
import time
import queue
from datetime import datetime
from app.config import load_config
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption

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

    _table_locks = {}
    _table_lock_creation_lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化数据库连接管理"""
        config = load_config()
        
        self.cloud_enabled = config.get('CLOUD_DATABASE_ENABLED', False)

        if self.cloud_enabled:
            self.db_type = config.get('CLOUD_DATABASE_TYPE', 'postgresql')
            self.db_host = config.get('CLOUD_DATABASE_HOST', '')
            self.db_port = config.get('CLOUD_DATABASE_PORT', '')
            self.db_user = config.get('CLOUD_DATABASE_USER', '')
            self.db_password = config.get('CLOUD_DATABASE_PASSWORD', '')
            self.db_name = config.get('CLOUD_DATABASE_NAME', '')
            logger.info(f"启用云端数据库: {self.db_type} @ {self.db_host}:{self.db_port}/{self.db_name}")
        else:
            self.db_type = config.get('DATABASE_TYPE', 'sqlite')
            import os
            self.db_name = config.get('DATABASE_NAME', 'app.db')
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', self.db_name)
            self.db_path = os.path.abspath(self.db_path)
            logger.info(f"使用本地数据库: {self.db_type} @ {self.db_path}")

        # 连接池配置 - 优化版本
        self._connection_pool = []
        self._min_connections = config.get('DB_MIN_CONNECTIONS', 5)
        self._max_connections = config.get('DB_MAX_CONNECTIONS', 50)
        self._initial_connections = config.get('DB_INITIAL_CONNECTIONS', 10)
        self._connection_lock = threading.Lock()
        self._connection_timeout = config.get('DB_CONNECTION_TIMEOUT', 30)
        self._connection_keepalive = config.get('DB_CONNECTION_KEEPALIVE', 300)
        
        # 动态扩容配置
        self._pool_expansion_factor = config.get('DB_POOL_EXPANSION_FACTOR', 0.5)
        self._pool_shrink_threshold = config.get('DB_POOL_SHRINK_THRESHOLD', 0.2)
        self._pool_maintenance_interval = config.get('DB_POOL_MAINTENANCE_INTERVAL', 30)
        
        # 连接等待队列
        self._wait_queue = queue.Queue(maxsize=100)
        self._wait_timeout = config.get('DB_WAIT_TIMEOUT', 10)
        
        # 连接元数据字典
        self._connection_metadata = {}
        
        # 连接池统计
        self._stats = {
            'total_connections': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'pool_dry_events': 0,
            'wait_queue_length': 0,
            'expansions': 0,
            'shrinks': 0
        }
        self._stats_lock = threading.Lock()

        self._thread_local = threading.local()

        self._query_cache = {}
        self._cache_lock = threading.RLock()
        self._cache_size = 1000
        self._cache_ttl = 300

        self._cache_access_count = {}
        self._cache_last_access = {}

        self._token_bucket = {
            'capacity': 1000,
            'tokens': 1000,
            'refill_rate': 100,
            'last_refill': time.time()
        }
        self._token_bucket_lock = threading.RLock()

        self._cache_warming = False
        self._cache_warming_lock = threading.RLock()

        # 初始化连接池到初始大小
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
        """初始化连接池到初始大小"""
        target_size = min(self._initial_connections, self._max_connections)
        created = 0
        
        with self._connection_lock:
            for _ in range(target_size):
                conn = self._create_connection()
                if conn:
                    conn_id = id(conn)
                    self._connection_metadata[conn_id] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'uses': 0
                    }
                    self._connection_pool.append(conn)
                    created += 1
        
        with self._stats_lock:
            self._stats['total_connections'] = created
        
        logger.info(f"数据库连接池初始化完成,创建了 {created} 个连接 (最小:{self._min_connections}, 最大:{self._max_connections})")

    def _expand_pool(self):
        """动态扩容连接池"""
        with self._connection_lock:
            current_size = len(self._connection_pool)
            if current_size >= self._max_connections:
                return 0
            
            new_size = int(current_size * (1 + self._pool_expansion_factor))
            new_size = min(new_size, self._max_connections)
            to_add = new_size - current_size
            
            added = 0
            for _ in range(to_add):
                conn = self._create_connection()
                if conn:
                    conn_id = id(conn)
                    self._connection_metadata[conn_id] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'uses': 0
                    }
                    self._connection_pool.append(conn)
                    added += 1
            
            if added > 0:
                with self._stats_lock:
                    self._stats['expansions'] += 1
                    self._stats['total_connections'] += added
                logger.info(f"连接池扩容: {current_size} -> {current_size + added}")
            
            return added

    def _shrink_pool(self):
        """动态收缩连接池"""
        with self._connection_lock:
            current_size = len(self._connection_pool)
            if current_size <= self._min_connections:
                return 0
            
            target_size = max(self._min_connections, int(current_size * (1 - self._pool_shrink_threshold)))
            to_remove = current_size - target_size
            
            removed = 0
            # 移除最久未使用的连接
            sorted_conns = sorted(
                self._connection_pool,
                key=lambda c: self._connection_metadata.get(id(c), {}).get('last_used', 0)
            )
            
            for conn in sorted_conns[:to_remove]:
                try:
                    conn.close()
                    conn_id = id(conn)
                    if conn_id in self._connection_metadata:
                        del self._connection_metadata[conn_id]
                    removed += 1
                except Exception:
                    pass
            
            self._connection_pool = sorted_conns[to_remove:]
            
            if removed > 0:
                with self._stats_lock:
                    self._stats['shrinks'] += 1
                    self._stats['total_connections'] -= removed
                logger.info(f"连接池收缩: {current_size} -> {current_size - removed}")
            
            return removed

    def _maintain_connection_pool(self):
        """维护连接池,定期清理过期连接并智能调整大小"""
        while True:
            time.sleep(self._pool_maintenance_interval)
            try:
                with self._connection_lock:
                    current_time = time.time()
                    valid_connections = []
                    
                    for conn in self._connection_pool:
                        conn_id = id(conn)
                        last_used = self._connection_metadata.get(conn_id, {}).get('last_used', 0)
                        
                        # 检查连接是否过期
                        if current_time - last_used < self._connection_keepalive:
                            # 检查连接是否仍然有效
                            if self._is_connection_valid(conn):
                                valid_connections.append(conn)
                            else:
                                try:
                                    conn.close()
                                    if conn_id in self._connection_metadata:
                                        del self._connection_metadata[conn_id]
                                except Exception:
                                    pass
                        else:
                            try:
                                conn.close()
                                if conn_id in self._connection_metadata:
                                    del self._connection_metadata[conn_id]
                            except Exception:
                                pass
                    
                    self._connection_pool = valid_connections

                    # 补充连接到最小数量
                    while len(self._connection_pool) < self._min_connections:
                        conn = self._create_connection()
                        if conn:
                            conn_id = id(conn)
                            self._connection_metadata[conn_id] = {
                                'created_at': time.time(),
                                'last_used': time.time(),
                                'uses': 0
                            }
                            self._connection_pool.append(conn)
                            logger.info("补充数据库连接池(低于最小连接数)")
                
                # 智能调整连接池大小
                self._smart_resize_pool()
                
            except Exception as e:
                logger.error(f"维护连接池失败: {str(e)}")

    def _is_connection_valid(self, conn):
        """检查连接是否有效"""
        try:
            if self.db_type == 'mysql':
                conn.ping(reconnect=False)
            elif self.db_type == 'postgresql':
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            elif self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            return True
        except Exception:
            return False

    def _smart_resize_pool(self):
        """根据池使用率智能调整连接池大小"""
        with self._connection_lock:
            current_size = len(self._connection_pool)
        
        with self._stats_lock:
            wait_queue_len = self._stats.get('wait_queue_length', 0)
            pool_hits = self._stats.get('pool_hits', 0)
            pool_misses = self._stats.get('pool_misses', 0)
        
        total_requests = pool_hits + pool_misses
        if total_requests == 0:
            return
        
        hit_rate = pool_hits / total_requests
        
        # 如果等待队列较长且命中率低,则扩容
        if wait_queue_len > 5 and hit_rate < 0.7 and current_size < self._max_connections:
            self._expand_pool()
        
        # 如果池使用率很低,则收缩
        elif hit_rate > 0.95 and wait_queue_len == 0 and current_size > self._min_connections:
            self._shrink_pool()

    def _create_connection(self):
        try:
            if self.db_type == 'sqlite':
                conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
                if SQLCIPHER_AVAILABLE:
                    encryption_key = getattr(Config, 'DATABASE_ENCRYPTION_KEY', None)
                    if not encryption_key:
                        logger.warning("未找到数据库加密密钥,使用默认密钥")
                        encryption_key = "default_key_for_development_only"

                    conn.execute(f"PRAGMA key = '{encryption_key}';")
                    conn.execute("PRAGMA cipher_compatibility = 4;")
                    logger.info("SQLCipher加密已启用")

                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA busy_timeout = 30000;")
                conn.execute("PRAGMA synchronous = NORMAL;")
                conn.execute("PRAGMA cache_size = 10000;")
                logger.info("SQLite WAL模式已启用,busy_timeout=30000ms")

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
            if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
                conn = self._thread_local.connection
                conn_id = id(conn)
                if conn_id in self._connection_metadata:
                    self._connection_metadata[conn_id]['last_used'] = time.time()
                    self._connection_metadata[conn_id]['uses'] = self._connection_metadata[conn_id].get('uses', 0) + 1
                return conn
            else:
                conn = self._create_connection()
                if conn:
                    conn_id = id(conn)
                    self._connection_metadata[conn_id] = {
                        'last_used': time.time(),
                        'uses': 1
                    }
                    self._thread_local.connection = conn
                return conn
        else:
            with self._connection_lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop(0)
                    conn_id = id(conn)
                    self._connection_metadata[conn_id]['last_used'] = time.time()
                    self._connection_metadata[conn_id]['uses'] = self._connection_metadata[conn_id].get('uses', 0) + 1
                    
                    with self._stats_lock:
                        self._stats['active_connections'] += 1
                        self._stats['pool_hits'] += 1
                    
                    return conn
                else:
                    with self._stats_lock:
                        self._stats['pool_misses'] += 1
                        self._stats['pool_dry_events'] += 1
                    
                    logger.warning("连接池已干涸,尝试创建新连接")
                    
                    # 尝试扩容
                    if len(self._connection_pool) < self._max_connections:
                        self._expand_pool()
                        if self._connection_pool:
                            conn = self._connection_pool.pop(0)
                            conn_id = id(conn)
                            self._connection_metadata[conn_id]['last_used'] = time.time()
                            self._connection_metadata[conn_id]['uses'] = self._connection_metadata[conn_id].get('uses', 0) + 1
                            
                            with self._stats_lock:
                                self._stats['active_connections'] += 1
                            
                            return conn
                
                # 如果仍然没有连接,使用等待队列
                return self._wait_for_connection()

    def _wait_for_connection(self):
        """等待可用连接"""
        start_time = time.time()
        request_id = id(threading.current_thread())
        
        try:
            self._wait_queue.put(request_id, timeout=self._wait_timeout)
            
            while time.time() - start_time < self._wait_timeout:
                with self._connection_lock:
                    if self._connection_pool:
                        conn = self._connection_pool.pop(0)
                        conn_id = id(conn)
                        self._connection_metadata[conn_id]['last_used'] = time.time()
                        self._connection_metadata[conn_id]['uses'] = self._connection_metadata[conn_id].get('uses', 0) + 1
                        
                        with self._stats_lock:
                            self._stats['active_connections'] += 1
                        
                        return conn
                
                time.sleep(0.1)
            
            logger.error("等待连接超时")
            return None
            
        except queue.Full:
            logger.error("等待队列已满")
            return None
        finally:
            # 清理等待队列中的请求
            try:
                with self._stats_lock:
                    self._stats['wait_queue_length'] = self._wait_queue.qsize()
            except Exception:
                pass

    def return_connection(self, conn):
        """将连接返回连接池或处理SQLite连接"""
        if self.db_type == 'sqlite':
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
            with self._connection_lock:
                if conn and len(self._connection_pool) < self._max_connections:
                    try:
                        if self._is_connection_valid(conn):
                            conn_id = id(conn)
                            self._connection_metadata[conn_id]['last_used'] = time.time()
                            self._connection_pool.append(conn)
                            
                            with self._stats_lock:
                                self._stats['active_connections'] -= 1
                            
                            return True
                        else:
                            conn.close()
                            conn_id = id(conn)
                            if conn_id in self._connection_metadata:
                                del self._connection_metadata[conn_id]
                    except Exception as e:
                        conn.close()
                        conn_id = id(conn)
                        if conn_id in self._connection_metadata:
                            del self._connection_metadata[conn_id]
                elif conn:
                    conn.close()
                    conn_id = id(conn)
                    if conn_id in self._connection_metadata:
                        del self._connection_metadata[conn_id]
                
                with self._stats_lock:
                    self._stats['active_connections'] = max(0, self._stats['active_connections'] - 1)
            
            return False

    def get_pool_stats(self):
        """获取连接池统计信息"""
        with self._stats_lock:
            with self._connection_lock:
                pool_size = len(self._connection_pool)
            
            return {
                'min_connections': self._min_connections,
                'max_connections': self._max_connections,
                'current_pool_size': pool_size,
                'active_connections': self._stats.get('active_connections', 0),
                'pool_hits': self._stats.get('pool_hits', 0),
                'pool_misses': self._stats.get('pool_misses', 0),
                'pool_dry_events': self._stats.get('pool_dry_events', 0),
                'wait_queue_length': self._wait_queue.qsize(),
                'expansions': self._stats.get('expansions', 0),
                'shrinks': self._stats.get('shrinks', 0),
                'total_connections': self._stats.get('total_connections', 0)
            }

    def _generate_cache_key(self, query, params):
        return f"{query}:{params}"

    def _get_from_cache(self, query, params):
        cache_key = self._generate_cache_key(query, params)
        if cache_key in self._query_cache:
            cached_data = self._query_cache[cache_key]
            if cached_data['expire_at'] > time.time():
                self._cache_access_count[cache_key] = self._cache_access_count.get(cache_key, 0) + 1
                return cached_data['result']
            else:
                del self._query_cache[cache_key]
        return None

    def _set_cache(self, query, params, result):
        with self._cache_lock:
            if len(self._query_cache) >= self._cache_size:
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
        with self._cache_lock:
            self._query_cache.clear()
            self._cache_access_count.clear()

    def _warmup_cache(self):
        with self._cache_warming_lock:
            if self._cache_warming:
                return

            self._cache_warming = True
            logger.info("开始缓存预热...")

            try:
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
        self._refill_tokens()

        with self._token_bucket_lock:
            if self._token_bucket['tokens'] >= 1:
                self._token_bucket['tokens'] -= 1
                return True
        return False

    def _calculate_olfu_score(self, key):
        access_count = self._cache_access_count.get(key, 0)
        last_access = self._cache_last_access.get(key, 0)
        now = time.time()
        time_factor = 1.0 / (1.0 + (now - last_access) / 3600)
        return access_count * time_factor

    def execute(self, query, params=None):
        if not self._consume_token():
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
        
        encrypted_query = query
        try:
            plaintext_tables = self._get_existing_plaintext_tables()
            
            encrypted_query = table_encryption.encrypt_table_names(query, skip_tables=plaintext_tables)
        except Exception as e:
            logger.debug(f"表名加密失败,使用原始查询: {str(e)}")
            encrypted_query = query

        if encrypted_query.strip().upper().startswith('SELECT'):
            cached_result = self._get_from_cache(encrypted_query, params)
            if cached_result is not None:
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

            if self.db_type != 'postgresql':
                conn.commit()

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
        cursor, success = self.execute(query, params)
        if success and cursor:
            result = cursor.fetchone()
            if not result:
                return None
            if hasattr(cursor, '_result'):
                return result

            if self.db_type == 'mysql' or self.db_type == 'postgresql':
                if hasattr(cursor, 'description') and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
            return result
        return None

    def fetch_all(self, query, params=None):
        cursor, success = self.execute(query, params)
        if success and cursor:
            results = cursor.fetchall()
            if not results:
                return []

            if hasattr(cursor, '_result'):
                return results

            if self.db_type == 'mysql' or self.db_type == 'postgresql':
                if hasattr(cursor, 'description') and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
            return results
        return []

    def fetch_scalar(self, query, params=None):
        result = self.fetch_one(query, params)
        if result:
            if isinstance(result, dict):
                return list(result.values())[0]
            return result[0] if isinstance(result, (list, tuple)) else result
        return None

    def insert(self, table, data):
        columns = ', '.join(data.keys())
        if self.db_type == 'mysql':
            placeholders = ', '.join(['%s'] * len(data))
        else:
            placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())
        cursor, success = self.execute(query, values)

        self._clear_table_cache(table)

        if success and cursor:
            if self.db_type == 'mysql':
                return cursor.lastrowid
            elif self.db_type == 'postgresql':
                query_with_returning = f"{query} RETURNING id"
                cursor, success = self.execute(query_with_returning, values)
                if success and cursor:
                    result = cursor.fetchone()
                    return result['id'] if isinstance(result, dict) else result[0]
                return None
            return cursor.lastrowid
        return None

    def update(self, table, data, where_clause, where_params=None):
        placeholders = ', '.join([f"{col} = ?" if self.db_type == 'sqlite' else f"{col} = %s" for col in data.keys()])
        values = tuple(data.values())
        
        if where_params:
            values += tuple(where_params)

        query = f"UPDATE {table} SET {placeholders} WHERE {where_clause}"
        _, success = self.execute(query, values)

        self._clear_table_cache(table)

        return success

    def delete(self, table, where_clause, where_params=None):
        query = f"DELETE FROM {table} WHERE {where_clause}"
        _, success = self.execute(query, where_params)

        self._clear_table_cache(table)

        return success

    def _clear_table_cache(self, table):
        encrypted_table = table_encryption.encrypt_table_name(table)

        with self._cache_lock:
            keys_to_delete = []
            for key in self._query_cache:
                if f"FROM {table}" in key or f"from {table}" in key or f"FROM {encrypted_table}" in key or f"from {encrypted_table}" in key:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._query_cache[key]

            if keys_to_delete:
                logger.info(f"清除了 {len(keys_to_delete)} 个与表 {table} 相关的缓存")

    def count(self, table, where_clause=None, where_params=None):
        encrypted_table = table_encryption.encrypt_table_name(table)
        query = f"SELECT COUNT(*) FROM {encrypted_table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        return self.fetch_scalar(query, where_params)

    def begin_transaction(self):
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

    def commit(self):
        """兼容旧代码的commit方法，execute()已在内部处理commit"""
        pass

    def commit_transaction(self, conn):
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
            except Exception:
                pass
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def rollback_transaction(self, conn):
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

    def _get_existing_plaintext_tables(self):
        """获取数据库中实际存在的明文表名"""
        plaintext_tables = set()
        
        if self.db_type != 'sqlite':
            return plaintext_tables
        
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for row in tables:
                    table_name = row[0]
                    
                    if not table_name.startswith('t_'):
                        plaintext_tables.add(table_name)
                    else:
                        decrypted = table_encryption.decrypt_table_name(table_name)
                        if decrypted != table_name:
                            if decrypted not in plaintext_tables:
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (decrypted,))
                                if cursor.fetchone():
                                    plaintext_tables.add(decrypted)
                
                self.return_connection(conn)
        except Exception as e:
            logger.debug(f"获取明文表列表失败: {str(e)}")
        
        return plaintext_tables

    def create_table(self, table_name, columns):
        encrypted_table_name = table_encryption.encrypt_table_name(table_name)

        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        cursor, _ = self.execute(query, (encrypted_table_name,))
        encrypted_exists = cursor.fetchone()

        if encrypted_exists:
            logger.info(f"表 {table_name} 已存在(加密为 {encrypted_table_name}), 跳过创建")
            return True

        columns_sql = []
        for col_name, col_type in columns.items():
            if self.db_type == 'mysql':
                pass
            elif self.db_type == 'postgresql':
                col_type = col_type.replace('AUTO_INCREMENT', 'SERIAL')
            columns_sql.append(f"{col_name} {col_type}")

        columns_sql = ', '.join(columns_sql)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
        _, success = self.execute(query)
        if success:
            logger.info(f"表 {table_name} (加密为 {encrypted_table_name}) 创建成功")
        return success

    def add_column(self, table_name, column_name, column_type):
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        _, success = self.execute(query)
        if success:
            logger.info(f"表 {table_name} 添加列 {column_name} 成功")
        return success

    def drop_table(self, table_name):
        query = f"DROP TABLE {table_name}"
        _, success = self.execute(query)
        if success:
            logger.info(f"表 {table_name} 删除成功")
        return success

    def vacuum(self):
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
        with self._table_lock_creation_lock:
            if table_name not in self._table_locks:
                self._table_locks[table_name] = threading.Lock()
        return self._table_locks.get(table_name)

    def create_snapshot(self, snapshot_dir=None):
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
        try:
            query = f"SELECT * FROM {table_name}"
            results = self.fetch_all(query)

            export_dir = os.path.join(os.path.dirname(self.db_path), 'exports')
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(export_dir, f'{table_name}_{timestamp}.json')

            import json
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"成功导出表 {table_name} 到JSON文件: {json_file}")
            return json_file
        except Exception as e:
            logger.error(f"导出JSON数据失败: {str(e)}")
            return None


db_manager = DatabaseManager()
