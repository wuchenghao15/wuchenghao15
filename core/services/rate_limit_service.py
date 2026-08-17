#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS限流服务 提供API速率限制和流量控制功能 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print

class RateLimitRule:
    """限流规则"""
    
    def __init__(self, rule_id: str, name: str, key_type: str = 'ip',
                 limit: int = 100, window_seconds: int = 60,
                 burst_limit: int = 200, enabled: bool = True,
                 created_at: str = None):
        self.rule_id = rule_id
        self.name = name
        self.key_type = key_type
        self.limit = limit
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'key_type': self.key_type,
            'limit': self.limit,
            'window_seconds': self.window_seconds,
            'burst_limit': self.burst_limit,
            'enabled': self.enabled,
            'created_at': self.created_at
        }

class TokenBucket:
    """令牌桶算法"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_tokens(self) -> float:
        """获取当前令牌数"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            return self.tokens

class SlidingWindowCounter:
    """滑动窗口计数器"""
    
    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self.timestamps: List[float] = []
        self.lock = threading.Lock()
    
    def increment(self) -> int:
        """增加计数"""
        with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
            self.timestamps.append(now)
            return len(self.timestamps)
    
    def get_count(self) -> int:
        """获取当前计数"""
        with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
            return len(self.timestamps)

class RateLimitService:
    """限流服务"""
    
    def __init__(self):
        self.rules: Dict[str, RateLimitRule] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._register_default_rules()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'rate_limit_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'default_limit': 100,
            'default_window': 60,
            'block_duration': 300,
            'max_blocked_ips': 1000,
            'use_token_bucket': True,
            'use_sliding_window': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'rate_limit_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS rate_limit_rules ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, key_type TEXT DEFAULT 'ip', limit INTEGER DEFAULT 100, window_seconds INTEGER DEFAULT 60, burst_limit INTEGER DEFAULT 200, enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS rate_limit_logs ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT, key TEXT, request_count INTEGER, limit INTEGER, window_seconds INTEGER, allowed INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS blocked_ips ( id INTEGER PRIMARY KEY AUTOINCREMENT, ip_address TEXT NOT NULL UNIQUE, block_reason TEXT, blocked_at TEXT DEFAULT CURRENT_TIMESTAMP, expires_at TEXT ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_rate_limit_rules_id ON rate_limit_rules(rule_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip ON blocked_ips(ip_address) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[限流] 初始化数据库失败: {e}")
    
    def _register_default_rules(self):
        """注册默认限流规则"""
        default_rules = [
            RateLimitRule('global_ip', '全局IP限流', 'ip', 100, 60),
            RateLimitRule('global_user', '全局用户限流', 'user_id', 200, 60),
            RateLimitRule('api_login', '登录接口限流', 'endpoint', 10, 60),
            RateLimitRule('api_register', '注册接口限流', 'endpoint', 5, 60),
            RateLimitRule('api_search', '搜索接口限流', 'endpoint', 50, 60),
            RateLimitRule('api_upload', '上传接口限流', 'endpoint', 20, 60),
            RateLimitRule('api_ai', 'AI接口限流', 'endpoint', 30, 60),
            RateLimitRule('api_admin', '管理接口限流', 'endpoint', 50, 60)
        ]
        
        for rule in default_rules:
            if rule.rule_id not in self.rules:
                self.rules[rule.rule_id] = rule
                self._save_rule_to_db(rule)
    
    def _generate_rule_id(self) -> str:
        """生成规则ID"""
        return f"rate_rule_{int(time.time())}_{hash(os.urandom(16))}"
    
    def add_rule(self, name: str, key_type: str = 'ip',
                limit: int = 100, window_seconds: int = 60,
                burst_limit: int = 200, enabled: bool = True) -> str:
        """添加限流规则"""
        rule_id = self._generate_rule_id()
        
        rule = RateLimitRule(
            rule_id=rule_id,
            name=name,
            key_type=key_type,
            limit=limit,
            window_seconds=window_seconds,
            burst_limit=burst_limit,
            enabled=enabled
        )
        
        with self.lock:
            self.rules[rule_id] = rule
        
        self._save_rule_to_db(rule)
        logger(f"[限流] 添加规则: {name}")
        
        return rule_id
    
    def _save_rule_to_db(self, rule: RateLimitRule):
        """保存规则到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR IGNORE INTO rate_limit_rules (rule_id, name, key_type, limit, window_seconds, burst_limit, enabled) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (
                rule.rule_id, rule.name, rule.key_type,
                rule.limit, rule.window_seconds,
                rule.burst_limit, 1 if rule.enabled else 0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[限流] 保存规则失败: {e}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """删除限流规则"""
        with self.lock:
            if rule_id not in self.rules:
                logger(f"[限流] 规则不存在: {rule_id}")
                return False
            
            del self.rules[rule_id]
        
        self._delete_rule_from_db(rule_id)
        logger(f"[限流] 删除规则: {rule_id}")
        
        return True
    
    def _delete_rule_from_db(self, rule_id: str):
        """从数据库删除规则"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM rate_limit_rules WHERE rule_id = ?', (rule_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[限流] 删除规则失败: {e}")
    
    def check_rate_limit(self, key: str, rule_id: str = None) -> Dict[str, Any]:
        """检查限流"""
        if not self.config['enabled']:
            return {'allowed': True, 'remaining': -1, 'reset_time': -1}
        
        rules_to_check = []
        
        if rule_id:
            rule = self.rules.get(rule_id)
            if rule and rule.enabled:
                rules_to_check.append(rule)
        else:
            rules_to_check = [r for r in self.rules.values() if r.enabled]
        
        for rule in rules_to_check:
            cache_key = f"{rule.rule_id}_{key}"
            
            if self.config['use_token_bucket']:
                if cache_key not in self.token_buckets:
                    rate = rule.limit / rule.window_seconds
                    self.token_buckets[cache_key] = TokenBucket(rate, rule.burst_limit)
                
                if not self.token_buckets[cache_key].consume():
                    remaining = int(self.token_buckets[cache_key].get_tokens())
                    reset_time = rule.window_seconds
                    self._log_limit(rule.rule_id, key, rule.limit - remaining, rule.limit, rule.window_seconds, False)
                    return {
                        'allowed': False,
                        'remaining': remaining,
                        'reset_time': reset_time,
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name
                    }
            
            if self.config['use_sliding_window']:
                if cache_key not in self.sliding_windows:
                    self.sliding_windows[cache_key] = SlidingWindowCounter(rule.window_seconds)
                
                count = self.sliding_windows[cache_key].increment()
                
                if count > rule.limit:
                    remaining = 0
                    reset_time = int(rule.window_seconds - (time.time(
                    ) - self.sliding_windows[cache_key].timestamps[0]))
                    self._log_limit(rule.rule_id, key, count, rule.limit, rule.window_seconds, False)
                    return {
                        'allowed': False,
                        'remaining': remaining,
                        'reset_time': max(0, reset_time),
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name
                    }
        
        return {'allowed': True, 'remaining': -1, 'reset_time': -1}
    
    def _log_limit(self, rule_id: str, key: str, request_count: int,
                  limit: int, window_seconds: int, allowed: bool):
        """记录限流日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO rate_limit_logs (rule_id, key, request_count, limit, window_seconds, allowed) VALUES (?, ?, ?, ?, ?, ?) ''', (rule_id, key, request_count, limit, window_seconds, 1 if allowed else 0))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[限流] 记录日志失败: {e}")
    
    def block_ip(self, ip_address: str, reason: str = 'excessive_requests'):
        """阻止IP"""
        expires_at = (datetime.now() + timedelta(seconds=self.config['block_duration'])).isoformat()
        
        with self.lock:
            self.blocked_ips[ip_address] = time.time() + self.config['block_duration']
        
        self._save_blocked_ip(ip_address, reason, expires_at)
        logger(f"[限流] 阻止IP: {ip_address} - {reason}")
    
    def _save_blocked_ip(self, ip_address: str, reason: str, expires_at: str):
        """保存阻止IP到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO blocked_ips (ip_address, block_reason, blocked_at, expires_at) VALUES (?, ?, ?, ?) ''', (ip_address, reason, datetime.now().isoformat(), expires_at))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[限流] 保存阻止IP失败: {e}")
    
    def unblock_ip(self, ip_address: str) -> bool:
        """解除IP阻止"""
        with self.lock:
            if ip_address in self.blocked_ips:
                del self.blocked_ips[ip_address]
        
        self._delete_blocked_ip(ip_address)
        logger(f"[限流] 解除阻止IP: {ip_address}")
        return True
    
    def _delete_blocked_ip(self, ip_address: str):
        """从数据库删除阻止IP"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM blocked_ips WHERE ip_address = ?', (ip_address,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[限流] 删除阻止IP失败: {e}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """检查IP是否被阻止"""
        with self.lock:
            if ip_address in self.blocked_ips:
                if self.blocked_ips[ip_address] > time.time():
                    return True
                del self.blocked_ips[ip_address]
        
        return False
    
    def get_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        """获取规则"""
        return self.rules.get(rule_id)
    
    def get_rules(self, enabled_only: bool = False) -> List[RateLimitRule]:
        """获取规则列表"""
        with self.lock:
            if enabled_only:
                return [r for r in self.rules.values() if r.enabled]
            return list(self.rules.values())
    
    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """获取被阻止的IP列表"""
        result = []
        
        with self.lock:
            for ip, expires_at in self.blocked_ips.items():
                if expires_at > time.time():
                    result.append({
                        'ip_address': ip,
                        'expires_at': datetime.fromtimestamp(expires_at).isoformat()
                    })
        
        return result
    
    def get_rate_limit_stats(self, rule_id: str = None) -> Dict[str, Any]:
        """获取限流统计"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) as total, SUM(CASE WHEN allowed = 0 THEN 1 ELSE 0 END) as blocked FROM rate_limit_logs'
            params = []
            
            if rule_id:
                query += ' WHERE rule_id = ?'
                params.append(rule_id)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_requests': row[0] or 0,
                'blocked_requests': row[1] or 0,
                'block_rate': round((row[1] or 0) / max(1, row[0] or 1) * 100, 2)
            }
        except Exception as e:
            logger(f"[限流] 获取统计失败: {e}")
            return {'total_requests': 0, 'blocked_requests': 0, 'block_rate': 0.0}
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            enabled_rules = sum(1 for r in self.rules.values() if r.enabled)
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'enabled': self.config['enabled'],
                'total_rules': len(self.rules),
                'enabled_rules': enabled_rules,
                'blocked_ips_count': len(self.blocked_ips),
                'use_token_bucket': self.config['use_token_bucket'],
                'use_sliding_window': self.config['use_sliding_window'],
                'block_duration': self.config['block_duration']
            }
    
    def start(self):
        """启动限流服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self._start_cleanup_thread()
        logger(f"[限流] 限流服务已启动")
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup():
            while self.is_running:
                time.sleep(60)
                
                with self.lock:
                    now = time.time()
                    self.blocked_ips = {ip: exp for ip, exp in self.blocked_ips.items() if exp > now}
                
                if len(self.token_buckets) > 10000:
                    with self.lock:
                        keys = list(self.token_buckets.keys())[:5000]
                        for key in keys:
                            del self.token_buckets[key]
                
                if len(self.sliding_windows) > 10000:
                    with self.lock:
                        keys = list(self.sliding_windows.keys())[:5000]
                        for key in keys:
                            del self.sliding_windows[key]
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def stop(self):
        """停止限流服务"""
        self.is_running = False
        logger(f"[限流] 限流服务已停止")

rate_limit_service = RateLimitService()
