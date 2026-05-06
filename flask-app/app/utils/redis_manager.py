#!/usr/bin/env python3
"""
Redis管理器，负责Redis连接和操作
支持单机、哨兵模式和集群模式
强化版哨兵模式：支持主从分离、故障转移、健康监控
"""

import os
# import json removed - using database storage
import logging
import threading
import time
import redis
from redis.sentinel import Sentinel
from app.config import load_config
from app.utils.logging import logger

class RedisManager:
    """Redis管理器，负责Redis连接和操作"""

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

        self.connections = {}
        self.connection_lock = threading.RLock()
        self.last_failover_time = 0
        self.failover_in_progress = False
        self.slave_connections = []

        # 初始化连接
        self._init_connections()

        # 启动连接监控线程
        self._monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self._monitor_thread.start()
        
        # 启动哨兵信息刷新线程（哨兵模式专用）
        if self.connection_mode == 'sentinel':
            self._sentinel_refresh_thread = threading.Thread(target=self._refresh_sentinel_info, daemon=True)
            self._sentinel_refresh_thread.start()
        
        logger.info("Redis管理器初始化完成，模式: {}".format(self.connection_mode))

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
                socket_connect_timeout=self.socket_connect_timeout
            )
            
            self.connections['default'] = redis.Redis(
                connection_pool=pool,
                decode_responses=True
            )

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

            # 创建哨兵实例
            self.sentinel = Sentinel(
                sentinel_nodes,
                socket_timeout=socket_timeout,
                password=password,
                db=db
            )

            # 创建主节点连接池
            self.master_pool = redis.ConnectionPool(
                connection_class=redis.connection.Connection,
                max_connections=pool_size,
                socket_timeout=socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                password=password,
                db=db,
                decode_responses=True
            )

            # 创建从节点连接池
            self.slave_pool = redis.ConnectionPool(
                connection_class=redis.connection.Connection,
                max_connections=pool_size,
                socket_timeout=socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                password=password,
                db=db,
                decode_responses=True
            )

            # 获取主节点连接
            self.master = self.sentinel.master_for(
                master_name,
                socket_timeout=socket_timeout,
                password=password,
                db=db,
                decode_responses=True,
                max_connections=pool_size
            )

            # 获取从节点连接（支持读写分离）
            if self.sentinel_config['read_from_slave']:
                self.slave = self.sentinel.slave_for(
                    master_name,
                    socket_timeout=socket_timeout,
                    password=password,
                    db=db,
                    decode_responses=True,
                    max_connections=pool_size
                )
            else:
                self.slave = self.master

            # 测试连接
            master_pong = self.master.ping()
            slave_pong = self.slave.ping()
            
            self.connections['sentinel'] = self.sentinel
            self.connections['master'] = self.master
            self.connections['slave'] = self.slave

            # 获取哨兵信息
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
                # 获取主节点信息
                master_info = self.sentinel.discover_master(self.sentinel_config['master_name'])
                self.master_address = master_info
                
                # 获取从节点列表
                slave_info = self.sentinel.discover_slaves(self.sentinel_config['master_name'])
                self.slave_addresses = slave_info
                
                # 获取哨兵状态
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
                time.sleep(10)  # 每10秒检查一次
                
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
        """监控哨兵模式连接 - 强化版"""
        if not hasattr(self, 'master'):
            return

        try:
            # 检查主节点
            self.master.ping()
            logger.debug("Redis哨兵主节点连接正常")
            
            # 检查从节点（如果启用读写分离）
            if self.sentinel_config['read_from_slave'] and hasattr(self, 'slave'):
                self.slave.ping()
                logger.debug("Redis哨兵从节点连接正常")
            
            # 检查哨兵节点状态
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
            logger.warning(f"检测到 {len(offline_sentinels)} 个哨兵节点离线: {[s['node'] for s in offline_sentinels]}")

    def _handle_sentinel_failover(self):
        """处理哨兵故障转移"""
        current_time = time.time()
        
        # 防止频繁故障转移
        if current_time - self.last_failover_time < 30:
            logger.info("故障转移冷却中，跳过本次尝试")
            return

        # 检查是否正在进行故障转移
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
                    
                    # 刷新哨兵信息
                    self._update_sentinel_info()
                    
                    # 重新获取主从连接
                    master_name = self.sentinel_config['master_name']
                    password = self.sentinel_config['password']
                    db = self.sentinel_config['db']
                    socket_timeout = self.sentinel_config['socket_timeout']
                    pool_size = self.sentinel_config['connection_pool_size']
                    
                    self.master = self.sentinel.master_for(
                        master_name,
                        socket_timeout=socket_timeout,
                        password=password,
                        db=db,
                        decode_responses=True,
                        max_connections=pool_size
                    )
                    
                    if self.sentinel_config['read_from_slave']:
                        self.slave = self.sentinel.slave_for(
                            master_name,
                            socket_timeout=socket_timeout,
                            password=password,
                            db=db,
                            decode_responses=True,
                            max_connections=pool_size
                        )
                    else:
                        self.slave = self.master
                    
                    # 测试新连接
                    self.master.ping()
                    logger.info("Redis哨兵故障转移成功")
                    logger.info(f"  新主节点: {self.master_address}")
                    return
                    
                except Exception as e:
                    logger.error(f"故障转移尝试 {attempt + 1} 失败: {str(e)}")
                    time.sleep(delay * (attempt + 1))  # 指数退避
            
            logger.error("Redis哨兵故障转移失败，达到最大重试次数")
            
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
                    logger.debug(f"哨兵信息已刷新 - 主节点: {self.master_address}, 从节点数: {len(self.slave_addresses)}")
            except Exception as e:
                logger.error(f"刷新哨兵信息失败: {str(e)}")
            
            time.sleep(60)  # 每分钟刷新一次

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
        
        logger.error("Redis重新连接失败，达到最大尝试次数")

    def get_connection(self, connection_type=None):
        """获取Redis连接
        
        Args:
            connection_type: 连接类型，default, master, slave, cluster, read, write
        
        Returns:
            Redis连接对象
        """
        with self.connection_lock:
            # 根据操作类型选择连接
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
            
            # 默认返回策略
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
        """获取主节点连接（用于写操作）"""
        return self.get_connection('master')

    def get_slave_connection(self):
        """获取从节点连接（用于读操作）"""
        return self.get_connection('slave')

    # ========== 通用操作方法 ==========

    def set(self, key, value, expire=None):
        """设置键值对（使用主节点）"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return False

            if isinstance(value, (dict, list)):
                value = str(value)

            if expire:
                return conn.setex(key, expire, value)
            else:
                return conn.set(key, value)
        except Exception as e:
            logger.error(f"Redis set操作失败: {str(e)}")
            return False

    def get(self, key, default=None, prefer_slave=True):
        """获取键值（优先使用从节点）"""
        try:
            if prefer_slave and self.connection_mode == 'sentinel':
                conn = self.get_slave_connection()
            else:
                conn = self.get_connection()
            
            if not conn:
                return default

            value = conn.get(key)
            if value is None:
                return default

            try:
                return eval(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis get操作失败: {str(e)}")
            return default

    def delete(self, key):
        """删除键（使用主节点）"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return False
            return bool(conn.delete(key))
        except Exception as e:
            logger.error(f"Redis delete操作失败: {str(e)}")
            return False

    def exists(self, key):
        """检查键是否存在"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            return bool(conn.exists(key))
        except Exception as e:
            logger.error(f"Redis exists操作失败: {str(e)}")
            return False

    def expire(self, key, seconds):
        """设置键的过期时间"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return False
            return bool(conn.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis expire操作失败: {str(e)}")
            return False

    def ttl(self, key):
        """获取键的剩余过期时间"""
        try:
            conn = self.get_connection()
            if not conn:
                return -2
            return conn.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl操作失败: {str(e)}")
            return -2

    def ping(self):
        """测试Redis连接"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            return conn.ping()
        except Exception as e:
            logger.error(f"Redis ping操作失败: {str(e)}")
            return False

    # ========== Hash操作 ==========

    def hset(self, name, key, value):
        """设置哈希表字段"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return False
            
            if isinstance(value, (dict, list)):
                value = str(value)
            
            return bool(conn.hset(name, key, value))
        except Exception as e:
            logger.error(f"Redis hset操作失败: {str(e)}")
            return False

    def hget(self, name, key, default=None):
        """获取哈希表字段"""
        try:
            conn = self.get_connection()
            if not conn:
                return default
            
            value = conn.hget(name, key)
            if value is None:
                return default
            
            try:
                return eval(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis hget操作失败: {str(e)}")
            return default

    def hgetall(self, name):
        """获取哈希表所有字段"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            data = conn.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = eval(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis hgetall操作失败: {str(e)}")
            return {}

    def hdel(self, name, key):
        """删除哈希表字段"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return False
            return bool(conn.hdel(name, key))
        except Exception as e:
            logger.error(f"Redis hdel操作失败: {str(e)}")
            return False

    # ========== 列表操作 ==========

    def lpush(self, name, *values):
        """将值推入列表左侧"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return 0
            
            serial_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serial_values.append(str(value))
                else:
                    serial_values.append(value)
            
            return conn.lpush(name, *serial_values)
        except Exception as e:
            logger.error(f"Redis lpush操作失败: {str(e)}")
            return 0

    def rpush(self, name, *values):
        """将值推入列表右侧"""
        try:
            conn = self.get_master_connection()
            if not conn:
                return 0
            
            serial_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serial_values.append(str(value))
                else:
                    serial_values.append(value)
            
            return conn.rpush(name, *serial_values)
        except Exception as e:
            logger.error(f"Redis rpush操作失败: {str(e)}")
            return 0

    def lrange(self, name, start, end):
        """获取列表指定范围的元素"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            values = conn.lrange(name, start, end)
            result = []
            for value in values:
                try:
                    result.append(eval(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
            return result
        except Exception as e:
            logger.error(f"Redis lrange操作失败: {str(e)}")
            return []

    def llen(self, name):
        """获取列表长度"""
        try:
            conn = self.get_connection()
            if not conn:
                return 0
            return conn.llen(name)
        except Exception as e:
            logger.error(f"Redis llen操作失败: {str(e)}")
            return 0

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

    def promote_slave(self, slave_address):
        """手动提升从节点为主节点（需要哨兵权限）"""
        if self.connection_mode != 'sentinel':
            return {'success': False, 'error': '当前不是哨兵模式'}
        
        try:
            logger.info(f"尝试提升从节点: {slave_address}")
            
            # 通过哨兵执行故障转移
            for sentinel_node in self.sentinel_config['nodes']:
                try:
                    sentinel_conn = redis.Redis(
                        host=sentinel_node[0],
                        port=sentinel_node[1],
                        password=self.sentinel_config['password'],
                        socket_timeout=2.0
                    )
                    
                    # 发送故障转移命令
                    result = sentinel_conn.sentinel('failover', self.sentinel_config['master_name'])
                    sentinel_conn.close()
                    
                    logger.info(f"哨兵 {sentinel_node} 故障转移结果: {result}")
                    return {'success': True, 'message': '故障转移已触发'}
                    
                except Exception as e:
                    logger.error(f"哨兵 {sentinel_node} 故障转移失败: {str(e)}")
            
            return {'success': False, 'error': '所有哨兵节点都无法响应'}
            
        except Exception as e:
            logger.error(f"提升从节点失败: {str(e)}")
            return {'success': False, 'error': str(e)}

# 创建Redis管理器实例
redis_manager = RedisManager()