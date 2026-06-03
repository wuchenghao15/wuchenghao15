# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Configuration Manager with Real-time Loading
实时配置加载管理器
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Thread, Lock
import time
import sys


class ConfigManager:
    """配置管理器 - 支持实时加载"""
    
    def __init__(self, db_path: str, auto_reload_interval: int = 30):
        self.db_path = db_path
        self.auto_reload_interval = auto_reload_interval
        self.config_cache = {}
        self.last_reload_time = None
        self.lock = Lock()
        self._init_db()
        self._load_config()
        
        # 启动自动重载线程
        self._start_auto_reload()
    
    def _init_db(self):
        """初始化配置数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT NOT NULL,
            config_type TEXT DEFAULT 'string',
            description TEXT,
            category TEXT DEFAULT 'general',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
        
        self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        default_configs = [
            {'config_key': 'APP_NAME', 'config_value': 'MTSCOS AI System', 'config_type': 'string', 'description': '应用名称', 'category': 'app'},
            {'config_key': 'APP_VERSION', 'config_value': '4.6.0', 'config_type': 'string', 'description': '应用版本', 'category': 'app'},
            {'config_key': 'APP_ENV', 'config_value': 'production', 'config_type': 'string', 'description': '运行环境', 'category': 'app'},
            {'config_key': 'DEBUG_MODE', 'config_value': 'false', 'config_type': 'boolean', 'description': '调试模式', 'category': 'app'},
            {'config_key': 'LOG_LEVEL', 'config_value': 'INFO', 'config_type': 'string', 'description': '日志级别', 'category': 'logging'},
            {'config_key': 'LOG_FILE', 'config_value': 'app.log', 'config_type': 'string', 'description': '日志文件路径', 'category': 'logging'},
            {'config_key': 'SESSION_TIMEOUT', 'config_value': '30', 'config_type': 'integer', 'description': '会话超时(分钟)', 'category': 'security'},
            {'config_key': 'MAX_LOGIN_ATTEMPTS', 'config_value': '5', 'config_type': 'integer', 'description': '最大登录尝试次数', 'category': 'security'},
            {'config_key': 'PASSWORD_EXPIRY_DAYS', 'config_value': '90', 'config_type': 'integer', 'description': '密码过期天数', 'category': 'security'},
            {'config_key': 'ENABLE_REGISTRATION', 'config_value': 'true', 'config_type': 'boolean', 'description': '允许注册', 'category': 'security'},
            {'config_key': 'MAINTENANCE_MODE', 'config_value': 'false', 'config_type': 'boolean', 'description': '维护模式', 'category': 'system'},
            {'config_key': 'AUTO_CLEANUP_ENABLED', 'config_value': 'true', 'config_type': 'boolean', 'description': '自动清理启用', 'category': 'system'},
            {'config_key': 'CLEANUP_INTERVAL_DAYS', 'config_value': '30', 'config_type': 'integer', 'description': '清理间隔天数', 'category': 'system'},
            {'config_key': 'NOTIFICATION_ENABLED', 'config_value': 'true', 'config_type': 'boolean', 'description': '通知启用', 'category': 'notification'},
            {'config_key': 'EMAIL_NOTIFICATION', 'config_value': 'true', 'config_type': 'boolean', 'description': '邮件通知', 'category': 'notification'},
            {'config_key': 'ALERT_THRESHOLD_CPU', 'config_value': '90', 'config_type': 'integer', 'description': 'CPU告警阈值(%)', 'category': 'monitor'},
            {'config_key': 'ALERT_THRESHOLD_MEMORY', 'config_value': '80', 'config_type': 'integer', 'description': '内存告警阈值(%)', 'category': 'monitor'},
            {'config_key': 'ALERT_THRESHOLD_DISK', 'config_value': '95', 'config_type': 'integer', 'description': '磁盘告警阈值(%)', 'category': 'monitor'},
            {'config_key': 'MAX_USERS', 'config_value': '1000', 'config_type': 'integer', 'description': '最大用户数', 'category': 'limits'},
            {'config_key': 'MAX_QUESTIONS', 'config_value': '10000', 'config_type': 'integer', 'description': '最大题目数', 'category': 'limits'},
            {'config_key': 'MAX_EXAMS_PER_USER', 'config_value': '50', 'config_type': 'integer', 'description': '用户最大考试数', 'category': 'limits'}
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for config in default_configs:
                cursor.execute('SELECT COUNT(*) FROM system_config WHERE config_key = ?', (config['config_key'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                    INSERT INTO system_config (config_key, config_value, config_type, description, category)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (config['config_key'], config['config_value'], config['config_type'], 
                          config['description'], config['category']))
            
            conn.commit()
    
    def _load_config(self):
        """加载配置到缓存"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('SELECT config_key, config_value, config_type FROM system_config WHERE is_active = 1')
                for row in cursor.fetchall():
                    key = row[0]
                    value = row[1]
                    config_type = row[2]
                    
                    # 类型转换
                    self.config_cache[key] = self._convert_value(value, config_type)
                
            self.last_reload_time = datetime.now()
    
    def _convert_value(self, value: str, config_type: str):
        """根据类型转换值"""
        try:
            if config_type == 'boolean':
                return value.lower() == 'true'
            elif config_type == 'integer':
                return int(value)
            elif config_type == 'float':
                return float(value)
            elif config_type == 'json':
                return json.loads(value)
            else:
                return value
        except Exception:
            return value
    
    def _start_auto_reload(self):
        """启动自动重载线程"""
        def reload_loop():
            while True:
                time.sleep(self.auto_reload_interval)
                self._load_config()
        
        self.reload_thread = Thread(target=reload_loop, daemon=True)
        self.reload_thread.start()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config_cache.get(key, default)
    
    def set(self, key: str, value: Any, config_type: str = 'string', description: str = '', category: str = 'general') -> bool:
        """设置配置值"""
        try:
            value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO system_config (config_key, config_value, config_type, description, category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (key, value_str, config_type, description, category, datetime.now()))
                
                conn.commit()
            
            # 立即更新缓存
            with self.lock:
                self.config_cache[key] = value
            
            return True
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    def get_by_category(self, category: str) -> Dict[str, Any]:
        """按类别获取配置"""
        result = {}
        for key, value in self.config_cache.items():
            # 从数据库获取类别信息
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                cursor.execute('SELECT category FROM system_config WHERE config_key = ?', (key,))
                row = cursor.fetchone()
            
            if row and row[0] == category:
                result[key] = value
        
        return result
    
    def reload(self):
        """手动重载配置"""
        self._load_config()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_cache.copy()
    
    def get_config_info(self, key: str) -> Optional[Dict]:
        """获取配置详细信息"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM system_config WHERE config_key = ?', (key,))
            row = cursor.fetchone()
            
        
        if row:
            columns = ['id', 'config_key', 'config_value', 'config_type', 'description', 'category', 'is_active', 'created_at', 'updated_at']
            return dict(zip(columns, row))
        
        return None
    
    def update_config_type(self, key: str, new_type: str) -> bool:
        """更新配置类型"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('UPDATE system_config SET config_type = ?, updated_at = ? WHERE config_key = ?',
                (new_type, datetime.now(), key))
                
                conn.commit()
            
            # 重新加载配置以应用类型变更
            self._load_config()
            
            return True
        except Exception as e:
            logger.error(f"Failed to update config type {key}: {e}")
            return False
    
    def delete_config(self, key: str) -> bool:
        """删除配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM system_config WHERE config_key = ?', (key,))
                
                conn.commit()
            
            # 从缓存移除
            with self.lock:
                self.config_cache.pop(key, None)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete config {key}: {e}")
            return False


# 全局配置管理器实例
config_manager: Optional[ConfigManager] = None


def init_config_manager(db_path: str, auto_reload_interval: int = 30):
    """初始化配置管理器"""
    global config_manager
    config_manager = ConfigManager(db_path, auto_reload_interval)
    return config_manager


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
    return config_manager


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any, config_type: str = 'string', description: str = '', category: str = 'general') -> bool:
    """设置配置值"""
    return get_config_manager().set(key, value, config_type, description, category)


def reload_config():
    """手动重载配置"""
    get_config_manager().reload()
