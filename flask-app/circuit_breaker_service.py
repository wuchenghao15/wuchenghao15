#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS断路器服务
提供故障恢复和容错机制
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print

class CircuitBreaker:
    """断路器"""
    
    STATES = ['closed', 'open', 'half_open']
    
    def __init__(self, breaker_id: str, name: str,
                 failure_threshold: int = 5, recovery_timeout: int = 30,
                 success_threshold: int = 3, enabled: bool = True):
        self.breaker_id = breaker_id
        self.name = name
        self.state = 'closed'
        self.failure_count = 0
        self.success_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.enabled = enabled
        self.last_failure_time = None
        self.last_state_change = datetime.now().isoformat()
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """调用受保护的函数"""
        if not self.enabled:
            return func(*args, **kwargs)
        
        with self.lock:
            if self.state == 'open':
                now = time.time()
                if self.last_failure_time and now - self.last_failure_time >= self.recovery_timeout:
                    self.state = 'half_open'
                    self.last_state_change = datetime.now().isoformat()
                    logger(f"[熔断] 断路器 {self.name} 进入半开状态")
                else:
                    raise CircuitBreakerOpenError(f"断路器 {self.name} 已打开")
            
            try:
                result = func(*args, **kwargs)
                
                with self.lock:
                    if self.state == 'half_open':
                        self.success_count += 1
                        if self.success_count >= self.success_threshold:
                            self.state = 'closed'
                            self.failure_count = 0
                            self.success_count = 0
                            self.last_state_change = datetime.now().isoformat()
                            logger(f"[熔断] 断路器 {self.name} 恢复关闭状态")
                    else:
                        self.failure_count = 0
                
                return result
            except Exception as e:
                with self.lock:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    
                    if self.failure_count >= self.failure_threshold:
                        self.state = 'open'
                        self.last_state_change = datetime.now().isoformat()
                        logger(f"[熔断] 断路器 {self.name} 打开，故障数: {self.failure_count}")
                
                raise
    
    def force_open(self):
        """强制打开断路器"""
        with self.lock:
            self.state = 'open'
            self.last_failure_time = time.time()
            self.last_state_change = datetime.now().isoformat()
        logger(f"[熔断] 强制打开断路器: {self.name}")
    
    def force_close(self):
        """强制关闭断路器"""
        with self.lock:
            self.state = 'closed'
            self.failure_count = 0
            self.success_count = 0
            self.last_state_change = datetime.now().isoformat()
        logger(f"[熔断] 强制关闭断路器: {self.name}")
    
    def get_state(self) -> str:
        """获取当前状态"""
        with self.lock:
            if self.state == 'open':
                now = time.time()
                if self.last_failure_time and now - self.last_failure_time >= self.recovery_timeout:
                    return 'half_open'
            return self.state
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'breaker_id': self.breaker_id,
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'success_threshold': self.success_threshold,
            'enabled': self.enabled,
            'last_state_change': self.last_state_change
        }

class CircuitBreakerOpenError(Exception):
    """断路器打开异常"""
    pass

class FallbackHandler:
    """降级处理器"""
    
    def __init__(self, fallback_func: Callable, description: str = ''):
        self.fallback_func = fallback_func
        self.description = description
        self.call_count = 0
        self.last_call = None
    
    def execute(self, *args, **kwargs):
        """执行降级逻辑"""
        self.call_count += 1
        self.last_call = datetime.now().isoformat()
        return self.fallback_func(*args, **kwargs)

class CircuitBreakerService:
    """断路器服务"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.fallbacks: Dict[str, FallbackHandler] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._register_default_breakers()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'circuit_breaker_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'default_failure_threshold': 5,
            'default_recovery_timeout': 30,
            'default_success_threshold': 3,
            'auto_reset_enabled': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'circuit_breaker_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS circuit_breakers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    breaker_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    failure_threshold INTEGER DEFAULT 5,
                    recovery_timeout INTEGER DEFAULT 30,
                    success_threshold INTEGER DEFAULT 3,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breaker_state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    breaker_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    reason TEXT,
                    changed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fallback_handlers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    handler_id TEXT NOT NULL UNIQUE,
                    breaker_id TEXT NOT NULL,
                    description TEXT,
                    call_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_circuit_breakers_id ON circuit_breakers(breaker_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_breaker_history_breaker ON breaker_state_history(breaker_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[熔断] 初始化数据库失败: {e}")
    
    def _register_default_breakers(self):
        """注册默认断路器"""
        default_breakers = [
            CircuitBreaker('db_main', '主数据库', 5, 30, 3),
            CircuitBreaker('db_slave', '从数据库', 5, 30, 3),
            CircuitBreaker('api_external', '外部API', 3, 60, 5),
            CircuitBreaker('api_ai', 'AI接口', 5, 30, 3),
            CircuitBreaker('api_auth', '认证接口', 3, 30, 3),
            CircuitBreaker('cache_redis', 'Redis缓存', 5, 15, 3),
            CircuitBreaker('service_email', '邮件服务', 3, 60, 3),
            CircuitBreaker('service_sms', '短信服务', 3, 60, 3)
        ]
        
        for breaker in default_breakers:
            if breaker.breaker_id not in self.breakers:
                self.breakers[breaker.breaker_id] = breaker
                self._save_breaker_to_db(breaker)
    
    def _generate_breaker_id(self) -> str:
        """生成断路器ID"""
        return f"breaker_{int(time.time())}_{hash(os.urandom(16))}"
    
    def add_breaker(self, name: str, failure_threshold: int = 5,
                    recovery_timeout: int = 30, success_threshold: int = 3,
                    enabled: bool = True) -> str:
        """添加断路器"""
        breaker_id = self._generate_breaker_id()
        
        breaker = CircuitBreaker(
            breaker_id=breaker_id,
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            enabled=enabled
        )
        
        with self.lock:
            self.breakers[breaker_id] = breaker
        
        self._save_breaker_to_db(breaker)
        self._log_state_change(breaker_id, 'closed', 'created')
        logger(f"[熔断] 添加断路器: {name}")
        
        return breaker_id
    
    def _save_breaker_to_db(self, breaker: CircuitBreaker):
        """保存断路器到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO circuit_breakers 
                (breaker_id, name, failure_threshold, recovery_timeout, success_threshold, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                breaker.breaker_id, breaker.name,
                breaker.failure_threshold, breaker.recovery_timeout,
                breaker.success_threshold, 1 if breaker.enabled else 0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[熔断] 保存断路器失败: {e}")
    
    def remove_breaker(self, breaker_id: str) -> bool:
        """删除断路器"""
        with self.lock:
            if breaker_id not in self.breakers:
                logger(f"[熔断] 断路器不存在: {breaker_id}")
                return False
            
            del self.breakers[breaker_id]
        
        self._delete_breaker_from_db(breaker_id)
        logger(f"[熔断] 删除断路器: {breaker_id}")
        
        return True
    
    def _delete_breaker_from_db(self, breaker_id: str):
        """从数据库删除断路器"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM circuit_breakers WHERE breaker_id = ?', (breaker_id,))
            cursor.execute('DELETE FROM breaker_state_history WHERE breaker_id = ?', (breaker_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[熔断] 删除断路器失败: {e}")
    
    def register_fallback(self, breaker_id: str, fallback_func: Callable, description: str = '') -> str:
        """注册降级处理器"""
        handler_id = f"fallback_{breaker_id}"
        
        fallback = FallbackHandler(fallback_func, description)
        self.fallbacks[handler_id] = fallback
        
        self._save_fallback_to_db(handler_id, breaker_id, description)
        logger(f"[熔断] 注册降级处理器: {handler_id}")
        
        return handler_id
    
    def _save_fallback_to_db(self, handler_id: str, breaker_id: str, description: str):
        """保存降级处理器到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO fallback_handlers 
                (handler_id, breaker_id, description)
                VALUES (?, ?, ?)
            ''', (handler_id, breaker_id, description))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[熔断] 保存降级处理器失败: {e}")
    
    def execute_with_fallback(self, breaker_id: str, func: Callable, *args, **kwargs):
        """执行带降级的调用"""
        breaker = self.breakers.get(breaker_id)
        
        if not breaker:
            return func(*args, **kwargs)
        
        fallback_key = f"fallback_{breaker_id}"
        fallback = self.fallbacks.get(fallback_key)
        
        try:
            return breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            if fallback:
                logger(f"[熔断] 断路器打开，执行降级: {breaker.name}")
                return fallback.execute(*args, **kwargs)
            raise
        except Exception:
            raise
    
    def protect(self, breaker_id: str):
        """装饰器：保护函数"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                return self.execute_with_fallback(breaker_id, func, *args, **kwargs)
            return wrapper
        return decorator
    
    def _log_state_change(self, breaker_id: str, state: str, reason: str):
        """记录状态变更"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO breaker_state_history (breaker_id, state, reason)
                VALUES (?, ?, ?)
            ''', (breaker_id, state, reason))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[熔断] 记录状态变更失败: {e}")
    
    def get_breaker(self, breaker_id: str) -> Optional[CircuitBreaker]:
        """获取断路器"""
        return self.breakers.get(breaker_id)
    
    def get_breakers(self, state: str = None) -> List[CircuitBreaker]:
        """获取断路器列表"""
        with self.lock:
            if state:
                return [b for b in self.breakers.values() if b.get_state() == state]
            return list(self.breakers.values())
    
    def get_state_history(self, breaker_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取状态变更历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM breaker_state_history WHERE 1=1'
            params = []
            
            if breaker_id:
                query += ' AND breaker_id = ?'
                params.append(breaker_id)
            
            query += ' ORDER BY changed_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                history.append(dict(zip(columns, row)))
            
            conn.close()
            return history
        except Exception as e:
            logger(f"[熔断] 获取状态历史失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            open_count = sum(1 for b in self.breakers.values() if b.get_state() == 'open')
            half_open_count = sum(1 for b in self.breakers.values() if b.get_state() == 'half_open')
            closed_count = sum(1 for b in self.breakers.values() if b.get_state() == 'closed')
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'enabled': self.config['enabled'],
                'total_breakers': len(self.breakers),
                'open_count': open_count,
                'half_open_count': half_open_count,
                'closed_count': closed_count,
                'auto_reset_enabled': self.config['auto_reset_enabled'],
                'total_fallbacks': len(self.fallbacks)
            }
    
    def start(self):
        """启动断路器服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[熔断] 断路器服务已启动")
    
    def stop(self):
        """停止断路器服务"""
        self.is_running = False
        logger(f"[熔断] 断路器服务已停止")

circuit_breaker_service = CircuitBreakerService()
