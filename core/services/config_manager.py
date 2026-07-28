#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS配置管理服务 统一管理系统配置项 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_cache: Dict[str, Any] = {}
        self.config_file_cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'config_manager_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'cache_enabled': True,
            'cache_ttl': 300,
            'auto_save': True,
            'config_dir': 'config'
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'config_manager_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS system_config ( id INTEGER PRIMARY KEY AUTOINCREMENT, config_key TEXT NOT NULL UNIQUE, config_value TEXT, config_type TEXT DEFAULT 'string', description TEXT, category TEXT DEFAULT 'general', is_secret INTEGER DEFAULT 0, is_readonly INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(config_key) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_config_category ON system_config(category) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配置] 初始化数据库失败: {e}")
    
    def _load_from_db(self):
        """从数据库加载配置"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT config_key, config_value, config_type FROM system_config')
            
            for row in cursor.fetchall():
                key, value, value_type = row
                
                try:
                    if value_type == 'json':
                        self.config_cache[key] = json.loads(value)
                    elif value_type == 'int':
                        self.config_cache[key] = int(value)
                    elif value_type == 'float':
                        self.config_cache[key] = float(value)
                    elif value_type == 'bool':
                        self.config_cache[key] = value.lower() == 'true'
                    else:
                        self.config_cache[key] = value
                except:
                    self.config_cache[key] = value
            
            conn.close()
        except Exception as e:
            logger(f"[配置] 从数据库加载失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if key in self.config_cache:
            return self.config_cache[key]
        
        self._load_from_db()
        
        if key in self.config_cache:
            return self.config_cache[key]
        
        return default
    
    def set(self, key: str, value: Any, description: str = None, 
            category: str = 'general', is_secret: bool = False, 
            is_readonly: bool = False):
        """设置配置值"""
        value_type = self._detect_type(value)
        
        if isinstance(value, dict) or isinstance(value, list):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO system_config (config_key, config_value, config_type, description, category, is_secret, is_readonly, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (key, value_str, value_type, description, category,
                  1 if is_secret else 0, 1 if is_readonly else 0, 
                  datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            with self.lock:
                self.config_cache[key] = value
            
            logger(f"[配置] 配置已更新: {key}")
        except Exception as e:
            logger(f"[配置] 设置配置失败: {e}")
    
    def _detect_type(self, value: Any) -> str:
        """检测值类型"""
        if isinstance(value, dict) or isinstance(value, list):
            return 'json'
        elif isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        return 'string'
    
    def delete(self, key: str):
        """删除配置"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM system_config WHERE config_key = ?', (key,))
            
            conn.commit()
            conn.close()
            
            with self.lock:
                if key in self.config_cache:
                    del self.config_cache[key]
            
            logger(f"[配置] 配置已删除: {key}")
        except Exception as e:
            logger(f"[配置] 删除配置失败: {e}")
    
    def get_by_category(self, category: str) -> Dict[str, Any]:
        """按分类获取配置"""
        result = {}
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT config_key, config_value, config_type FROM system_config WHERE category = ?',
            (category,))
            
            for row in cursor.fetchall():
                key, value, value_type = row
                
                try:
                    if value_type == 'json':
                        result[key] = json.loads(value)
                    elif value_type == 'int':
                        result[key] = int(value)
                    elif value_type == 'float':
                        result[key] = float(value)
                    elif value_type == 'bool':
                        result[key] = value.lower() == 'true'
                    else:
                        result[key] = value
                except:
                    result[key] = value
            
            conn.close()
        except Exception as e:
            logger(f"[配置] 获取分类配置失败: {e}")
        
        return result
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        result = {}
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT config_key, config_value, config_type, category, description, is_secret FROM system_config')
            
            for row in cursor.fetchall():
                key, value, value_type, category, description, is_secret = row
                
                try:
                    if value_type == 'json':
                        val = json.loads(value)
                    elif value_type == 'int':
                        val = int(value)
                    elif value_type == 'float':
                        val = float(value)
                    elif value_type == 'bool':
                        val = value.lower() == 'true'
                    else:
                        val = value
                except:
                    val = value
                
                result[key] = {
                    'value': val,
                    'type': value_type,
                    'category': category,
                    'description': description,
                    'is_secret': bool(is_secret)
                }
            
            conn.close()
        except Exception as e:
            logger(f"[配置] 获取所有配置失败: {e}")
        
        return result
    
    def load_config_file(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        file_path = os.path.abspath(file_path)
        
        if file_path in self.config_file_cache:
            return self.config_file_cache[file_path]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.config_file_cache[file_path] = config
            logger(f"[配置] 配置文件已加载: {file_path}")
            return config
        except Exception as e:
            logger(f"[配置] 加载配置文件失败: {e}")
            return {}
    
    def save_config_file(self, file_path: str, config: Dict[str, Any]):
        """保存配置文件"""
        file_path = os.path.abspath(file_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.config_file_cache[file_path] = config
            logger(f"[配置] 配置文件已保存: {file_path}")
        except Exception as e:
            logger(f"[配置] 保存配置文件失败: {e}")
    
    def reload_cache(self):
        """重新加载缓存"""
        with self.lock:
            self.config_cache.clear()
        self._load_from_db()
        logger(f"[配置] 缓存已重新加载")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM system_config')
            config_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM system_config WHERE is_secret = 1')
            secret_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'running',
                'config_count': config_count,
                'secret_count': secret_count,
                'cache_size': len(self.config_cache),
                'cache_enabled': self.config['cache_enabled'],
                'cache_ttl': self.config['cache_ttl']
            }
        except Exception as e:
            logger(f"[配置] 获取状态失败: {e}")
            return {'status': 'error', 'error': str(e)}

config_manager = ConfigManager()



