#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS服务网格代理
提供服务间通信的流量控制、重试、熔断和负载均衡
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict

logger = print


class RetryPolicy:
    """重试策略"""

    def __init__(self, max_retries: int = 3, initial_delay: float = 0.1,
                 max_delay: float = 1.0, backoff_multiplier: float = 2.0,
                 retryable_status: List[int] = None):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.retryable_status = retryable_status or [502, 503, 504]

    def get_delay(self, attempt: int) -> float:
        """获取重试延迟"""
        delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int, status_code: int = None,
                     error: str = None) -> bool:
        """是否应该重试"""
        if attempt >= self.max_retries:
            return False
        if status_code and status_code in self.retryable_status:
            return True
        if error:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_retries': self.max_retries,
            'initial_delay': self.initial_delay,
            'max_delay': self.max_delay,
            'backoff_multiplier': self.backoff_multiplier,
            'retryable_status': self.retryable_status
        }


class CircuitPolicy:
    """熔断策略"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30,
                 half_open_max: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max

    def to_dict(self) -> Dict[str, Any]:
        return {
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'half_open_max': self.half_open_max
        }


class RouteRule:
    """路由规则"""

    def __init__(self, rule_id: str, source: str, destination: str,
                 weight: int = 100, conditions: Dict[str, Any] = None,
                 enabled: bool = True):
        self.rule_id = rule_id
        self.source = source
        self.destination = destination
        self.weight = weight
        self.conditions = conditions or {}
        self.enabled = enabled
        self.request_count = 0
        self.error_count = 0

    def matches(self, context: Dict[str, Any]) -> bool:
        """检查是否匹配"""
        if not self.enabled:
            return False

        for key, value in self.conditions.items():
            if context.get(key) != value:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'source': self.source,
            'destination': self.destination,
            'weight': self.weight,
            'conditions': self.conditions,
            'enabled': self.enabled,
            'request_count': self.request_count,
            'error_count': self.error_count
        }


class ServiceEndpoint:
    """服务端点状态"""

    def __init__(self, endpoint_id: str, service_name: str, address: str):
        self.endpoint_id = endpoint_id
        self.service_name = service_name
        self.address = address
        self.state = 'closed'  # closed, open, half_open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure = None
        self.last_success = None
        self.opened_at = None
        self.half_open_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint_id': self.endpoint_id,
            'service_name': self.service_name,
            'address': self.address,
            'state': self.state,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure': self.last_failure,
            'last_success': self.last_success,
            'opened_at': self.opened_at
        }


class ServiceMeshProxy:
    """服务网格代理"""

    def __init__(self):
        self.endpoints: Dict[str, ServiceEndpoint] = {}
        self.routes: Dict[str, RouteRule] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}
        self.circuit_policies: Dict[str, CircuitPolicy] = {}
        self.is_running = False
        self.lock = threading.Lock()

        self.default_retry = RetryPolicy()
        self.default_circuit = CircuitPolicy()

        self._init_database()
        self._register_defaults()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mesh_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL UNIQUE,
                    service_name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    state TEXT DEFAULT 'closed',
                    failure_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_failure TEXT,
                    last_success TEXT,
                    opened_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mesh_routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    weight INTEGER DEFAULT 100,
                    conditions TEXT,
                    enabled INTEGER DEFAULT 1,
                    request_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mesh_request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    destination TEXT,
                    method TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    attempts INTEGER DEFAULT 1,
                    success INTEGER,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mesh_endpoints_service ON mesh_endpoints(service_name)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mesh_routes_source ON mesh_routes(source)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网格] 初始化数据库失败: {e}")

    def _register_defaults(self):
        """注册默认配置"""
        defaults = [
            ('ep_auth_1', 'auth_service', 'http://127.0.0.1:5010'),
            ('ep_auth_2', 'auth_service', 'http://127.0.0.1:5011'),
            ('ep_api_1', 'api_service', 'http://127.0.0.1:5020'),
            ('ep_api_2', 'api_service', 'http://127.0.0.1:5021'),
            ('ep_data_1', 'data_service', 'http://127.0.0.1:5030'),
        ]

        for eid, svc, addr in defaults:
            if eid not in self.endpoints:
                ep = ServiceEndpoint(eid, svc, addr)
                self.endpoints[eid] = ep
                self._save_endpoint_to_db(ep)

        self.retry_policies['default'] = self.default_retry
        self.circuit_policies['default'] = self.default_circuit

    def _save_endpoint_to_db(self, ep: ServiceEndpoint):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO mesh_endpoints
                (endpoint_id, service_name, address, state, failure_count,
                 success_count, last_failure, last_success, opened_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ep.endpoint_id, ep.service_name, ep.address,
                ep.state, ep.failure_count, ep.success_count,
                ep.last_failure, ep.last_success, ep.opened_at
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网格] 保存端点失败: {e}")

    def add_endpoint(self, service_name: str, address: str) -> str:
        """添加服务端点"""
        import uuid
        endpoint_id = f"ep_{uuid.uuid4().hex[:8]}"

        ep = ServiceEndpoint(endpoint_id, service_name, address)

        with self.lock:
            self.endpoints[endpoint_id] = ep

        self._save_endpoint_to_db(ep)
        logger(f"[网格] 添加端点: {service_name} @ {address}")

        return endpoint_id

    def add_route(self, source: str, destination: str,
                  weight: int = 100, conditions: Dict[str, Any] = None) -> str:
        """添加路由规则"""
        import uuid
        rule_id = f"route_{uuid.uuid4().hex[:8]}"

        route = RouteRule(
            rule_id=rule_id,
            source=source,
            destination=destination,
            weight=weight,
            conditions=conditions or {}
        )

        with self.lock:
            self.routes[rule_id] = route

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO mesh_routes
                (rule_id, source, destination, weight, conditions, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                rule_id, source, destination, weight,
                json.dumps(conditions or {}), 1
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网格] 保存路由失败: {e}")

        return rule_id

    def get_available_endpoints(self, service_name: str) -> List[ServiceEndpoint]:
        """获取可用端点（熔断器关闭或半开）"""
        with self.lock:
            return [
                ep for ep in self.endpoints.values()
                if ep.service_name == service_name and ep.state != 'open'
            ]

    def select_endpoint(self, service_name: str,
                        context: Dict[str, Any] = None) -> Optional[ServiceEndpoint]:
        """选择端点（负载均衡）"""
        available = self.get_available_endpoints(service_name)

        if not available:
            return None

        import random
        return random.choice(available)

    def record_success(self, endpoint_id: str, response_time: float):
        """记录成功"""
        with self.lock:
            ep = self.endpoints.get(endpoint_id)
            if not ep:
                return

            ep.success_count += 1
            ep.last_success = datetime.now().isoformat()

            if ep.state == 'half_open':
                ep.half_open_count += 1
                circuit = self.circuit_policies.get('default', self.default_circuit)

                if ep.half_open_count >= circuit.half_open_max:
                    ep.state = 'closed'
                    ep.failure_count = 0
                    ep.half_open_count = 0
                    logger(f"[网格] 熔断器恢复: {ep.service_name}")

            elif ep.state == 'closed':
                ep.failure_count = max(0, ep.failure_count - 1)

        self._save_endpoint_to_db(ep)

    def record_failure(self, endpoint_id: str, error: str = ''):
        """记录失败"""
        with self.lock:
            ep = self.endpoints.get(endpoint_id)
            if not ep:
                return

            ep.failure_count += 1
            ep.last_failure = datetime.now().isoformat()

            circuit = self.circuit_policies.get('default', self.default_circuit)

            if ep.state == 'closed':
                if ep.failure_count >= circuit.failure_threshold:
                    ep.state = 'open'
                    ep.opened_at = datetime.now().isoformat()
                    logger(f"[网格] 熔断器打开: {ep.service_name}")

            elif ep.state == 'half_open':
                ep.state = 'open'
                ep.opened_at = datetime.now().isoformat()
                ep.half_open_count = 0

        self._save_endpoint_to_db(ep)

    def check_recovery(self, endpoint_id: str):
        """检查是否可以恢复"""
        with self.lock:
            ep = self.endpoints.get(endpoint_id)
            if not ep or ep.state != 'open':
                return

            circuit = self.circuit_policies.get('default', self.default_circuit)

            if ep.opened_at:
                opened_time = datetime.fromisoformat(ep.opened_at)
                if (datetime.now() - opened_time).total_seconds() > circuit.recovery_timeout:
                    ep.state = 'half_open'
                    ep.half_open_count = 0
                    logger(f"[网格] 熔断器半开: {ep.service_name}")

        if ep:
            self._save_endpoint_to_db(ep)

    def execute_request(self, service_name: str, request_func: Callable,
                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行请求（带重试和熔断）"""
        context = context or {}
        retry = self.retry_policies.get('default', self.default_retry)

        last_error = None
        last_status = None

        for attempt in range(1, retry.max_retries + 1):
            ep = self.select_endpoint(service_name, context)
            if not ep:
                return {
                    'success': False,
                    'error': 'no_available_endpoint',
                    'attempts': attempt - 1
                }

            self.check_recovery(ep.endpoint_id)

            start_time = time.time()

            try:
                result = request_func(ep.address, context)
                response_time = time.time() - start_time

                status_code = result.get('status_code', 200) if isinstance(result, dict) else 200

                if status_code < 400:
                    self.record_success(ep.endpoint_id, response_time)
                    self._log_request(context.get('source', ''), ep.address,
                                    'REQUEST', status_code, response_time,
                                    attempt, True, '')
                    return {
                        'success': True,
                        'result': result,
                        'endpoint': ep.address,
                        'attempts': attempt,
                        'response_time': response_time
                    }
                else:
                    last_status = status_code
                    self.record_failure(ep.endpoint_id, f'HTTP {status_code}')

                    if not retry.should_retry(attempt, status_code):
                        self._log_request(context.get('source', ''), ep.address,
                                        'REQUEST', status_code, response_time,
                                        attempt, False, f'HTTP {status_code}')
                        return {
                            'success': False,
                            'status_code': status_code,
                            'endpoint': ep.address,
                            'attempts': attempt,
                            'response_time': response_time
                        }

            except Exception as e:
                last_error = str(e)
                response_time = time.time() - start_time
                self.record_failure(ep.endpoint_id, last_error)

                if not retry.should_retry(attempt, error=last_error):
                    self._log_request(context.get('source', ''), ep.address,
                                    'REQUEST', 0, response_time,
                                    attempt, False, last_error)
                    return {
                        'success': False,
                        'error': last_error,
                        'endpoint': ep.address,
                        'attempts': attempt,
                        'response_time': response_time
                    }

            delay = retry.get_delay(attempt)
            time.sleep(delay)

        return {
            'success': False,
            'error': last_error or f'HTTP {last_status}',
            'attempts': retry.max_retries
        }

    def _log_request(self, source: str, destination: str, method: str,
                     status_code: int, response_time: float,
                     attempts: int, success: bool, error: str):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO mesh_request_logs
                (source, destination, method, status_code, response_time,
                 attempts, success, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source, destination, method, status_code,
                response_time, attempts, 1 if success else 0, error
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def get_endpoints(self, service_name: str = None) -> List[Dict[str, Any]]:
        with self.lock:
            if service_name:
                return [e.to_dict() for e in self.endpoints.values()
                        if e.service_name == service_name]
            return [e.to_dict() for e in self.endpoints.values()]

    def get_routes(self, source: str = None) -> List[Dict[str, Any]]:
        with self.lock:
            if source:
                return [r.to_dict() for r in self.routes.values() if r.source == source]
            return [r.to_dict() for r in self.routes.values()]

    def get_request_stats(self, hours: int = 24) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor.execute('''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
                    AVG(response_time) as avg_time,
                    AVG(attempts) as avg_attempts
                FROM mesh_request_logs
                WHERE created_at >= ?
            ''', (since,))

            row = cursor.fetchone()

            conn.close()

            return {
                'total_requests': row[0] or 0,
                'successful': row[1] or 0,
                'failed': row[2] or 0,
                'avg_response_time': round(row[3] or 0, 3),
                'avg_attempts': round(row[4] or 0, 2),
                'success_rate': round((row[1] or 0) / max(1, row[0] or 1) * 100, 2)
            }
        except Exception as e:
            logger(f"[网格] 获取统计失败: {e}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            open_count = sum(1 for e in self.endpoints.values() if e.state == 'open')
            half_open_count = sum(1 for e in self.endpoints.values() if e.state == 'half_open')

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_endpoints': len(self.endpoints),
                'open_circuits': open_count,
                'half_open_circuits': half_open_count,
                'total_routes': len(self.routes)
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[网格] 服务网格代理已启动")

    def stop(self):
        self.is_running = False
        logger(f"[网格] 服务网格代理已停止")


service_mesh_proxy = ServiceMeshProxy()
