# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Redis管理器,负责Redis连接和操作
支持单机,哨兵模式和集群模式
强化版:支持主从分离,故障转移,健康监控,缓存策略,分布式锁,限流
"""

import os
import logging
import threading
import time
import json
import hashlib
from functools import wraps
from datetime import datetime
import redis
from redis.sentinel import Sentinel
from app.config import load_config
from app.utils.logging import logger
import sys

class RedisManager:
    """Redis管理器,负责Redis连接和操作"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RedisManager, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化Redis管理器"""
        self.config = load_config()
        self.redis_config = self.config.get('REDIS_CONFIG', {})
        self.connection_mode = self.redis_config.get('MODE', 'single')  # single, sentinel, cluster
        
        # 连接池配置
        self.pool_size = self.redis_config.get('POOL_SIZE', 20)
        self.pool_timeout = self.redis_config.get('POOL_TIMEOUT', 30)
        self.socket_timeout = self.redis_config.get('SOCKET_TIMEOUT', 0.5)
        self.socket_connect_timeout = self.redis_config.get('SOCKET_CONNECT_TIMEOUT', 2.0)
        
        # 重连配置
        self.reconnect_interval = self.redis_config.get('RECONNECT_INTERVAL', 5)
        self.max_reconnect_attempts = self.redis_config.get('MAX_RECONNECT_ATTEMPTS', 10)
        
        # 哨兵模式专用配置
        self.sentinel_config = {
            'nodes': self.redis_config.get('SENTINEL_NODES', [('localhost', 26379)]),
            'master_name': self.redis_config.get('MASTER_NAME', 'mymaster'),
            'password': self.redis_config.get('PASSWORD', ''),
            'db': self.redis_config.get('DB', 0),
            'socket_timeout': self.redis_config.get('SENTINEL_SOCKET_TIMEOUT', 0.1),
            'connection_pool_size': self.redis_config.get('SENTINEL_POOL_SIZE', 10),
            'read_from_slave': self.redis_config.get('READ_FROM_SLAVE', True),
            'failover_retry_delay': self.redis_config.get('FAILOVER_RETRY_DELAY', 1),
            'failover_max_retries': self.redis_config.get('FAILOVER_MAX_RETRIES', 5)
        }

        # 缓存策略配置
        self.cache_config = {
            'default_ttl': self.redis_config.get('DEFAULT_TTL', 3600),
            'short_ttl': self.redis_config.get('SHORT_TTL', 60),
            'medium_ttl': self.redis_config.get('MEDIUM_TTL', 1800),
            'long_ttl': self.redis_config.get('LONG_TTL', 86400),
            'max_memory_policy': self.redis_config.get('MAX_MEMORY_POLICY', 'allkeys-lru'),
            'cache_prefix': self.redis_config.get('CACHE_PREFIX', 'mtscos:'),
            'enable_cache': self.redis_config.get('ENABLE_CACHE', True)
        }

        # 限流配置
        self.rate_limit_config = {
            'enabled': self.redis_config.get('ENABLE_RATE_LIMIT', True),
            'default_limit': self.redis_config.get('DEFAULT_RATE_LIMIT', 100),
            'default_window': self.redis_config.get('DEFAULT_RATE_WINDOW', 60),
            'burst_limit': self.redis_config.get('BURST_LIMIT', 500)
        }

        self.connections = {}
        self.connection_lock = threading.RLock()
        self.last_failover_time = 0
        self.failover_in_progress = False
        self.slave_connections = []
        self.metrics = {
            'get_count': 0,
            'set_count': 0,
            'delete_count': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'last_reset': datetime.now().isoformat()
        }

        self._use_memory_fallback = False
        self._memory_cache = {}
        self._memory_cache_expire = {}
        self._memory_cache_lock = threading.RLock()

        self._init_connections()

        # 启动连接监控线程
        self._monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self._monitor_thread.start()
        
        # 启动哨兵信息刷新线程(哨兵模式专用)
        if self.connection_mode == 'sentinel':
            self._sentinel_refresh_thread = threading.Thread(target=self._refresh_sentinel_info, daemon=True)
            self._sentinel_refresh_thread.start()
        
        # 启动指标收集线程
        self._metrics_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        self._metrics_thread.start()
        
        logger.info("Redis管理器初始化完成,模式: {}".format(self.connection_mode))

    def _init_connections(self):
        """初始化Redis连接"""
        with self.connection_lock:
            if self.connection_mode == 'single':
                self._init_single_connection()
            elif self.connection_mode == 'sentinel':
                self._init_sentinel_connection()
            elif self.connection_mode == 'cluster':
                self._init_cluster_connection()
            else:
                logger.error(f"不支持的Redis连接模式: {self.connection_mode}")
            
            if not self.connections and not hasattr(self, 'master'):
                self._use_memory_fallback = True
                logger.warning("Redis连接失败，自动切换到内存缓存模式")

    def _init_single_connection(self):
        """初始化单机模式连接"""
        try:
            host = self.redis_config.get('HOST', 'localhost')
            port = self.redis_config.get('PORT', 6379)
            password = self.redis_config.get('PASSWORD', '')
            db = self.redis_config.get('DB', 0)

            pool = redis.ConnectionPool(
                host=host,
                port=port,
                password=password,
                db=db,
                max_connections=self.pool_size,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                decode_responses=True
            )
            
            self.connections['default'] = redis.Redis(connection_pool=pool)
            self.connections['default'].ping()
            logger.info(f"Redis单机连接成功: {host}:{port}")
        except Exception as e:
            logger.error(f"Redis单机连接失败: {str(e)}")

    def _init_sentinel_connection(self):
        """初始化哨兵模式连接 - 强化版"""
        try:
            sentinel_nodes = self.sentinel_config['nodes']
            master_name = self.sentinel_config['master_name']
            password = self.sentinel_config['password']
            db = self.sentinel_config['db']
            socket_timeout = self.sentinel_config['socket_timeout']
            pool_size = self.sentinel_config['connection_pool_size']

            self.sentinel = Sentinel(
                sentinel_nodes,
                socket_timeout=socket_timeout,
                password=password,
                db=db,
                decode_responses=True
            )

            self.master = self.sentinel.master_for(
                master_name,
                socket_timeout=socket_timeout,
                password=password,
                db=db,
                max_connections=pool_size,
                decode_responses=True
            )

            if self.sentinel_config['read_from_slave']:
                self.slave = self.sentinel.slave_for(
                    master_name,
                    socket_timeout=socket_timeout,
                    password=password,
                    db=db,
                    max_connections=pool_size,
                    decode_responses=True
                )
            else:
                self.slave = self.master

            self.master.ping()
            self.slave.ping()
            
            self.connections['sentinel'] = self.sentinel
            self.connections['master'] = self.master
            self.connections['slave'] = self.slave

            self._update_sentinel_info()
            
            logger.info(f"Redis哨兵模式连接成功")
            logger.info(f"  哨兵节点: {sentinel_nodes}")
            logger.info(f"  主节点: {self.master_address}")
            logger.info(f"  从节点数: {len(self.slave_addresses)}")
            logger.info(f"  读写分离: {'开启' if self.sentinel_config['read_from_slave'] else '关闭'}")

        except Exception as e:
            logger.error(f"Redis哨兵模式连接失败: {str(e)}")
            raise

    def _update_sentinel_info(self):
        """更新哨兵信息"""
        try:
            if self.connection_mode == 'sentinel' and hasattr(self, 'sentinel'):
                self.master_address = self.sentinel.discover_master(self.sentinel_config['master_name'])
                self.slave_addresses = self.sentinel.discover_slaves(self.sentinel_config['master_name'])
                
                self.sentinel_status = []
                for sentinel_node in self.sentinel_config['nodes']:
                    try:
                        sentinel_conn = redis.Redis(
                            host=sentinel_node[0],
                            port=sentinel_node[1],
                            password=self.sentinel_config['password'],
                            socket_timeout=0.5
                        )
                        info = sentinel_conn.info('sentinel')
                        self.sentinel_status.append({
                            'node': sentinel_node,
                            'status': 'online',
                            'info': info
                        })
                        sentinel_conn.close()
                    except Exception as e:
                        self.sentinel_status.append({
                            'node': sentinel_node,
                            'status': 'offline',
                            'error': str(e)
                        })
        except Exception as e:
            logger.error(f"更新哨兵信息失败: {str(e)}")

    def _init_cluster_connection(self):
        """初始化集群模式连接"""
        try:
            cluster_nodes = self.redis_config.get('CLUSTER_NODES', [
                {'host': 'localhost', 'port': 7000},
                {'host': 'localhost', 'port': 7001},
            ])
            password = self.redis_config.get('PASSWORD', '')

            startup_nodes = [(node['host'], node['port']) for node in cluster_nodes]

            self.connections['cluster'] = redis.RedisCluster(
                startup_nodes=startup_nodes,
                password=password,
                decode_responses=True,
                skip_full_coverage_check=True,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout
            )

            self.connections['cluster'].ping()
            logger.info(f"Redis集群模式连接成功: {cluster_nodes}")
        except Exception as e:
            logger.error(f"Redis集群模式连接失败: {str(e)}")

    def _monitor_connections(self):
        """监控Redis连接状态"""
        while True:
            try:
                time.sleep(10)
                with self.connection_lock:
                    if self.connection_mode == 'single':
                        self._monitor_single_connection()
                    elif self.connection_mode == 'sentinel':
                        self._monitor_sentinel_connection()
                    elif self.connection_mode == 'cluster':
                        self._monitor_cluster_connection()
            except Exception as e:
                logger.error(f"监控Redis连接失败: {str(e)}")

    def _monitor_single_connection(self):
        """监控单机模式连接"""
        if 'default' in self.connections:
            try:
                self.connections['default'].ping()
                logger.debug("Redis单机连接正常")
            except Exception as e:
                logger.error(f"Redis单机连接异常: {str(e)}")
                self._reconnect()

    def _monitor_sentinel_connection(self):
        """监控哨兵模式连接"""
        if not hasattr(self, 'master'):
            return

        try:
            self.master.ping()
            logger.debug("Redis哨兵主节点连接正常")
            
            if self.sentinel_config['read_from_slave'] and hasattr(self, 'slave'):
                self.slave.ping()
                logger.debug("Redis哨兵从节点连接正常")
            
            self._check_sentinel_health()
        except Exception as e:
            logger.error(f"Redis哨兵模式连接异常: {str(e)}")
            self._handle_sentinel_failover()

    def _check_sentinel_health(self):
        """检查哨兵节点健康状态"""
        if not hasattr(self, 'sentinel_status'):
            return

        offline_sentinels = [s for s in self.sentinel_status if s['status'] == 'offline']
        if offline_sentinels:
            logger.warning(f"检测到 {len(offline_sentinels)} 个哨兵节点离线")

    def _handle_sentinel_failover(self):
        """处理哨兵故障转移"""
        current_time = time.time()
        
        if current_time - self.last_failover_time < 30:
            logger.info("故障转移冷却中,跳过本次尝试")
            return

        if self.failover_in_progress:
            logger.info("故障转移正在进行中")
            return

        self.failover_in_progress = True
        self.last_failover_time = current_time

        try:
            logger.info("开始Redis哨兵故障转移处理...")
            
            retries = self.sentinel_config['failover_max_retries']
            delay = self.sentinel_config['failover_retry_delay']
            
            for attempt in range(retries):
                try:
                    logger.info(f"故障转移尝试 {attempt + 1}/{retries}")
                    
                    self._update_sentinel_info()
                    
                    master_name = self.sentinel_config['master_name']
                    password = self.sentinel_config['password']
                    db = self.sentinel_config['db']
                    socket_timeout = self.sentinel_config['socket_timeout']
                    pool_size = self.sentinel_config['connection_pool_size']
                    
                    self.master = self.sentinel.master_for(
                        master_name, socket_timeout=socket_timeout,
                        password=password, db=db, max_connections=pool_size,
                        decode_responses=True
                    )
                    
                    if self.sentinel_config['read_from_slave']:
                        self.slave = self.sentinel.slave_for(
                            master_name, socket_timeout=socket_timeout,
                            password=password, db=db, max_connections=pool_size,
                            decode_responses=True
                        )
                    else:
                        self.slave = self.master
                    
                    self.master.ping()
                    logger.info(f"Redis哨兵故障转移成功,新主节点: {self.master_address}")
                    return
                    
                except Exception as e:
                    logger.error(f"故障转移尝试 {attempt + 1} 失败: {str(e)}")
                    time.sleep(delay * (attempt + 1))
            
            logger.error("Redis哨兵故障转移失败,达到最大重试次数")
            
        finally:
            self.failover_in_progress = False

    def _monitor_cluster_connection(self):
        """监控集群模式连接"""
        if 'cluster' in self.connections:
            try:
                self.connections['cluster'].ping()
                logger.debug("Redis集群连接正常")
            except Exception as e:
                logger.error(f"Redis集群连接异常: {str(e)}")
                self._reconnect()

    def _refresh_sentinel_info(self):
        """定期刷新哨兵信息"""
        while True:
            try:
                if self.connection_mode == 'sentinel':
                    self._update_sentinel_info()
                    logger.debug(f"哨兵信息已刷新")
            except Exception as e:
                logger.error(f"刷新哨兵信息失败: {str(e)}")
            time.sleep(60)

    def _collect_metrics(self):
        """收集Redis操作指标"""
        while True:
            try:
                time.sleep(60)
                logger.debug(f"Redis指标: {self.metrics}")
            except Exception as e:
                logger.error(f"收集Redis指标失败: {str(e)}")

    def _reconnect(self):
        """重新连接Redis"""
        attempts = 0
        while attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"尝试重新连接Redis (尝试 {attempts+1}/{self.max_reconnect_attempts})")
                self.connections.clear()
                self._init_connections()
                logger.info("Redis重新连接成功")
                return
            except Exception as e:
                logger.error(f"Redis重新连接失败: {str(e)}")
                attempts += 1
                time.sleep(self.reconnect_interval)
        
        logger.error("Redis重新连接失败,达到最大尝试次数")

    def get_connection(self, connection_type=None):
        """获取Redis连接"""
        with self.connection_lock:
            if connection_type == 'write' or connection_type == 'master':
                if self.connection_mode == 'sentinel' and hasattr(self, 'master'):
                    return self.master
                elif 'master' in self.connections:
                    return self.connections['master']
            
            if connection_type == 'read' or connection_type == 'slave':
                if self.connection_mode == 'sentinel' and hasattr(self, 'slave'):
                    return self.slave
                elif 'slave' in self.connections:
                    return self.connections['slave']
            
            if connection_type in self.connections:
                return self.connections[connection_type]
            elif 'default' in self.connections:
                return self.connections['default']
            elif 'master' in self.connections:
                return self.connections['master']
            elif 'cluster' in self.connections:
                return self.connections['cluster']
            elif self.connection_mode == 'sentinel' and hasattr(self, 'master'):
                return self.master
            
            logger.error("没有可用的Redis连接")
            return None

    def get_master_connection(self):
        """获取主节点连接"""
        return self.get_connection('master')

    def get_slave_connection(self):
        """获取从节点连接"""
        return self.get_connection('slave')

    # ========== 通用操作方法 ==========

    def _get_full_key(self, key):
        """获取带前缀的完整键名"""
        return f"{self.cache_config['cache_prefix']}{key}"

    def set(self, key, value, expire=None):
        """设置键值对"""
        try:
            conn = self.get_master_connection()
            ttl = expire if expire else self.cache_config['default_ttl']

            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if conn:
                full_key = self._get_full_key(key)
                if ttl:
                    result = conn.setex(full_key, ttl, value)
                else:
                    result = conn.set(full_key, value)
                self.metrics['set_count'] += 1
                return result
            else:
                if self._use_memory_fallback:
                    full_key = self._get_full_key(key)
                    with self._memory_cache_lock:
                        self._memory_cache[full_key] = value
                        if ttl:
                            self._memory_cache_expire[full_key] = time.time() + ttl
                        else:
                            self._memory_cache_expire[full_key] = None
                    self.metrics['set_count'] += 1
                    logger.debug(f"内存缓存 set: {full_key}")
                    return True
                return False
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Redis set操作失败: {str(e)}")
            if self._use_memory_fallback:
                full_key = self._get_full_key(key)
                with self._memory_cache_lock:
                    self._memory_cache[full_key] = value
                    ttl = expire if expire else self.cache_config['default_ttl']
                    if ttl:
                        self._memory_cache_expire[full_key] = time.time() + ttl
                    else:
                        self._memory_cache_expire[full_key] = None
                self.metrics['set_count'] += 1
                return True
            return False

    def get(self, key, default=None, prefer_slave=True):
        """获取键值"""
        try:
            if prefer_slave and self.connection_mode == 'sentinel':
                conn = self.get_slave_connection()
            else:
                conn = self.get_connection()

            full_key = self._get_full_key(key)

            if conn:
                value = conn.get(full_key)
                
                if value is None:
                    self.metrics['misses'] += 1
                    if self._use_memory_fallback:
                        with self._memory_cache_lock:
                            if full_key in self._memory_cache:
                                expire_time = self._memory_cache_expire.get(full_key)
                                if expire_time is None or expire_time > time.time():
                                    value = self._memory_cache[full_key]
                                    self.metrics['hits'] += 1
                                    self.metrics['misses'] -= 1
                                    try:
                                        return json.loads(value)
                                    except (json.JSONDecodeError, TypeError):
                                        return value
                    return default

                self.metrics['hits'] += 1
                self.metrics['get_count'] += 1

                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_key in self._memory_cache:
                            expire_time = self._memory_cache_expire.get(full_key)
                            if expire_time is None or expire_time > time.time():
                                value = self._memory_cache[full_key]
                                self.metrics['hits'] += 1
                                self.metrics['get_count'] += 1
                                try:
                                    return json.loads(value)
                                except (json.JSONDecodeError, TypeError):
                                    return value
                            else:
                                del self._memory_cache[full_key]
                                del self._memory_cache_expire[full_key]
                    self.metrics['misses'] += 1
                return default
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Redis get操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_key in self._memory_cache:
                        expire_time = self._memory_cache_expire.get(full_key)
                        if expire_time is None or expire_time > time.time():
                            value = self._memory_cache[full_key]
                            self.metrics['hits'] += 1
                            self.metrics['get_count'] += 1
                            try:
                                return json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                return value
                self.metrics['misses'] += 1
            return default

    def delete(self, key):
        """删除键"""
        try:
            conn = self.get_master_connection()
            full_key = self._get_full_key(key)

            if conn:
                result = bool(conn.delete(full_key))
                self.metrics['delete_count'] += 1
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        self._memory_cache.pop(full_key, None)
                        self._memory_cache_expire.pop(full_key, None)
                return result
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        self._memory_cache.pop(full_key, None)
                        self._memory_cache_expire.pop(full_key, None)
                    self.metrics['delete_count'] += 1
                    return True
                return False
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Redis delete操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    self._memory_cache.pop(full_key, None)
                    self._memory_cache_expire.pop(full_key, None)
                self.metrics['delete_count'] += 1
                return True
            return False

    def exists(self, key):
        """检查键是否存在"""
        try:
            conn = self.get_connection()
            full_key = self._get_full_key(key)

            if conn:
                return bool(conn.exists(full_key))
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_key in self._memory_cache:
                            expire_time = self._memory_cache_expire.get(full_key)
                            if expire_time is None or expire_time > time.time():
                                return True
                            else:
                                del self._memory_cache[full_key]
                                del self._memory_cache_expire[full_key]
                    return False
                return False
        except Exception as e:
            logger.error(f"Redis exists操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_key in self._memory_cache:
                        expire_time = self._memory_cache_expire.get(full_key)
                        if expire_time is None or expire_time > time.time():
                            return True
                return False
            return False

    def expire(self, key, seconds):
        """设置键的过期时间"""
        try:
            conn = self.get_master_connection()
            full_key = self._get_full_key(key)

            if conn:
                result = bool(conn.expire(full_key, seconds))
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_key in self._memory_cache:
                            self._memory_cache_expire[full_key] = time.time() + seconds
                return result
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_key in self._memory_cache:
                            self._memory_cache_expire[full_key] = time.time() + seconds
                            return True
                    return False
                return False
        except Exception as e:
            logger.error(f"Redis expire操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_key in self._memory_cache:
                        self._memory_cache_expire[full_key] = time.time() + seconds
                        return True
                return False
            return False

    def ttl(self, key):
        """获取键的剩余过期时间"""
        try:
            conn = self.get_connection()
            full_key = self._get_full_key(key)

            if conn:
                return conn.ttl(full_key)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_key in self._memory_cache:
                            expire_time = self._memory_cache_expire.get(full_key)
                            if expire_time is None:
                                return -1
                            remaining = int(expire_time - time.time())
                            if remaining <= 0:
                                del self._memory_cache[full_key]
                                del self._memory_cache_expire[full_key]
                                return -2
                            return remaining
                    return -2
                return -2
        except Exception as e:
            logger.error(f"Redis ttl操作失败: {str(e)}")
            return -2

    def ping(self):
        """测试Redis连接"""
        try:
            conn = self.get_connection()
            if conn:
                return conn.ping()
            elif self._use_memory_fallback:
                return True
            return False
        except Exception as e:
            logger.error(f"Redis ping操作失败: {str(e)}")
            if self._use_memory_fallback:
                return True
            return False

    # ========== Hash操作 ==========

    def hset(self, name, key, value):
        """设置哈希表字段"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if conn:
                return bool(conn.hset(full_name, key, value))
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name not in self._memory_cache:
                            self._memory_cache[full_name] = {}
                        self._memory_cache[full_name][key] = value
                        self._memory_cache_expire[full_name] = None
                    return True
                return False
        except Exception as e:
            logger.error(f"Redis hset操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_name not in self._memory_cache:
                        self._memory_cache[full_name] = {}
                    self._memory_cache[full_name][key] = value
                    self._memory_cache_expire[full_name] = None
                return True
            return False

    def hget(self, name, key, default=None):
        """获取哈希表字段"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                value = conn.hget(full_name, key)
                if value is None:
                    return default
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            value = self._memory_cache[full_name].get(key)
                            if value is None:
                                return default
                            try:
                                return json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                return value
                    return default
                return default
        except Exception as e:
            logger.error(f"Redis hget操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_name in self._memory_cache:
                        value = self._memory_cache[full_name].get(key)
                        if value is None:
                            return default
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                return default
            return default

    def hgetall(self, name):
        """获取哈希表所有字段"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                data = conn.hgetall(full_name)
                result = {}
                for key, value in data.items():
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
                return result
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            data = self._memory_cache[full_name]
                            result = {}
                            for key, value in data.items():
                                try:
                                    result[key] = json.loads(value)
                                except (json.JSONDecodeError, TypeError):
                                    result[key] = value
                            return result
                    return {}
                return {}
        except Exception as e:
            logger.error(f"Redis hgetall操作失败: {str(e)}")
            return {}

    def hdel(self, name, key):
        """删除哈希表字段"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)

            if conn:
                return bool(conn.hdel(full_name, key))
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            if key in self._memory_cache[full_name]:
                                del self._memory_cache[full_name][key]
                                return True
                    return False
                return False
        except Exception as e:
            logger.error(f"Redis hdel操作失败: {str(e)}")
            return False

    # ========== 列表操作 ==========

    def lpush(self, name, *values):
        """将值推入列表左侧"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)
            serial_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serial_values.append(json.dumps(value))
                else:
                    serial_values.append(value)
            
            if conn:
                return conn.lpush(full_name, *serial_values)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name not in self._memory_cache:
                            self._memory_cache[full_name] = []
                        self._memory_cache[full_name] = serial_values + self._memory_cache[full_name]
                        self._memory_cache_expire[full_name] = None
                    return len(self._memory_cache[full_name])
                return 0
        except Exception as e:
            logger.error(f"Redis lpush操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_name not in self._memory_cache:
                        self._memory_cache[full_name] = []
                    self._memory_cache[full_name] = serial_values + self._memory_cache[full_name]
                    self._memory_cache_expire[full_name] = None
                return len(self._memory_cache[full_name])
            return 0

    def rpush(self, name, *values):
        """将值推入列表右侧"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)
            serial_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serial_values.append(json.dumps(value))
                else:
                    serial_values.append(value)
            
            if conn:
                return conn.rpush(full_name, *serial_values)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name not in self._memory_cache:
                            self._memory_cache[full_name] = []
                        self._memory_cache[full_name].extend(serial_values)
                        self._memory_cache_expire[full_name] = None
                    return len(self._memory_cache[full_name])
                return 0
        except Exception as e:
            logger.error(f"Redis rpush操作失败: {str(e)}")
            if self._use_memory_fallback:
                with self._memory_cache_lock:
                    if full_name not in self._memory_cache:
                        self._memory_cache[full_name] = []
                    self._memory_cache[full_name].extend(serial_values)
                    self._memory_cache_expire[full_name] = None
                return len(self._memory_cache[full_name])
            return 0

    def lrange(self, name, start, end):
        """获取列表指定范围的元素"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                values = conn.lrange(full_name, start, end)
                result = []
                for value in values:
                    try:
                        result.append(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        result.append(value)
                return result
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            values = self._memory_cache[full_name]
                            if end == -1:
                                end = len(values)
                            result = []
                            for value in values[start:end+1]:
                                try:
                                    result.append(json.loads(value))
                                except (json.JSONDecodeError, TypeError):
                                    result.append(value)
                            return result
                    return []
                return []
        except Exception as e:
            logger.error(f"Redis lrange操作失败: {str(e)}")
            return []

    def llen(self, name):
        """获取列表长度"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.llen(full_name)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            return len(self._memory_cache[full_name])
                    return 0
                return 0
        except Exception as e:
            logger.error(f"Redis llen操作失败: {str(e)}")
            return 0

    # ========== 集合操作 ==========

    def sadd(self, name, *values):
        """添加元素到集合"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.sadd(full_name, *values)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name not in self._memory_cache:
                            self._memory_cache[full_name] = set()
                        count = 0
                        for v in values:
                            if v not in self._memory_cache[full_name]:
                                self._memory_cache[full_name].add(v)
                                count += 1
                        self._memory_cache_expire[full_name] = None
                    return count
                return 0
        except Exception as e:
            logger.error(f"Redis sadd操作失败: {str(e)}")
            return 0

    def smembers(self, name):
        """获取集合所有元素"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.smembers(full_name)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            return set(self._memory_cache[full_name])
                    return set()
                return set()
        except Exception as e:
            logger.error(f"Redis smembers操作失败: {str(e)}")
            return set()

    def sismember(self, name, value):
        """检查元素是否在集合中"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.sismember(full_name, value)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            return value in self._memory_cache[full_name]
                    return False
                return False
        except Exception as e:
            logger.error(f"Redis sismember操作失败: {str(e)}")
            return False

    def srem(self, name, *values):
        """从集合中移除元素"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.srem(full_name, *values)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            count = 0
                            for v in values:
                                if v in self._memory_cache[full_name]:
                                    self._memory_cache[full_name].remove(v)
                                    count += 1
                            return count
                    return 0
                return 0
        except Exception as e:
            logger.error(f"Redis srem操作失败: {str(e)}")
            return 0

    # ========== 有序集合操作 ==========

    def zadd(self, name, *args, **kwargs):
        """添加元素到有序集合"""
        try:
            conn = self.get_master_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.zadd(full_name, *args, **kwargs)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name not in self._memory_cache:
                            self._memory_cache[full_name] = {}
                        for k, v in kwargs.items():
                            self._memory_cache[full_name][k] = v
                        if args:
                            for i in range(0, len(args), 2):
                                self._memory_cache[full_name][args[i]] = args[i+1]
                        self._memory_cache_expire[full_name] = None
                    return len(kwargs) + len(args) // 2
                return 0
        except Exception as e:
            logger.error(f"Redis zadd操作失败: {str(e)}")
            return 0

    def zrange(self, name, start, end, desc=False, withscores=False):
        """获取有序集合指定范围的元素"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.zrange(full_name, start, end, desc=desc, withscores=withscores)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            items = list(self._memory_cache[full_name].items())
                            items.sort(key=lambda x: x[1], reverse=desc)
                            if end == -1:
                                end = len(items)
                            result = items[start:end+1]
                            if withscores:
                                return result
                            return [item[0] for item in result]
                    return []
                return []
        except Exception as e:
            logger.error(f"Redis zrange操作失败: {str(e)}")
            return []

    def zrank(self, name, value):
        """获取元素在有序集合中的排名"""
        try:
            conn = self.get_connection()
            full_name = self._get_full_key(name)

            if conn:
                return conn.zrank(full_name, value)
            else:
                if self._use_memory_fallback:
                    with self._memory_cache_lock:
                        if full_name in self._memory_cache:
                            items = list(self._memory_cache[full_name].items())
                            items.sort(key=lambda x: x[1])
                            for i, (k, v) in enumerate(items):
                                if k == value:
                                    return i
                    return None
                return None
        except Exception as e:
            logger.error(f"Redis zrank操作失败: {str(e)}")
            return None

    # ========== 缓存装饰器 ==========

    def cached(self, ttl=None, key_prefix='cache'):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.cache_config['enable_cache']:
                    return func(*args, **kwargs)
                
                key_args = str(args) + str(kwargs)
                key_hash = hashlib.md5(key_args.encode()).hexdigest()
                cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"
                
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator

    # ========== 分布式锁 ==========

    def acquire_lock(self, lock_name, acquire_timeout=10, lock_timeout=60):
        """获取分布式锁"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return None
            
            lock_key = f"lock:{lock_name}"
            identifier = hashlib.uuid4().hex
            end = time.time() + acquire_timeout
            
            while time.time() < end:
                if conn.set(lock_key, identifier, ex=lock_timeout, nx=True):
                    return identifier
                
                time.sleep(0.1)
            
            return None
        except Exception as e:
            logger.error(f"获取分布式锁失败: {str(e)}")
            return None

    def release_lock(self, lock_name, identifier):
        """释放分布式锁"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return False
            
            lock_key = f"lock:{lock_name}"
            
            while True:
                conn.watch(lock_key)
                if conn.get(lock_key) == identifier:
                    pipe = conn.pipeline()
                    pipe.delete(lock_key)
                    pipe.execute()
                    return True
                
                conn.unwatch()
                break
            
            return False
        except Exception as e:
            logger.error(f"释放分布式锁失败: {str(e)}")
            return False

    # ========== 限流功能 ==========

    def is_rate_limited(self, key, limit=None, window=None):
        """检查是否限流"""
        if not self.rate_limit_config['enabled']:
            return False
        
        try:
            conn = self.get_master_connection()
            if not conn:
                return False
            
            rate_key = f"rate_limit:{key}"
            current_limit = limit if limit else self.rate_limit_config['default_limit']
            current_window = window if window else self.rate_limit_config['default_window']
            
            current = conn.incr(rate_key)
            if current == 1:
                conn.expire(rate_key, current_window)
            
            return current > current_limit
        except Exception as e:
            logger.error(f"限流检查失败: {str(e)}")
            return False

    def get_rate_limit_info(self, key):
        """获取限流信息"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            rate_key = f"rate_limit:{key}"
            count = conn.get(rate_key)
            ttl = conn.ttl(rate_key)
            
            return {
                'count': int(count) if count else 0,
                'ttl': ttl,
                'limit': self.rate_limit_config['default_limit']
            }
        except Exception as e:
            logger.error(f"获取限流信息失败: {str(e)}")
            return None

    # ========== 哨兵模式专用方法 ==========

    def get_sentinel_status(self):
        """获取哨兵模式状态信息"""
        if self.connection_mode != 'sentinel':
            return {'error': '当前不是哨兵模式'}
        
        return {
            'master_name': self.sentinel_config['master_name'],
            'master_address': getattr(self, 'master_address', None),
            'slave_addresses': getattr(self, 'slave_addresses', []),
            'sentinel_nodes': self.sentinel_config['nodes'],
            'sentinel_status': getattr(self, 'sentinel_status', []),
            'read_from_slave': self.sentinel_config['read_from_slave'],
            'last_failover_time': self.last_failover_time,
            'failover_in_progress': self.failover_in_progress
        }

    def trigger_failover_check(self):
        """手动触发故障转移检查"""
        if self.connection_mode == 'sentinel':
            self._handle_sentinel_failover()
            return True
        return False

    # ========== 指标和状态 ==========

    def get_metrics(self):
        """获取Redis操作指标"""
        return self.metrics.copy()

    def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            'get_count': 0,
            'set_count': 0,
            'delete_count': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'last_reset': datetime.now().isoformat()
        }

    def get_stats(self):
        """获取Redis状态统计"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            info = conn.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', ''),
                'used_cpu_sys': info.get('used_cpu_sys', 0),
                'used_cpu_user': info.get('used_cpu_user', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"获取Redis状态失败: {str(e)}")
            return None

# 创建Redis管理器实例
redis_manager = RedisManager()