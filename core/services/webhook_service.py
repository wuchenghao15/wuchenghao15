#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS Webhook服务
提供外部系统集成和事件通知功能
"""

import os
import sys
import json
import time
import hmac
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print


class WebhookEndpoint:
    """Webhook端点"""

    def __init__(self, endpoint_id: str, name: str, url: str,
                 events: List[str] = None, secret: str = '',
                 enabled: bool = True, headers: Dict[str, str] = None,
                 timeout: int = 30, retry_count: int = 3,
                 retry_delay: int = 5, created_at: str = None):
        self.endpoint_id = endpoint_id
        self.name = name
        self.url = url
        self.events = events or []
        self.secret = secret
        self.enabled = enabled
        self.headers = headers or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.created_at = created_at or datetime.now().isoformat()
        self.last_triggered = None
        self.last_status = 'never'
        self.success_count = 0
        self.failure_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint_id': self.endpoint_id,
            'name': self.name,
            'url': self.url,
            'events': self.events,
            'enabled': self.enabled,
            'headers': list(self.headers.keys()),
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'created_at': self.created_at,
            'last_triggered': self.last_triggered,
            'last_status': self.last_status,
            'success_count': self.success_count,
            'failure_count': self.failure_count
        }


class WebhookDelivery:
    """Webhook投递记录"""

    def __init__(self, delivery_id: str, endpoint_id: str, event_type: str,
                 payload: Dict[str, Any], status: str = 'pending',
                 attempt: int = 0, response_code: int = None,
                 response_body: str = '', error_message: str = '',
                 created_at: str = None):
        self.delivery_id = delivery_id
        self.endpoint_id = endpoint_id
        self.event_type = event_type
        self.payload = payload
        self.status = status
        self.attempt = attempt
        self.response_code = response_code
        self.response_body = response_body
        self.error_message = error_message
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'delivery_id': self.delivery_id,
            'endpoint_id': self.endpoint_id,
            'event_type': self.event_type,
            'status': self.status,
            'attempt': self.attempt,
            'response_code': self.response_code,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }


class WebhookService:
    """Webhook服务"""

    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.delivery_queue: List[Dict[str, Any]] = []

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    events TEXT,
                    secret TEXT,
                    enabled INTEGER DEFAULT 1,
                    headers TEXT,
                    timeout INTEGER DEFAULT 30,
                    retry_count INTEGER DEFAULT 3,
                    retry_delay INTEGER DEFAULT 5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TEXT,
                    last_status TEXT DEFAULT 'never',
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delivery_id TEXT NOT NULL UNIQUE,
                    endpoint_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    status TEXT DEFAULT 'pending',
                    attempt INTEGER DEFAULT 0,
                    response_code INTEGER,
                    response_body TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_webhook_endpoints_id ON webhook_endpoints(endpoint_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_endpoint ON webhook_deliveries(endpoint_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[Webhook] 初始化数据库失败: {e}")

    def _generate_id(self, prefix: str = 'wh') -> str:
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:16]}"

    def register_endpoint(self, name: str, url: str, events: List[str] = None,
                          secret: str = '', headers: Dict[str, str] = None,
                          timeout: int = 30, retry_count: int = 3,
                          retry_delay: int = 5) -> str:
        endpoint_id = self._generate_id('ep')

        endpoint = WebhookEndpoint(
            endpoint_id=endpoint_id,
            name=name,
            url=url,
            events=events or ['*'],
            secret=secret,
            headers=headers or {'Content-Type': 'application/json'},
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay
        )

        with self.lock:
            self.endpoints[endpoint_id] = endpoint

        self._save_endpoint_to_db(endpoint)
        logger(f"[Webhook] 注册端点: {name} -> {url}")

        return endpoint_id

    def _save_endpoint_to_db(self, endpoint: WebhookEndpoint):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO webhook_endpoints
                (endpoint_id, name, url, events, secret, enabled, headers,
                 timeout, retry_count, retry_delay, last_triggered, last_status,
                 success_count, failure_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint.endpoint_id, endpoint.name, endpoint.url,
                json.dumps(endpoint.events), endpoint.secret,
                1 if endpoint.enabled else 0,
                json.dumps(endpoint.headers),
                endpoint.timeout, endpoint.retry_count, endpoint.retry_delay,
                endpoint.last_triggered, endpoint.last_status,
                endpoint.success_count, endpoint.failure_count
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[Webhook] 保存端点失败: {e}")

    def remove_endpoint(self, endpoint_id: str) -> bool:
        with self.lock:
            if endpoint_id not in self.endpoints:
                return False
            del self.endpoints[endpoint_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM webhook_endpoints WHERE endpoint_id = ?', (endpoint_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[Webhook] 删除端点失败: {e}")

        logger(f"[Webhook] 删除端点: {endpoint_id}")
        return True

    def trigger(self, event_type: str, payload: Dict[str, Any] = None):
        """触发webhook事件"""
        payload = payload or {}

        with self.lock:
            target_endpoints = [
                ep for ep in self.endpoints.values()
                if ep.enabled and ('*' in ep.events or event_type in ep.events)
            ]

        for endpoint in target_endpoints:
            delivery_id = self._generate_id('dev')

            delivery = WebhookDelivery(
                delivery_id=delivery_id,
                endpoint_id=endpoint.endpoint_id,
                event_type=event_type,
                payload=payload
            )

            with self.lock:
                self.deliveries[delivery_id] = delivery

            self._save_delivery_to_db(delivery)

            thread = threading.Thread(
                target=self._deliver_webhook,
                args=(delivery_id,),
                daemon=True
            )
            thread.start()

        logger(f"[Webhook] 触发事件 {event_type} -> {len(target_endpoints)} 个端点")

    def _deliver_webhook(self, delivery_id: str):
        """投递webhook"""
        with self.lock:
            delivery = self.deliveries.get(delivery_id)
            if not delivery:
                return

            endpoint = self.endpoints.get(delivery.endpoint_id)
            if not endpoint:
                delivery.status = 'failed'
                delivery.error_message = '端点不存在'
                return

        import urllib.request
        import urllib.error

        max_attempts = endpoint.retry_count + 1

        for attempt in range(1, max_attempts + 1):
            delivery.attempt = attempt

            try:
                payload_bytes = json.dumps({
                    'event': delivery.event_type,
                    'data': delivery.payload,
                    'timestamp': datetime.now().isoformat(),
                    'delivery_id': delivery_id
                }).encode('utf-8')

                headers = endpoint.headers.copy()

                if endpoint.secret:
                    signature = hmac.new(
                        endpoint.secret.encode('utf-8'),
                        payload_bytes,
                        hashlib.sha256
                    ).hexdigest()
                    headers['X-Webhook-Signature'] = signature

                headers['X-Webhook-Event'] = delivery.event_type
                headers['X-Webhook-Delivery'] = delivery_id

                req = urllib.request.Request(
                    endpoint.url,
                    data=payload_bytes,
                    headers=headers,
                    method='POST'
                )

                with urllib.request.urlopen(req, timeout=endpoint.timeout) as response:
                    delivery.response_code = response.getcode()
                    delivery.response_body = response.read().decode('utf-8')[:1000]

                    if 200 <= delivery.response_code < 300:
                        delivery.status = 'success'
                        delivery.completed_at = datetime.now().isoformat()

                        with self.lock:
                            endpoint.last_triggered = datetime.now().isoformat()
                            endpoint.last_status = 'success'
                            endpoint.success_count += 1

                        self._update_endpoint_stats(endpoint)
                        self._update_delivery_in_db(delivery)
                        logger(f"[Webhook] 投递成功: {endpoint.name}")
                        return
                    else:
                        delivery.status = 'failed'
                        delivery.error_message = f'HTTP {delivery.response_code}'

            except urllib.error.URLError as e:
                delivery.status = 'failed'
                delivery.error_message = str(e.reason)
            except Exception as e:
                delivery.status = 'failed'
                delivery.error_message = str(e)

            if attempt < max_attempts:
                time.sleep(endpoint.retry_delay * attempt)

        delivery.completed_at = datetime.now().isoformat()

        with self.lock:
            endpoint.last_triggered = datetime.now().isoformat()
            endpoint.last_status = 'failed'
            endpoint.failure_count += 1

        self._update_endpoint_stats(endpoint)
        self._update_delivery_in_db(delivery)
        logger(f"[Webhook] 投递失败: {endpoint.name} - {delivery.error_message}")

    def _save_delivery_to_db(self, delivery: WebhookDelivery):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO webhook_deliveries
                (delivery_id, endpoint_id, event_type, payload, status, attempt)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                delivery.delivery_id, delivery.endpoint_id,
                delivery.event_type, json.dumps(delivery.payload),
                delivery.status, delivery.attempt
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[Webhook] 保存投递记录失败: {e}")

    def _update_delivery_in_db(self, delivery: WebhookDelivery):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE webhook_deliveries
                SET status = ?, attempt = ?, response_code = ?,
                    response_body = ?, error_message = ?, completed_at = ?
                WHERE delivery_id = ?
            ''', (
                delivery.status, delivery.attempt,
                delivery.response_code, delivery.response_body,
                delivery.error_message, delivery.completed_at,
                delivery.delivery_id
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[Webhook] 更新投递记录失败: {e}")

    def _update_endpoint_stats(self, endpoint: WebhookEndpoint):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE webhook_endpoints
                SET last_triggered = ?, last_status = ?,
                    success_count = ?, failure_count = ?
                WHERE endpoint_id = ?
            ''', (
                endpoint.last_triggered, endpoint.last_status,
                endpoint.success_count, endpoint.failure_count,
                endpoint.endpoint_id
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[Webhook] 更新端点统计失败: {e}")

    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        return self.endpoints.get(endpoint_id)

    def get_endpoints(self, enabled_only: bool = False) -> List[WebhookEndpoint]:
        with self.lock:
            if enabled_only:
                return [ep for ep in self.endpoints.values() if ep.enabled]
            return list(self.endpoints.values())

    def get_deliveries(self, endpoint_id: str = None, status: str = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM webhook_deliveries WHERE 1=1'
            params = []

            if endpoint_id:
                query += ' AND endpoint_id = ?'
                params.append(endpoint_id)
            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            deliveries = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return deliveries
        except Exception as e:
            logger(f"[Webhook] 获取投递记录失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_endpoints': len(self.endpoints),
                'enabled_endpoints': sum(1 for ep in self.endpoints.values() if ep.enabled),
                'pending_deliveries': sum(1 for d in self.deliveries.values() if d.status == 'pending'),
                'total_success': sum(ep.success_count for ep in self.endpoints.values()),
                'total_failure': sum(ep.failure_count for ep in self.endpoints.values())
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[Webhook] Webhook服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[Webhook] Webhook服务已停止")


webhook_service = WebhookService()
