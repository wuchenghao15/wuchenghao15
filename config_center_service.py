#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS配置中心服务
提供统一配置管理和热更新功能
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

class ConfigItem:
    """配置项"""
    
    def __init__(self, config_id: str, key: str, value: Any,
                 description: str = '', config_type: str = 'string',
                 namespace: str = 'default', environment: str = 'all',
                 version: int = 1, created_at: str = None):
        self.config_id = config_id
        self.key = key
        self.value = value
        self.description = description
        self.config_type = config_type
        self.namespace = namespace
        self.environment = environment
        self.version = version
        self.created_at = created_at or datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'config_id': self.config_id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'config_type': self.config_type,
            'namespace': self.namespace,
            'environment': self.environment,
            'version': self.version,
            'created_at': self.created_at,
            'last_modified': self.last_modified
        }

class ConfigWatcher:
    """配置监听器"""
    
    def __init__(self, callback: Callable, keys: List[str] = None,
                 namespace: str = 'default'):
        self.callback = callback
        self.keys = keys
        self.namespace = namespace

class ConfigCenterService:
    """配置中心服务"""
    
    def __init__(self):
        self.configs: Dict[str, ConfigItem] = {}
        self.watchers: List[ConfigWatcher] = []
        self.is_running = False
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_center (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id TEXT NOT NULL UNIQUE,
                    key TEXT NOT NULL,
                    value TEXT,
                    description TEXT,
                    config_type TEXT DEFAULT 'string',
                    namespace TEXT DEFAULT 'default',
                    environment TEXT DEFAULT 'all',
                    version INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    version INTEGER,
                    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    changed_by TEXT,
                    change_reason TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id TEXT NOT NULL,
                    tag TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_config_center_key ON config_center(key)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_config_center_namespace ON config_center(namespace)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_config_history_config ON config_history(config_id)
            ''')
            
            conn.commit()
            conn.close()
            
            self._load_configs_from_db()
        except Exception as e:
            logger(f"[配置] 初始化数据库失败: {e}")
    
    def _load_configs_from_db(self):
        """从数据库加载配置"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM config_center')
            
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                config = ConfigItem(
                    config_id=data['config_id'],
                    key=data['key'],
                    value=data['value'],
                    description=data['description'],
                    config_type=data['config_type'],
                    namespace=data['namespace'],
                    environment=data['environment'],
                    version=data['version'],
                    created_at=data['created_at']
                )
                config.last_modified = data['last_modified']
                self.configs[data['config_id']] = config
            
            conn.close()
        except Exception as e:
            logger(f"[配置] 加载配置失败: {e}")
    
    def _generate_config_id(self) -> str:
        """生成配置ID"""
        return f"cfg_{int(time.time())}_{hash(os.urandom(16))}"
    
    def set(self, key: str, value: Any, description: str = '',
            config_type: str = 'string', namespace: str = 'default',
            environment: str = 'all', changed_by: str = '',
            change_reason: str = '') -> str:
        """设置配置"""
        config_id = f"cfg_{namespace}_{key}"
        
        with self.lock:
            if config_id in self.configs:
                old_value = self.configs[config_id].value
                self.configs[config_id].value = str(value)
                self.configs[config_id].description = description
                self.configs[config_id].config_type = config_type
                self.configs[config_id].environment = environment
                self.configs[config_id].version += 1
                self.configs[config_id].last_modified = datetime.now().isoformat()
            else:
                config = ConfigItem(
                    config_id=config_id,
                    key=key,
                    value=str(value),
                    description=description,
                    config_type=config_type,
                    namespace=namespace,
                    environment=environment
                )
                self.configs[config_id] = config
        
        self._save_config_to_db(self.configs[config_id])
        self._log_config_change(config_id, key, str(value), self.configs[config_id].version,
                               changed_by, change_reason)
        self._notify_watchers(key, value, namespace)
        
        logger(f"[配置] 设置配置: {namespace}.{key} = {value}")
        
        return config_id
    
    def _save_config_to_db(self, config: ConfigItem):
        """保存配置到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO config_center 
                (config_id, key, value, description, config_type, namespace, 
                 environment, version, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.config_id, config.key, config.value,
                config.description, config.config_type,
                config.namespace, config.environment,
                config.version, config.last_modified
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配置] 保存配置失败: {e}")
    
    def _log_config_change(self, config_id: str, key: str, value: str,
                           version: int, changed_by: str, change_reason: str):
        """记录配置变更"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO config_history (config_id, key, value, version, changed_by, change_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (config_id, key, value, version, changed_by, change_reason))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配置] 记录变更失败: {e}")
    
    def get(self, key: str, default: Any = None, namespace: str = 'default',
            environment: str = None) -> Any:
        """获取配置"""
        config_id = f"cfg_{namespace}_{key}"
        config = self.configs.get(config_id)
        
        if not config:
            return default
        
        if environment and config.environment != 'all' and config.environment != environment:
            return default
        
        try:
            if config.config_type == 'int':
                return int(config.value)
            elif config.config_type == 'float':
                return float(config.value)
            elif config.config_type == 'bool':
                return config.value.lower() == 'true'
            elif config.config_type == 'json':
                return json.loads(config.value)
            elif config.config_type == 'list':
                return json.loads(config.value)
            else:
                return config.value
        except:
            return config.value
    
    def get_namespace_configs(self, namespace: str = 'default') -> Dict[str, Any]:
        """获取命名空间下所有配置"""
        result = {}
        
        for config in self.configs.values():
            if config.namespace == namespace:
                result[config.key] = self._convert_value(config)
        
        return result
    
    def _convert_value(self, config: ConfigItem) -> Any:
        """转换配置值"""
        try:
            if config.config_type == 'int':
                return int(config.value)
            elif config.config_type == 'float':
                return float(config.value)
            elif config.config_type == 'bool':
                return config.value.lower() == 'true'
            elif config.config_type == 'json':
                return json.loads(config.value)
            elif config.config_type == 'list':
                return json.loads(config.value)
            else:
                return config.value
        except:
            return config.value
    
    def delete(self, key: str, namespace: str = 'default') -> bool:
        """删除配置"""
        config_id = f"cfg_{namespace}_{key}"
        
        with self.lock:
            if config_id not in self.configs:
                logger(f"[配置] 配置不存在: {namespace}.{key}")
                return False
            
            del self.configs[config_id]
        
        self._delete_config_from_db(config_id)
        logger(f"[配置] 删除配置: {namespace}.{key}")
        
        return True
    
    def _delete_config_from_db(self, config_id: str):
        """从数据库删除配置"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM config_center WHERE config_id = ?', (config_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配置] 删除配置失败: {e}")
    
    def watch(self, callback: Callable, keys: List[str] = None,
              namespace: str = 'default'):
        """监听配置变化"""
        watcher = ConfigWatcher(callback, keys, namespace)
        self.watchers.append(watcher)
        logger(f"[配置] 注册监听器: namespace={namespace}, keys={keys}")
    
    def _notify_watchers(self, key: str, value: Any, namespace: str):
        """通知监听器"""
        for watcher in self.watchers:
            if watcher.namespace != namespace:
                continue
            
            if watcher.keys is None or key in watcher.keys:
                try:
                    watcher.callback(key, value, namespace)
                except Exception as e:
                    logger(f"[配置] 通知监听器失败: {e}")
    
    def reload(self):
        """重新加载所有配置"""
        self._load_configs_from_db()
        logger(f"[配置] 重新加载配置完成，共 {len(self.configs)} 项")
    
    def batch_set(self, configs: Dict[str, Any], namespace: str = 'default',
                  changed_by: str = '', change_reason: str = ''):
        """批量设置配置"""
        for key, value in configs.items():
            self.set(key, value, namespace=namespace,
                     changed_by=changed_by, change_reason=change_reason)
    
    def get_config_history(self, key: str = None, namespace: str = 'default',
                          limit: int = 50) -> List[Dict[str, Any]]:
        """获取配置变更历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM config_history WHERE 1=1'
            params = []
            
            if key:
                query += ' AND key = ?'
                params.append(key)
            
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
            logger(f"[配置] 获取变更历史失败: {e}")
            return []
    
    def get_namespaces(self) -> List[str]:
        """获取所有命名空间"""
        namespaces = set()
        
        for config in self.configs.values():
            namespaces.add(config.namespace)
        
        return sorted(list(namespaces))
    
    def get_configs(self, namespace: str = None) -> List[ConfigItem]:
        """获取配置列表"""
        if namespace:
            return [c for c in self.configs.values() if c.namespace == namespace]
        return list(self.configs.values())
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_configs': len(self.configs),
            'total_namespaces': len(self.get_namespaces()),
            'total_watchers': len(self.watchers)
        }
    
    def start(self):
        """启动配置中心服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[配置] 配置中心服务已启动")
    
    def stop(self):
        """停止配置中心服务"""
        self.is_running = False
        logger(f"[配置] 配置中心服务已停止")

config_center_service = ConfigCenterService()
