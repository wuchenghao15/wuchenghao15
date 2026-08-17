#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS API网关服务 统一管理API路由、认证、限流、日志 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = print

class APIEndpoint:
    """API端点"""
    
    def __init__(self, path: str, method: str, handler: Callable,
                 requires_auth: bool = False, rate_limit: int = 60,
                 rate_limit_window: int = 60, description: str = '',
                 category: str = 'general'):
        self.path = path
        self.method = method
        self.handler = handler
        self.requires_auth = requires_auth
        self.rate_limit = rate_limit
        self.rate_limit_window = rate_limit_window
        self.description = description
        self.category = category
        self.call_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'path': self.path,
            'method': self.method,
            'requires_auth': self.requires_auth,
            'rate_limit': self.rate_limit,
            'rate_limit_window': self.rate_limit_window,
            'description': self.description,
            'category': self.category,
            'call_count': self.call_count,
            'error_count': self.error_count
        }

class APIGateway:
    """API网关"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self.cleanup_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'api_gateway_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'default_rate_limit': 60,
            'default_rate_limit_window': 60,
            'max_request_size': 1048576,
            'allowed_origins': [],
            'api_key_header': 'X-API-Key',
            'auth_header': 'Authorization',
            'enable_logging': True,
            'enable_rate_limiting': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'api_gateway_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS api_endpoints ( id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, method TEXT NOT NULL, requires_auth INTEGER DEFAULT 0, rate_limit INTEGER DEFAULT 60, rate_limit_window INTEGER DEFAULT 60, description TEXT, category TEXT DEFAULT 'general', enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE UNIQUE INDEX IF NOT EXISTS idx_endpoint_path_method ON api_endpoints(path, method) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS api_request_logs ( id INTEGER PRIMARY KEY AUTOINCREMENT, endpoint TEXT NOT NULL, method TEXT NOT NULL, user_id TEXT, user_ip TEXT, status_code INTEGER, response_time REAL, request_size INTEGER, error_message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS api_keys ( id INTEGER PRIMARY KEY AUTOINCREMENT, api_key TEXT NOT NULL UNIQUE, name TEXT NOT NULL, user_id TEXT, permissions TEXT, rate_limit INTEGER DEFAULT 1000, enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, expires_at TEXT ) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网关] 初始化数据库失败: {e}")
    
    def register_endpoint(self, path: str, method: str, handler: Callable,
                          requires_auth: bool = False, rate_limit: int = None,
                          rate_limit_window: int = None, description: str = '',
                          category: str = 'general'):
        """注册API端点"""
        key = f"{method.upper()}_{path}"
        
        rate_limit = rate_limit or self.config['default_rate_limit']
        rate_limit_window = rate_limit_window or self.config['default_rate_limit_window']
        
        endpoint = APIEndpoint(
            path=path,
            method=method.upper(),
            handler=handler,
            requires_auth=requires_auth,
            rate_limit=rate_limit,
            rate_limit_window=rate_limit_window,
            description=description,
            category=category
        )
        
        with self.lock:
            self.endpoints[key] = endpoint
        
        self._save_endpoint_to_db(endpoint)
        
        logger(f"[网关] 注册API端点: {method.upper()} {path}")
    
    def _save_endpoint_to_db(self, endpoint: APIEndpoint):
        """保存端点到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO api_endpoints (path, method, requires_auth, rate_limit, rate_limit_window, description, category, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                endpoint.path, endpoint.method,
                1 if endpoint.requires_auth else 0,
                endpoint.rate_limit, endpoint.rate_limit_window,
                endpoint.description, endpoint.category,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网关] 保存端点失败: {e}")
    
    def unregister_endpoint(self, path: str, method: str):
        """注销API端点"""
        key = f"{method.upper()}_{path}"
        
        with self.lock:
            if key in self.endpoints:
                del self.endpoints[key]
        
        self._delete_endpoint_from_db(path, method)
        
        logger(f"[网关] 注销API端点: {method.upper()} {path}")
    
    def _delete_endpoint_from_db(self, path: str, method: str):
        """从数据库删除端点"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM api_endpoints WHERE path = ? AND method = ?',
                          (path, method.upper()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网关] 删除端点失败: {e}")
    
    def _check_rate_limit(self, client_ip: str, endpoint_key: str) -> bool:
        """检查速率限制"""
        if not self.config['enable_rate_limiting']:
            return True
        
        now = time.time()
        key = f"{client_ip}_{endpoint_key}"
        
        with self.lock:
            if key not in self.rate_limits:
                self.rate_limits[key] = {
                    'count': 0,
                    'window_start': now
                }
            
            rate_info = self.rate_limits[key]
            endpoint = self.endpoints.get(endpoint_key)
            
            if not endpoint:
                return True
            
            window = endpoint.rate_limit_window
            
            if now - rate_info['window_start'] > window:
                rate_info['count'] = 0
                rate_info['window_start'] = now
            
            if rate_info['count'] >= endpoint.rate_limit:
                return False
            
            rate_info['count'] += 1
        
        return True
    
    def _log_request(self, endpoint: str, method: str, user_id: str = None,
                    user_ip: str = None, status_code: int = 200,
                    response_time: float = 0, request_size: int = 0,
                    error_message: str = None):
        """记录请求日志"""
        if not self.config['enable_logging']:
            return
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO api_request_logs (endpoint, method, user_id, user_ip, status_code, response_time, request_size, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                endpoint, method, user_id, user_ip,
                status_code, response_time, request_size, error_message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[网关] 记录日志失败: {e}")
    
    def handle_request(self, path: str, method: str, user_ip: str = None,
                      user_id: str = None, headers: Dict[str, str] = None,
                      body: bytes = b'', **kwargs) -> Dict[str, Any]:
        """处理API请求"""
        start_time = time.time()
        endpoint_key = f"{method.upper()}_{path}"
        
        with self.lock:
            endpoint = self.endpoints.get(endpoint_key)
        
        if not endpoint:
            response_time = time.time() - start_time
            self._log_request(path, method, user_id, user_ip, 404, response_time, len(body), "Endpoint not found")
            return {'status_code': 404, 'error': 'Endpoint not found'}
        
        if not self._check_rate_limit(user_ip or 'unknown', endpoint_key):
            response_time = time.time() - start_time
            self._log_request(path, method, user_id, user_ip, 429, response_time, len(body), "Rate limit exceeded")
            return {'status_code': 429, 'error': 'Rate limit exceeded'}
        
        if len(body) > self.config['max_request_size']:
            response_time = time.time() - start_time
            self._log_request(path, method, user_id, user_ip, 413, response_time, len(body), "Request too large")
            return {'status_code': 413, 'error': 'Request too large'}
        
        try:
            result = endpoint.handler(**kwargs)
            
            response_time = time.time() - start_time
            
            with self.lock:
                endpoint.call_count += 1
                endpoint.total_response_time += response_time
            
            self._log_request(path, method, user_id, user_ip, 200, response_time, len(body))
            
            return {'status_code': 200, 'data': result}
        except Exception as e:
            response_time = time.time() - start_time
            
            with self.lock:
                endpoint.error_count += 1
            
            self._log_request(path, method, user_id, user_ip, 500, response_time, len(body), str(e))
            
            return {'status_code': 500, 'error': str(e)}
    
    def get_endpoint(self, path: str, method: str) -> Optional[APIEndpoint]:
        """获取端点"""
        key = f"{method.upper()}_{path}"
        return self.endpoints.get(key)
    
    def get_endpoints(self, category: str = None, requires_auth: bool = None) -> List[APIEndpoint]:
        """获取端点列表"""
        result = []
        
        with self.lock:
            for endpoint in self.endpoints.values():
                if category and endpoint.category != category:
                    continue
                if requires_auth is not None and endpoint.requires_auth != requires_auth:
                    continue
                result.append(endpoint)
        
        return result
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        
        with self.lock:
            for endpoint in self.endpoints.values():
                categories.add(endpoint.category)
        
        return sorted(list(categories))
    
    def generate_api_key(self, name: str, user_id: str = None, 
                        permissions: List[str] = None, rate_limit: int = 1000,
                        expires_at: datetime = None) -> str:
        """生成API密钥"""
        import uuid
        
        api_key = str(uuid.uuid4())
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO api_keys (api_key, name, user_id, permissions, rate_limit, enabled, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (
                api_key, name, user_id,
                json.dumps(permissions or []),
                rate_limit, 1,
                expires_at.isoformat() if expires_at else None
            ))
            
            conn.commit()
            conn.close()
            
            logger(f"[网关] 生成API密钥: {name}")
            return api_key
        except Exception as e:
            logger(f"[网关] 生成API密钥失败: {e}")
            return ''
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT name, user_id, permissions, rate_limit, enabled, expires_at FROM api_keys WHERE api_key = ?',
                          (api_key,))
            
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                name, user_id, permissions, rate_limit, enabled, expires_at = result
                
                if not enabled:
                    return None
                
                if expires_at and datetime.now().isoformat() > expires_at:
                    return None
                
                return {
                    'name': name,
                    'user_id': user_id,
                    'permissions': json.loads(permissions) if permissions else [],
                    'rate_limit': rate_limit
                }
            
            return None
        except Exception as e:
            logger(f"[网关] 验证API密钥失败: {e}")
            return None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """撤销API密钥"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM api_keys WHERE api_key = ?', (api_key,))
            
            conn.commit()
            conn.close()
            
            logger(f"[网关] 撤销API密钥")
            return True
        except Exception as e:
            logger(f"[网关] 撤销API密钥失败: {e}")
            return False
    
    def _cleanup_rate_limits(self):
        """清理过期的速率限制记录"""
        now = time.time()
        
        with self.lock:
            expired_keys = []
            
            for key, rate_info in self.rate_limits.items():
                window_start = rate_info.get('window_start', 0)
                
                if now - window_start > 3600:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.rate_limits[key]
        
        if expired_keys:
            logger(f"[网关] 清理过期速率限制: {len(expired_keys)}条")
    
    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                time.sleep(60)
                self._cleanup_rate_limits()
            except Exception as e:
                logger(f"[网关] 清理循环错误: {e}")
    
    def get_api_stats(self) -> Dict[str, Any]:
        """获取API统计"""
        with self.lock:
            total_calls = sum(endpoint.call_count for endpoint in self.endpoints.values())
            total_errors = sum(endpoint.error_count for endpoint in self.endpoints.values())
            total_response_time = sum(endpoint.total_response_time for endpoint in self.endpoints.values())
            avg_response_time = total_response_time / total_calls if total_calls > 0 else 0
            
            return {
                'total_endpoints': len(self.endpoints),
                'total_calls': total_calls,
                'total_errors': total_errors,
                'avg_response_time': round(avg_response_time, 3),
                'active_rate_limits': len(self.rate_limits)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'enable_logging': self.config['enable_logging'],
            'enable_rate_limiting': self.config['enable_rate_limiting'],
            'default_rate_limit': self.config['default_rate_limit'],
            'max_request_size': self.config['max_request_size'],
            'api_stats': self.get_api_stats()
        }
    
    def start(self):
        """启动API网关"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger(f"[网关] API网关服务已启动")
    
    def stop(self):
        """停止API网关"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        
        logger(f"[网关] API网关服务已停止")

api_gateway = APIGateway()

def api_route(path: str, method: str = 'GET', requires_auth: bool = False,
              rate_limit: int = None, description: str = '',
              category: str = 'general'):
    """装饰器：注册API路由"""
    def decorator(func):
        api_gateway.register_endpoint(
            path=path,
            method=method,
            handler=func,
            requires_auth=requires_auth,
            rate_limit=rate_limit,
            description=description,
            category=category
        )
        
        return func
    return decorator

