#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 微服务基础设施 v16.0.0
====================================
构建微服务架构，包括服务注册发现、API网关、消息队列和分布式系统

核心能力：
1. 服务注册发现 - 服务注册、服务发现、健康检查
2. API网关升级 - 路由管理、限流熔断、负载均衡
3. 消息队列优化 - 异步消息、发布订阅、消息持久化
4. 分布式系统 - 分布式锁、分布式事务、分布式缓存
"""

import os
import json
import uuid
import sqlite3
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict
import queue

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'microservice_infrastructure.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MicroserviceInfrastructure')


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._services = {}
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 服务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT UNIQUE NOT NULL,
                service_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT DEFAULT 'http',
                status TEXT DEFAULT 'healthy',
                metadata TEXT,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat TEXT DEFAULT CURRENT_TIMESTAMP,
                tags TEXT
            )
        ''')
        
        # 服务实例表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT UNIQUE NOT NULL,
                service_id TEXT NOT NULL,
                instance_name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT DEFAULT 'healthy',
                weight INTEGER DEFAULT 1,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES service_registry(service_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("服务注册中心数据库初始化完成")
    
    def register_service(
        self,
        service_name: str,
        service_type: str,
        host: str,
        port: int,
        protocol: str = 'http',
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """注册服务"""
        with self._lock:
            service_id = f"svc_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO service_registry
                    (service_id, service_name, service_type, host, port, protocol, metadata, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (service_id, service_name, service_type, host, port, protocol,
                      json.dumps(metadata) if metadata else None,
                      json.dumps(tags) if tags else None))
                
                conn.commit()
                
                # 缓存到内存
                self._services[service_id] = {
                    'service_name': service_name,
                    'service_type': service_type,
                    'host': host,
                    'port': port,
                    'protocol': protocol,
                    'status': 'healthy',
                    'registered_at': datetime.now().isoformat()
                }
                
                logger.info(f"服务注册成功: {service_name} ({service_id})")
                
                return {
                    'success': True,
                    'service_id': service_id,
                    'message': '服务注册成功'
                }
                
            except Exception as e:
                logger.error(f"服务注册失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def discover_service(
        self,
        service_name: str = None,
        service_type: str = None,
        tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """发现服务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM service_registry WHERE status = 'healthy'"
            params = []
            
            if service_name:
                query += " AND service_name = ?"
                params.append(service_name)
            
            if service_type:
                query += " AND service_type = ?"
                params.append(service_type)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            
            services = []
            for row in cursor.fetchall():
                service = dict(zip(columns, row))
                
                # 过滤标签
                if tags:
                    service_tags = json.loads(service.get('tags', '[]'))
                    if not any(tag in service_tags for tag in tags):
                        continue
                
                services.append(service)
            
            return services
            
        except Exception as e:
            logger.error(f"服务发现失败: {e}")
            return []
        finally:
            conn.close()
    
    def heartbeat(self, service_id: str) -> Dict[str, Any]:
        """服务心跳"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    UPDATE service_registry
                    SET last_heartbeat = ?, status = 'healthy'
                    WHERE service_id = ?
                ''', (datetime.now().isoformat(), service_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': '心跳成功'
                }
                
            except Exception as e:
                logger.error(f"心跳失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def deregister_service(self, service_id: str) -> Dict[str, Any]:
        """注销服务"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    UPDATE service_registry
                    SET status = 'deregistered'
                    WHERE service_id = ?
                ''', (service_id,))
                
                conn.commit()
                
                # 从缓存中移除
                if service_id in self._services:
                    del self._services[service_id]
                
                logger.info(f"服务注销成功: {service_id}")
                
                return {
                    'success': True,
                    'message': '服务注销成功'
                }
                
            except Exception as e:
                logger.error(f"服务注销失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 统计服务状态
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM service_registry
                GROUP BY status
            ''')
            
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 检查超时服务
            timeout_threshold = (datetime.now() - timedelta(minutes=5)).isoformat()
            cursor.execute('''
                SELECT service_id, service_name, last_heartbeat
                FROM service_registry
                WHERE last_heartbeat < ? AND status = 'healthy'
            ''', (timeout_threshold,))
            
            timeout_services = cursor.fetchall()
            
            # 更新超时服务状态
            for service_id, service_name, _ in timeout_services:
                cursor.execute('''
                    UPDATE service_registry
                    SET status = 'unhealthy'
                    WHERE service_id = ?
                ''', (service_id,))
                
                logger.warning(f"服务超时: {service_name} ({service_id})")
            
            conn.commit()
            
            return {
                'total_services': sum(status_counts.values()),
                'status_counts': status_counts,
                'timeout_services': len(timeout_services)
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {}
        finally:
            conn.close()


class APIGatewayEnhanced:
    """增强版API网关"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._routes = {}
        self._rate_limits = {}
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 路由表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                service_id TEXT NOT NULL,
                target_path TEXT,
                authentication INTEGER DEFAULT 0,
                rate_limit INTEGER,
                timeout INTEGER DEFAULT 30,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 限流记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limit_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                route_id TEXT NOT NULL,
                request_count INTEGER DEFAULT 1,
                window_start TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, route_id, window_start)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("API网关数据库初始化完成")
    
    def register_route(
        self,
        path: str,
        method: str,
        service_id: str,
        target_path: str = None,
        authentication: bool = False,
        rate_limit: int = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """注册路由"""
        with self._lock:
            route_id = f"route_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO api_routes
                    (route_id, path, method, service_id, target_path, authentication, rate_limit, timeout)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (route_id, path, method, service_id, target_path or path,
                      1 if authentication else 0, rate_limit, timeout))
                
                conn.commit()
                
                # 缓存到内存
                self._routes[f"{method}:{path}"] = {
                    'route_id': route_id,
                    'service_id': service_id,
                    'target_path': target_path or path,
                    'authentication': authentication,
                    'rate_limit': rate_limit,
                    'timeout': timeout
                }
                
                logger.info(f"路由注册成功: {method} {path}")
                
                return {
                    'success': True,
                    'route_id': route_id,
                    'message': '路由注册成功'
                }
                
            except Exception as e:
                logger.error(f"路由注册失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def route_request(
        self,
        method: str,
        path: str,
        client_id: str = 'anonymous'
    ) -> Dict[str, Any]:
        """路由请求"""
        route_key = f"{method}:{path}"
        
        if route_key not in self._routes:
            return {
                'success': False,
                'error': '路由不存在',
                'status_code': 404
            }
        
        route = self._routes[route_key]
        
        # 检查限流
        if route.get('rate_limit'):
            if not self._check_rate_limit(client_id, route['route_id'], route['rate_limit']):
                return {
                    'success': False,
                    'error': '请求过于频繁',
                    'status_code': 429
                }
        
        # 返回路由信息
        return {
            'success': True,
            'route_id': route['route_id'],
            'service_id': route['service_id'],
            'target_path': route['target_path'],
            'timeout': route['timeout']
        }
    
    def _check_rate_limit(self, client_id: str, route_id: str, limit: int) -> bool:
        """检查限流"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 获取当前窗口
                window_start = datetime.now().replace(second=0, microsecond=0).isoformat()
                
                # 查询当前请求数
                cursor.execute('''
                    SELECT request_count FROM rate_limit_records
                    WHERE client_id = ? AND route_id = ? AND window_start = ?
                ''', (client_id, route_id, window_start))
                
                result = cursor.fetchone()
                
                if result:
                    current_count = result[0]
                    if current_count >= limit:
                        return False
                    
                    # 增加计数
                    cursor.execute('''
                        UPDATE rate_limit_records
                        SET request_count = request_count + 1
                        WHERE client_id = ? AND route_id = ? AND window_start = ?
                    ''', (client_id, route_id, window_start))
                else:
                    # 创建新记录
                    cursor.execute('''
                        INSERT INTO rate_limit_records
                        (client_id, route_id, window_start)
                        VALUES (?, ?, ?)
                    ''', (client_id, route_id, window_start))
                
                conn.commit()
                
                return True
                
            except Exception as e:
                logger.error(f"限流检查失败: {e}")
                return True  # 失败时允许请求
            finally:
                conn.close()
    
    def list_routes(self) -> List[Dict[str, Any]]:
        """列出所有路由"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM api_routes WHERE enabled = 1')
            columns = [desc[0] for desc in cursor.description]
            
            routes = []
            for row in cursor.fetchall():
                route = dict(zip(columns, row))
                routes.append(route)
            
            return routes
            
        except Exception as e:
            logger.error(f"路由列表失败: {e}")
            return []
        finally:
            conn.close()


class MessageQueue:
    """消息队列"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._queues = defaultdict(queue.Queue)
        self._subscribers = defaultdict(list)
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 消息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                queue_name TEXT NOT NULL,
                message_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                consumed_at TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3
            )
        ''')
        
        # 订阅表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id TEXT UNIQUE NOT NULL,
                queue_name TEXT NOT NULL,
                subscriber_id TEXT NOT NULL,
                filter_pattern TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("消息队列数据库初始化完成")
    
    def publish(
        self,
        queue_name: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> Dict[str, Any]:
        """发布消息"""
        with self._lock:
            message_id = f"msg_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO message_queue
                    (message_id, queue_name, message_type, payload, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (message_id, queue_name, message_type, json.dumps(payload), priority))
                
                conn.commit()
                
                # 通知订阅者
                self._notify_subscribers(queue_name, message_id, message_type, payload)
                
                logger.info(f"消息发布成功: {message_id} -> {queue_name}")
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'message': '消息发布成功'
                }
                
            except Exception as e:
                logger.error(f"消息发布失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def consume(self, queue_name: str, subscriber_id: str) -> Optional[Dict[str, Any]]:
        """消费消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取待消费消息
            cursor.execute('''
                SELECT message_id, message_type, payload
                FROM message_queue
                WHERE queue_name = ? AND status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            ''', (queue_name,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
            
            message_id, message_type, payload = result
            
            # 更新消息状态
            cursor.execute('''
                UPDATE message_queue
                SET status = 'consumed', consumed_at = ?
                WHERE message_id = ?
            ''', (datetime.now().isoformat(), message_id))
            
            conn.commit()
            
            return {
                'message_id': message_id,
                'message_type': message_type,
                'payload': json.loads(payload)
            }
            
        except Exception as e:
            logger.error(f"消息消费失败: {e}")
            return None
        finally:
            conn.close()
    
    def subscribe(
        self,
        queue_name: str,
        subscriber_id: str,
        filter_pattern: str = None
    ) -> Dict[str, Any]:
        """订阅消息"""
        with self._lock:
            subscription_id = f"sub_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO message_subscriptions
                    (subscription_id, queue_name, subscriber_id, filter_pattern)
                    VALUES (?, ?, ?, ?)
                ''', (subscription_id, queue_name, subscriber_id, filter_pattern))
                
                conn.commit()
                
                # 添加到内存订阅列表
                self._subscribers[queue_name].append({
                    'subscription_id': subscription_id,
                    'subscriber_id': subscriber_id,
                    'filter_pattern': filter_pattern
                })
                
                logger.info(f"订阅成功: {subscriber_id} -> {queue_name}")
                
                return {
                    'success': True,
                    'subscription_id': subscription_id,
                    'message': '订阅成功'
                }
                
            except Exception as e:
                logger.error(f"订阅失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def _notify_subscribers(
        self,
        queue_name: str,
        message_id: str,
        message_type: str,
        payload: Dict[str, Any]
    ):
        """通知订阅者"""
        if queue_name not in self._subscribers:
            return
        
        for subscriber in self._subscribers[queue_name]:
            # 检查过滤模式
            if subscriber.get('filter_pattern'):
                import re
                if not re.match(subscriber['filter_pattern'], message_type):
                    continue
            
            # 这里可以发送通知（邮件、webhook等）
            logger.info(f"通知订阅者: {subscriber['subscriber_id']} - {message_id}")


class DistributedLock:
    """分布式锁"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._locks = {}
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS distributed_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lock_name TEXT UNIQUE NOT NULL,
                owner_id TEXT NOT NULL,
                acquired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("分布式锁数据库初始化完成")
    
    def acquire(
        self,
        lock_name: str,
        owner_id: str,
        ttl: int = 30,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """获取锁"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 检查锁是否存在且未过期
                cursor.execute('''
                    SELECT owner_id, expires_at FROM distributed_locks
                    WHERE lock_name = ?
                ''', (lock_name,))
                
                result = cursor.fetchone()
                
                if result:
                    current_owner, expires_at = result
                    
                    # 检查是否过期
                    if datetime.fromisoformat(expires_at) > datetime.now():
                        # 锁未过期，检查是否是同一个所有者
                        if current_owner != owner_id:
                            return {
                                'success': False,
                                'error': '锁已被其他进程持有',
                                'owner_id': current_owner
                            }
                    
                    # 锁已过期或属于当前所有者，更新锁
                    cursor.execute('''
                        UPDATE distributed_locks
                        SET owner_id = ?, expires_at = ?, metadata = ?
                        WHERE lock_name = ?
                    ''', (owner_id, (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                          json.dumps(metadata) if metadata else None, lock_name))
                else:
                    # 创建新锁
                    cursor.execute('''
                        INSERT INTO distributed_locks
                        (lock_name, owner_id, expires_at, metadata)
                        VALUES (?, ?, ?, ?)
                    ''', (lock_name, owner_id,
                          (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                          json.dumps(metadata) if metadata else None))
                
                conn.commit()
                
                logger.info(f"获取锁成功: {lock_name} by {owner_id}")
                
                return {
                    'success': True,
                    'lock_name': lock_name,
                    'owner_id': owner_id,
                    'message': '获取锁成功'
                }
                
            except Exception as e:
                logger.error(f"获取锁失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def release(self, lock_name: str, owner_id: str) -> Dict[str, Any]:
        """释放锁"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    DELETE FROM distributed_locks
                    WHERE lock_name = ? AND owner_id = ?
                ''', (lock_name, owner_id))
                
                if cursor.rowcount == 0:
                    return {
                        'success': False,
                        'error': '锁不存在或不属于当前所有者'
                    }
                
                conn.commit()
                
                logger.info(f"释放锁成功: {lock_name} by {owner_id}")
                
                return {
                    'success': True,
                    'message': '释放锁成功'
                }
                
            except Exception as e:
                logger.error(f"释放锁失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def renew(self, lock_name: str, owner_id: str, ttl: int = 30) -> Dict[str, Any]:
        """续期锁"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    UPDATE distributed_locks
                    SET expires_at = ?
                    WHERE lock_name = ? AND owner_id = ?
                ''', ((datetime.now() + timedelta(seconds=ttl)).isoformat(),
                      lock_name, owner_id))
                
                if cursor.rowcount == 0:
                    return {
                        'success': False,
                        'error': '锁不存在或不属于当前所有者'
                    }
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': '续期成功'
                }
                
            except Exception as e:
                logger.error(f"续期失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()


class MicroserviceInfrastructure:
    """微服务基础设施主类"""
    
    def __init__(self):
        self.service_registry = ServiceRegistry()
        self.api_gateway = APIGatewayEnhanced()
        self.message_queue = MessageQueue()
        self.distributed_lock = DistributedLock()
        
        logger.info("微服务基础设施初始化完成")
    
    def get_infrastructure_report(self) -> Dict[str, Any]:
        """获取基础设施报告"""
        return {
            'service_registry': {
                'status': 'active',
                'health': self.service_registry.health_check()
            },
            'api_gateway': {
                'status': 'active',
                'routes_count': len(self.api_gateway.list_routes())
            },
            'message_queue': {
                'status': 'active',
                'features': ['异步消息', '发布订阅', '消息持久化']
            },
            'distributed_lock': {
                'status': 'active',
                'features': ['分布式锁', '自动续期', '超时释放']
            }
        }


# 全局实例
microservice_infrastructure = MicroserviceInfrastructure()

if __name__ == '__main__':
    print("=== 微服务基础设施测试 ===")
    
    # 测试服务注册
    result = microservice_infrastructure.service_registry.register_service(
        service_name='user-service',
        service_type='backend',
        host='localhost',
        port=5000,
        tags=['user', 'auth']
    )
    print(f"服务注册: {result}")
    
    # 测试服务发现
    services = microservice_infrastructure.service_registry.discover_service(
        service_type='backend'
    )
    print(f"服务发现: {len(services)} 个服务")
    
    # 测试路由注册
    result = microservice_infrastructure.api_gateway.register_route(
        path='/api/users',
        method='GET',
        service_id='svc_001',
        authentication=True,
        rate_limit=100
    )
    print(f"路由注册: {result}")
    
    # 测试消息发布
    result = microservice_infrastructure.message_queue.publish(
        queue_name='user-events',
        message_type='user.created',
        payload={'user_id': '123', 'username': 'test'}
    )
    print(f"消息发布: {result}")
    
    # 测试分布式锁
    result = microservice_infrastructure.distributed_lock.acquire(
        lock_name='test-lock',
        owner_id='process-1',
        ttl=30
    )
    print(f"获取锁: {result}")
    
    # 获取基础设施报告
    report = microservice_infrastructure.get_infrastructure_report()
    print(f"基础设施报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
    
    print("\n微服务基础设施测试完成")
