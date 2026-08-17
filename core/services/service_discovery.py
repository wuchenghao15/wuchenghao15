#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS服务发现服务
提供微服务注册与发现功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print


class ServiceInstance:
    """服务实例"""

    def __init__(self, service_id: str, name: str, host: str, port: int,
                 protocol: str = 'http', version: str = '1.0.0',
                 metadata: Dict[str, Any] = None, health_check_url: str = '',
                 status: str = 'up', weight: int = 1):
        self.service_id = service_id
        self.name = name
        self.host = host
        self.port = port
        self.protocol = protocol
        self.version = version
        self.metadata = metadata or {}
        self.health_check_url = health_check_url
        self.status = status
        self.weight = weight
        self.registered_at = datetime.now().isoformat()
        self.last_heartbeat = datetime.now().isoformat()
        self.heartbeat_count = 0

    @property
    def address(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_id': self.service_id,
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'version': self.version,
            'address': self.address,
            'metadata': self.metadata,
            'health_check_url': self.health_check_url,
            'status': self.status,
            'weight': self.weight,
            'registered_at': self.registered_at,
            'last_heartbeat': self.last_heartbeat,
            'heartbeat_count': self.heartbeat_count
        }


class ServiceDiscovery:
    """服务发现服务"""

    def __init__(self):
        self.services: Dict[str, ServiceInstance] = {}
        self.is_running = False
        self.heartbeat_thread = None
        self.lock = threading.Lock()

        self.heartbeat_timeout = 30
        self.cleanup_interval = 10

        self._init_database()
        self._register_default_services()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    protocol TEXT DEFAULT 'http',
                    version TEXT DEFAULT '1.0.0',
                    metadata TEXT,
                    health_check_url TEXT,
                    status TEXT DEFAULT 'up',
                    weight INTEGER DEFAULT 1,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_heartbeat TEXT,
                    heartbeat_count INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_heartbeat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id TEXT NOT NULL,
                    status TEXT,
                    checked_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_service_instances_id ON service_instances(service_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_service_instances_name ON service_instances(name)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[发现] 初始化数据库失败: {e}")

    def _register_default_services(self):
        """注册默认服务"""
        defaults = [
            ServiceInstance('svc_main', 'MTSCOS主服务', '127.0.0.1', 5000,
                          version='10.0.0', health_check_url='/api/health'),
            ServiceInstance('svc_auth', '认证服务', '127.0.0.1', 5001,
                          version='1.0.0', health_check_url='/api/auth/health',
                          metadata={'type': 'security'}),
            ServiceInstance('svc_monitor', '监控服务', '127.0.0.1', 5002,
                          version='1.0.0', health_check_url='/api/monitor/health',
                          metadata={'type': 'monitoring'}),
            ServiceInstance('svc_search', '搜索服务', '127.0.0.1', 5003,
                          version='1.0.0', health_check_url='/api/search/health',
                          metadata={'type': 'search'}),
            ServiceInstance('svc_cache', '缓存服务', '127.0.0.1', 6379,
                          protocol='redis', version='1.0.0',
                          metadata={'type': 'cache'})
        ]

        for svc in defaults:
            if svc.service_id not in self.services:
                self.services[svc.service_id] = svc
                self._save_service_to_db(svc)

    def _generate_service_id(self) -> str:
        import uuid
        return f"svc_{uuid.uuid4().hex[:12]}"

    def register(self, name: str, host: str, port: int, protocol: str = 'http',
                 version: str = '1.0.0', metadata: Dict[str, Any] = None,
                 health_check_url: str = '', weight: int = 1) -> str:
        service_id = self._generate_service_id()

        instance = ServiceInstance(
            service_id=service_id,
            name=name,
            host=host,
            port=port,
            protocol=protocol,
            version=version,
            metadata=metadata or {},
            health_check_url=health_check_url,
            weight=weight
        )

        with self.lock:
            self.services[service_id] = instance

        self._save_service_to_db(instance)
        logger(f"[发现] 注册服务: {name} @ {host}:{port}")

        return service_id

    def _save_service_to_db(self, instance: ServiceInstance):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO service_instances
                (service_id, name, host, port, protocol, version, metadata,
                 health_check_url, status, weight, registered_at, last_heartbeat, heartbeat_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                instance.service_id, instance.name, instance.host, instance.port,
                instance.protocol, instance.version,
                json.dumps(instance.metadata),
                instance.health_check_url, instance.status, instance.weight,
                instance.registered_at, instance.last_heartbeat,
                instance.heartbeat_count
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[发现] 保存服务失败: {e}")

    def deregister(self, service_id: str) -> bool:
        with self.lock:
            if service_id not in self.services:
                return False
            del self.services[service_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM service_instances WHERE service_id = ?', (service_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[发现] 注销服务失败: {e}")

        logger(f"[发现] 注销服务: {service_id}")
        return True

    def heartbeat(self, service_id: str) -> bool:
        """服务心跳"""
        with self.lock:
            instance = self.services.get(service_id)
            if not instance:
                return False

            instance.last_heartbeat = datetime.now().isoformat()
            instance.heartbeat_count += 1
            instance.status = 'up'

        self._update_heartbeat_in_db(service_id, instance.last_heartbeat,
                                     instance.heartbeat_count, instance.status)
        self._log_heartbeat(service_id, 'up')

        return True

    def _update_heartbeat_in_db(self, service_id: str, last_heartbeat: str,
                                heartbeat_count: int, status: str):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE service_instances
                SET last_heartbeat = ?, heartbeat_count = ?, status = ?
                WHERE service_id = ?
            ''', (last_heartbeat, heartbeat_count, status, service_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[发现] 更新心跳失败: {e}")

    def _log_heartbeat(self, service_id: str, status: str):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO service_heartbeat_logs (service_id, status)
                VALUES (?, ?)
            ''', (service_id, status))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[发现] 记录心跳失败: {e}")

    def discover(self, name: str = None, version: str = None,
                 status: str = 'up') -> List[ServiceInstance]:
        """发现服务"""
        with self.lock:
            results = []

            for instance in self.services.values():
                if status and instance.status != status:
                    continue
                if name and instance.name != name:
                    continue
                if version and instance.version != version:
                    continue

                results.append(instance)

            return results

    def get_instance(self, service_id: str) -> Optional[ServiceInstance]:
        return self.services.get(service_id)

    def get_service_address(self, name: str) -> Optional[str]:
        """获取服务地址（负载均衡）"""
        instances = self.discover(name=name, status='up')

        if not instances:
            return None

        import random
        total_weight = sum(i.weight for i in instances)
        r = random.randint(1, total_weight)

        for instance in instances:
            r -= instance.weight
            if r <= 0:
                return instance.address

        return instances[0].address

    def get_all_services(self) -> List[ServiceInstance]:
        with self.lock:
            return list(self.services.values())

    def _cleanup_loop(self):
        """清理循环 - 标记超时服务"""
        while self.is_running:
            time.sleep(self.cleanup_interval)

            now = datetime.now()

            with self.lock:
                for instance in self.services.values():
                    if instance.status == 'up':
                        try:
                            last_hb = datetime.fromisoformat(instance.last_heartbeat)
                            if (now - last_hb).total_seconds() > self.heartbeat_timeout:
                                instance.status = 'down'
                                self._update_heartbeat_in_db(
                                    instance.service_id,
                                    instance.last_heartbeat,
                                    instance.heartbeat_count,
                                    'down'
                                )
                                logger(f"[发现] 服务心跳超时: {instance.name}")
                        except:
                            pass

    def get_heartbeat_logs(self, service_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM service_heartbeat_logs WHERE 1=1'
            params = []

            if service_id:
                query += ' AND service_id = ?'
                params.append(service_id)

            query += ' ORDER BY checked_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except Exception as e:
            logger(f"[发现] 获取心跳日志失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            up_count = sum(1 for s in self.services.values() if s.status == 'up')
            down_count = sum(1 for s in self.services.values() if s.status == 'down')

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_services': len(self.services),
                'up_services': up_count,
                'down_services': down_count,
                'heartbeat_timeout': self.heartbeat_timeout
            }

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        self.heartbeat_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.heartbeat_thread.start()
        logger(f"[发现] 服务发现服务已启动")

    def stop(self):
        self.is_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        logger(f"[发现] 服务发现服务已停止")


service_discovery = ServiceDiscovery()
