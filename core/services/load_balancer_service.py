#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS负载均衡服务
提供流量分发和健康路由功能
"""

import os
import sys
import json
import time
import random
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print


class BackendServer:
    """后端服务器"""

    def __init__(self, server_id: str, name: str, host: str, port: int,
                 protocol: str = 'http', weight: int = 1,
                 max_connections: int = 100, enabled: bool = True):
        self.server_id = server_id
        self.name = name
        self.host = host
        self.port = port
        self.protocol = protocol
        self.weight = weight
        self.max_connections = max_connections
        self.enabled = enabled
        self.current_connections = 0
        self.status = 'down'
        self.health_check_url = ''
        self.last_health_check = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.total_requests = 0
        self.total_errors = 0
        self.avg_response_time = 0
        self.registered_at = datetime.now().isoformat()

    @property
    def address(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'server_id': self.server_id,
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'address': self.address,
            'weight': self.weight,
            'max_connections': self.max_connections,
            'current_connections': self.current_connections,
            'enabled': self.enabled,
            'status': self.status,
            'last_health_check': self.last_health_check,
            'consecutive_failures': self.consecutive_failures,
            'consecutive_successes': self.consecutive_successes,
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'avg_response_time': round(self.avg_response_time, 3),
            'registered_at': self.registered_at
        }


class LoadBalancerService:
    """负载均衡服务"""

    STRATEGIES = ['round_robin', 'weighted_round_robin', 'least_connections',
                  'random', 'weighted_random', 'ip_hash']

    def __init__(self):
        self.servers: Dict[str, BackendServer] = {}
        self.pools: Dict[str, List[str]] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.health_thread = None

        self.default_strategy = 'weighted_round_robin'
        self._round_robin_index: Dict[str, int] = {}
        self._ip_hash_map: Dict[str, str] = {}

        self._init_database()
        self._register_default_servers()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lb_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    protocol TEXT DEFAULT 'http',
                    weight INTEGER DEFAULT 1,
                    max_connections INTEGER DEFAULT 100,
                    enabled INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'down',
                    health_check_url TEXT,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lb_pools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_name TEXT NOT NULL,
                    server_id TEXT NOT NULL,
                    strategy TEXT DEFAULT 'weighted_round_robin',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lb_request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_name TEXT,
                    server_id TEXT,
                    server_name TEXT,
                    client_ip TEXT,
                    response_time REAL,
                    status_code INTEGER,
                    success INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_lb_servers_id ON lb_servers(server_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_lb_pools_name ON lb_pools(pool_name)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[负载] 初始化数据库失败: {e}")

    def _register_default_servers(self):
        """注册默认后端服务器"""
        defaults = [
            BackendServer('srv_1', '主服务器-1', '127.0.0.1', 5000, weight=3),
            BackendServer('srv_2', '主服务器-2', '127.0.0.1', 5001, weight=2),
            BackendServer('srv_3', '主服务器-3', '127.0.0.1', 5002, weight=1),
            BackendServer('srv_auth_1', '认证服务-1', '127.0.0.1', 5010, weight=1),
            BackendServer('srv_auth_2', '认证服务-2', '127.0.0.1', 5011, weight=1),
            BackendServer('srv_api_1', 'API服务-1', '127.0.0.1', 5020, weight=2),
            BackendServer('srv_api_2', 'API服务-2', '127.0.0.1', 5021, weight=2),
        ]

        for srv in defaults:
            if srv.server_id not in self.servers:
                srv.status = 'up'
                self.servers[srv.server_id] = srv
                self._save_server_to_db(srv)

        self.pools['main'] = ['srv_1', 'srv_2', 'srv_3']
        self.pools['auth'] = ['srv_auth_1', 'srv_auth_2']
        self.pools['api'] = ['srv_api_1', 'srv_api_2']

    def _save_server_to_db(self, server: BackendServer):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO lb_servers
                (server_id, name, host, port, protocol, weight, max_connections,
                 enabled, status, health_check_url, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                server.server_id, server.name, server.host, server.port,
                server.protocol, server.weight, server.max_connections,
                1 if server.enabled else 0, server.status,
                server.health_check_url, server.registered_at
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[负载] 保存服务器失败: {e}")

    def add_server(self, name: str, host: str, port: int, protocol: str = 'http',
                   weight: int = 1, max_connections: int = 100) -> str:
        """添加后端服务器"""
        import uuid
        server_id = f"srv_{uuid.uuid4().hex[:8]}"

        server = BackendServer(
            server_id=server_id,
            name=name,
            host=host,
            port=port,
            protocol=protocol,
            weight=weight,
            max_connections=max_connections
        )
        server.status = 'up'

        with self.lock:
            self.servers[server_id] = server

        self._save_server_to_db(server)
        logger(f"[负载] 添加服务器: {name} @ {host}:{port}")

        return server_id

    def remove_server(self, server_id: str) -> bool:
        """移除后端服务器"""
        with self.lock:
            if server_id not in self.servers:
                return False
            del self.servers[server_id]

            for pool_name, server_ids in self.pools.items():
                if server_id in server_ids:
                    server_ids.remove(server_id)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM lb_servers WHERE server_id = ?', (server_id,))
            cursor.execute('DELETE FROM lb_pools WHERE server_id = ?', (server_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[负载] 移除服务器失败: {e}")

        return True

    def create_pool(self, pool_name: str, server_ids: List[str],
                    strategy: str = 'weighted_round_robin'):
        """创建服务器池"""
        with self.lock:
            self.pools[pool_name] = server_ids
            self._round_robin_index[pool_name] = 0

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            for sid in server_ids:
                cursor.execute('''
                    INSERT INTO lb_pools (pool_name, server_id, strategy)
                    VALUES (?, ?, ?)
                ''', (pool_name, sid, strategy))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[负载] 创建池失败: {e}")

        logger(f"[负载] 创建池: {pool_name} ({len(server_ids)} 台服务器)")

    def get_server(self, pool_name: str = 'main',
                   strategy: str = None,
                   client_ip: str = None) -> Optional[BackendServer]:
        """获取服务器（负载均衡选择）"""
        strategy = strategy or self.default_strategy

        with self.lock:
            server_ids = self.pools.get(pool_name, [])

            available = [
                self.servers[sid] for sid in server_ids
                if sid in self.servers and
                self.servers[sid].enabled and
                self.servers[sid].status == 'up' and
                self.servers[sid].current_connections < self.servers[sid].max_connections
            ]

            if not available:
                return None

            if strategy == 'round_robin':
                return self._round_robin(pool_name, available)
            elif strategy == 'weighted_round_robin':
                return self._weighted_round_robin(pool_name, available)
            elif strategy == 'least_connections':
                return self._least_connections(available)
            elif strategy == 'random':
                return random.choice(available)
            elif strategy == 'weighted_random':
                return self._weighted_random(available)
            elif strategy == 'ip_hash':
                return self._ip_hash(pool_name, available, client_ip or '')
            else:
                return self._weighted_round_robin(pool_name, available)

    def _round_robin(self, pool_name: str, servers: List[BackendServer]) -> BackendServer:
        """轮询"""
        idx = self._round_robin_index.get(pool_name, 0) % len(servers)
        self._round_robin_index[pool_name] = idx + 1
        return servers[idx]

    def _weighted_round_robin(self, pool_name: str,
                              servers: List[BackendServer]) -> BackendServer:
        """加权轮询"""
        total_weight = sum(s.weight for s in servers)
        r = random.randint(1, total_weight)

        for server in servers:
            r -= server.weight
            if r <= 0:
                return server

        return servers[0]

    def _least_connections(self, servers: List[BackendServer]) -> BackendServer:
        """最少连接"""
        return min(servers, key=lambda s: s.current_connections)

    def _weighted_random(self, servers: List[BackendServer]) -> BackendServer:
        """加权随机"""
        total_weight = sum(s.weight for s in servers)
        r = random.randint(1, total_weight)

        for server in servers:
            r -= server.weight
            if r <= 0:
                return server

        return random.choice(servers)

    def _ip_hash(self, pool_name: str, servers: List[BackendServer],
                 client_ip: str) -> BackendServer:
        """IP哈希"""
        if client_ip in self._ip_hash_map:
            server_id = self._ip_hash_map[client_ip]
            for s in servers:
                if s.server_id == server_id:
                    return s

        import hashlib
        hash_val = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        selected = servers[hash_val % len(servers)]

        self._ip_hash_map[client_ip] = selected.server_id

        return selected

    def record_request(self, server_id: str, response_time: float,
                       status_code: int, success: bool, client_ip: str = ''):
        """记录请求"""
        with self.lock:
            server = self.servers.get(server_id)
            if server:
                server.total_requests += 1
                if not success:
                    server.total_errors += 1

                if server.avg_response_time == 0:
                    server.avg_response_time = response_time
                else:
                    server.avg_response_time = (
                        server.avg_response_time * 0.9 + response_time * 0.1
                    )

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO lb_request_logs
                (server_id, server_name, client_ip, response_time, status_code, success)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                server_id,
                self.servers[server_id].name if server_id in self.servers else '',
                client_ip, response_time, status_code, 1 if success else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[负载] 记录请求失败: {e}")

    def acquire_connection(self, server_id: str) -> bool:
        """获取连接"""
        with self.lock:
            server = self.servers.get(server_id)
            if not server or not server.enabled or server.status != 'up':
                return False
            if server.current_connections >= server.max_connections:
                return False
            server.current_connections += 1
            return True

    def release_connection(self, server_id: str):
        """释放连接"""
        with self.lock:
            server = self.servers.get(server_id)
            if server and server.current_connections > 0:
                server.current_connections -= 1

    def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            try:
                time.sleep(30)

                with self.lock:
                    servers = list(self.servers.values())

                for server in servers:
                    if not server.enabled:
                        continue

                    is_healthy = self._check_server_health(server)
                    server.last_health_check = datetime.now().isoformat()

                    if is_healthy:
                        server.consecutive_successes += 1
                        server.consecutive_failures = 0

                        if server.status == 'down' and server.consecutive_successes >= 2:
                            server.status = 'up'
                            logger(f"[负载] 服务器恢复: {server.name}")
                    else:
                        server.consecutive_failures += 1
                        server.consecutive_successes = 0

                        if server.status == 'up' and server.consecutive_failures >= 3:
                            server.status = 'down'
                            logger(f"[负载] 服务器下线: {server.name}")

            except Exception as e:
                logger(f"[负载] 健康检查错误: {e}")

    def _check_server_health(self, server: BackendServer) -> bool:
        """检查服务器健康"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((server.host, server.port))
            sock.close()
            return result == 0
        except:
            return False

    def get_servers(self, pool_name: str = None) -> List[BackendServer]:
        with self.lock:
            if pool_name:
                server_ids = self.pools.get(pool_name, [])
                return [self.servers[sid] for sid in server_ids if sid in self.servers]
            return list(self.servers.values())

    def get_pools(self) -> Dict[str, List[str]]:
        return dict(self.pools)

    def get_request_stats(self, pool_name: str = None, hours: int = 24) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor.execute('''
                SELECT server_name, COUNT(*) as total,
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors,
                       AVG(response_time) as avg_time
                FROM lb_request_logs
                WHERE created_at >= ?
                GROUP BY server_name
            ''', (since,))

            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'total_requests': row[1],
                    'errors': row[2],
                    'avg_response_time': round(row[3] or 0, 3),
                    'error_rate': round((row[2] or 0) / max(1, row[1]) * 100, 2)
                }

            conn.close()
            return stats
        except Exception as e:
            logger(f"[负载] 获取统计失败: {e}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            up_count = sum(1 for s in self.servers.values() if s.status == 'up')
            down_count = sum(1 for s in self.servers.values() if s.status == 'down')
            total_connections = sum(s.current_connections for s in self.servers.values())

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_servers': len(self.servers),
                'up_servers': up_count,
                'down_servers': down_count,
                'total_pools': len(self.pools),
                'total_connections': total_connections,
                'default_strategy': self.default_strategy
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_thread.start()
        logger(f"[负载] 负载均衡服务已启动")

    def stop(self):
        self.is_running = False
        if self.health_thread:
            self.health_thread.join()
        logger(f"[负载] 负载均衡服务已停止")


load_balancer_service = LoadBalancerService()
