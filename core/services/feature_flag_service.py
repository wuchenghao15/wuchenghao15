#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS特性开关服务 提供功能开关和动态配置管理 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print

class FeatureFlag:
    """特性开关"""
    
    def __init__(self, flag_id: str, name: str, description: str = '',
                 enabled: bool = False, rollout_percentage: float = 0.0,
                 target_users: List[str] = None, target_roles: List[str] = None,
                 target_groups: List[str] = None, environment: str = 'all',
                 expires_at: str = None, created_at: str = None):
        self.flag_id = flag_id
        self.name = name
        self.description = description
        self.enabled = enabled
        self.rollout_percentage = rollout_percentage
        self.target_users = target_users or []
        self.target_roles = target_roles or []
        self.target_groups = target_groups or []
        self.environment = environment
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        self.access_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'flag_id': self.flag_id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'rollout_percentage': self.rollout_percentage,
            'target_users': self.target_users,
            'target_roles': self.target_roles,
            'target_groups': self.target_groups,
            'environment': self.environment,
            'expires_at': self.expires_at,
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'access_count': self.access_count
        }

class DynamicConfig:
    """动态配置"""
    
    def __init__(self, config_id: str, name: str, value: Any,
                 description: str = '', config_type: str = 'string',
                 environment: str = 'all', created_at: str = None):
        self.config_id = config_id
        self.name = name
        self.value = value
        self.description = description
        self.config_type = config_type
        self.environment = environment
        self.created_at = created_at or datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        self.access_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'config_id': self.config_id,
            'name': self.name,
            'value': self.value,
            'description': self.description,
            'config_type': self.config_type,
            'environment': self.environment,
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'access_count': self.access_count
        }

class FeatureFlagService:
    """特性开关服务"""
    
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self.configs: Dict[str, DynamicConfig] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._register_default_flags()
        self._register_default_configs()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'feature_flag_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'cache_ttl': 300,
            'default_environment': 'production',
            'auto_refresh_enabled': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'feature_flag_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS feature_flags ( id INTEGER PRIMARY KEY AUTOINCREMENT, flag_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, description TEXT, enabled INTEGER DEFAULT 0, rollout_percentage REAL DEFAULT 0.0, target_users TEXT, target_roles TEXT, target_groups TEXT, environment TEXT DEFAULT 'all', expires_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, last_modified TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS dynamic_configs ( id INTEGER PRIMARY KEY AUTOINCREMENT, config_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, value TEXT, description TEXT, config_type TEXT DEFAULT 'string', environment TEXT DEFAULT 'all', created_at TEXT DEFAULT CURRENT_TIMESTAMP, last_modified TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS flag_access_logs ( id INTEGER PRIMARY KEY AUTOINCREMENT, flag_id TEXT NOT NULL, user_id TEXT, user_role TEXT, environment TEXT, result INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_feature_flags_id ON feature_flags(flag_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_dynamic_configs_id ON dynamic_configs(config_id) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[特性] 初始化数据库失败: {e}")
    
    def _register_default_flags(self):
        """注册默认特性开关"""
        default_flags = [
            FeatureFlag('new_ui', '新界面', '启用新的UI设计', False, 0),
            FeatureFlag('ai_assistant', 'AI助手', '启用AI助手功能', True, 100),
            FeatureFlag('dark_mode', '暗色模式', '启用暗色主题', True, 100),
            FeatureFlag('real_time_notifications', '实时通知', '启用WebSocket实时通知', True, 100),
            FeatureFlag('advanced_search', '高级搜索', '启用高级搜索功能', True, 100),
            FeatureFlag('data_export', '数据导出', '启用数据导出功能', True, 100),
            FeatureFlag('audit_logs', '审计日志', '启用审计日志', True, 100),
            FeatureFlag('multi_language', '多语言', '启用多语言支持', False, 0),
            FeatureFlag('mobile_app', '移动端适配', '启用移动端适配', True, 100),
            FeatureFlag('beta_features', 'Beta功能', '启用Beta测试功能', False, 0, [], ['admin'])
        ]
        
        for flag in default_flags:
            if flag.flag_id not in self.flags:
                self.flags[flag.flag_id] = flag
                self._save_flag_to_db(flag)
    
    def _register_default_configs(self):
        """注册默认动态配置"""
        default_configs = [
            DynamicConfig('app_name', '应用名称', 'MTSCOS AI', '系统应用名称', 'string'),
            DynamicConfig('app_version', '应用版本', '9.7.0', '系统版本号', 'string'),
            DynamicConfig('max_upload_size', '最大上传大小', '52428800', '最大文件上传大小(字节)', 'int'),
            DynamicConfig('session_timeout', '会话超时', '86400', '用户会话超时时间(秒)', 'int'),
            DynamicConfig('pagination_limit', '分页限制', '20', '默认分页大小', 'int'),
            DynamicConfig('max_search_results', '最大搜索结果', '100', '搜索最大返回数量', 'int'),
            DynamicConfig('cache_ttl', '缓存TTL', '300', '缓存过期时间(秒)', 'int'),
            DynamicConfig('log_level', '日志级别', 'INFO', '系统日志级别', 'string'),
            DynamicConfig('debug_mode', '调试模式', 'false', '是否启用调试模式', 'bool'),
            DynamicConfig('maintenance_mode', '维护模式', 'false', '是否启用维护模式', 'bool')
        ]
        
        for config in default_configs:
            if config.config_id not in self.configs:
                self.configs[config.config_id] = config
                self._save_config_to_db(config)
    
    def _generate_flag_id(self) -> str:
        """生成开关ID"""
        return f"flag_{int(time.time())}_{hash(os.urandom(16))}"
    
    def add_flag(self, name: str, description: str = '', enabled: bool = False,
                rollout_percentage: float = 0.0, target_users: List[str] = None,
                target_roles: List[str] = None, target_groups: List[str] = None,
                environment: str = 'all', expires_at: str = None) -> str:
        """添加特性开关"""
        flag_id = self._generate_flag_id()
        
        flag = FeatureFlag(
            flag_id=flag_id,
            name=name,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            target_users=target_users or [],
            target_roles=target_roles or [],
            target_groups=target_groups or [],
            environment=environment,
            expires_at=expires_at
        )
        
        with self.lock:
            self.flags[flag_id] = flag
        
        self._save_flag_to_db(flag)
        logger(f"[特性] 添加开关: {name}")
        
        return flag_id
    
    def _save_flag_to_db(self, flag: FeatureFlag):
        """保存开关到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO feature_flags (flag_id, name, description, enabled, rollout_percentage, target_users, target_roles, target_groups, environment, expires_at, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                flag.flag_id, flag.name, flag.description,
                1 if flag.enabled else 0, flag.rollout_percentage,
                json.dumps(flag.target_users),
                json.dumps(flag.target_roles),
                json.dumps(flag.target_groups),
                flag.environment, flag.expires_at,
                flag.last_modified
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[特性] 保存开关失败: {e}")
    
    def update_flag(self, flag_id: str, **kwargs) -> bool:
        """更新特性开关"""
        with self.lock:
            if flag_id not in self.flags:
                logger(f"[特性] 开关不存在: {flag_id}")
                return False
            
            flag = self.flags[flag_id]
            
            if 'name' in kwargs:
                flag.name = kwargs['name']
            if 'description' in kwargs:
                flag.description = kwargs['description']
            if 'enabled' in kwargs:
                flag.enabled = kwargs['enabled']
            if 'rollout_percentage' in kwargs:
                flag.rollout_percentage = kwargs['rollout_percentage']
            if 'target_users' in kwargs:
                flag.target_users = kwargs['target_users']
            if 'target_roles' in kwargs:
                flag.target_roles = kwargs['target_roles']
            if 'target_groups' in kwargs:
                flag.target_groups = kwargs['target_groups']
            if 'environment' in kwargs:
                flag.environment = kwargs['environment']
            if 'expires_at' in kwargs:
                flag.expires_at = kwargs['expires_at']
            
            flag.last_modified = datetime.now().isoformat()
        
        self._save_flag_to_db(flag)
        logger(f"[特性] 更新开关: {flag_id}")
        
        return True
    
    def remove_flag(self, flag_id: str) -> bool:
        """删除特性开关"""
        with self.lock:
            if flag_id not in self.flags:
                logger(f"[特性] 开关不存在: {flag_id}")
                return False
            
            del self.flags[flag_id]
        
        self._delete_flag_from_db(flag_id)
        logger(f"[特性] 删除开关: {flag_id}")
        
        return True
    
    def _delete_flag_from_db(self, flag_id: str):
        """从数据库删除开关"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM feature_flags WHERE flag_id = ?', (flag_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[特性] 删除开关失败: {e}")
    
    def is_enabled(self, flag_id: str, user_id: str = None, user_role: str = None,
                  user_group: str = None, environment: str = None) -> bool:
        """检查开关是否启用"""
        if not self.config['enabled']:
            return False
        
        flag = self.flags.get(flag_id)
        
        if not flag:
            return False
        
        if not flag.enabled:
            return False
        
        if flag.expires_at and datetime.now().isoformat() > flag.expires_at:
            return False
        
        if flag.environment != 'all' and environment and flag.environment != environment:
            return False
        
        if user_role and flag.target_roles and user_role in flag.target_roles:
            flag.access_count += 1
            self._log_flag_access(flag_id, user_id, user_role, environment, True)
            return True
        
        if user_group and flag.target_groups and user_group in flag.target_groups:
            flag.access_count += 1
            self._log_flag_access(flag_id, user_id, user_role, environment, True)
            return True
        
        if user_id and flag.target_users and user_id in flag.target_users:
            flag.access_count += 1
            self._log_flag_access(flag_id, user_id, user_role, environment, True)
            return True
        
        if flag.target_users or flag.target_roles or flag.target_groups:
            flag.access_count += 1
            self._log_flag_access(flag_id, user_id, user_role, environment, False)
            return False
        
        if flag.rollout_percentage > 0:
            import random
            if random.random() * 100 <= flag.rollout_percentage:
                flag.access_count += 1
                self._log_flag_access(flag_id, user_id, user_role, environment, True)
                return True
        
        flag.access_count += 1
        self._log_flag_access(flag_id, user_id, user_role, environment, flag.rollout_percentage >= 100)
        return flag.rollout_percentage >= 100
    
    def _log_flag_access(self, flag_id: str, user_id: str, user_role: str,
                        environment: str, result: bool):
        """记录开关访问日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO flag_access_logs (flag_id, user_id, user_role, environment, result) VALUES (?, ?, ?, ?, ?) ''', (flag_id, user_id or '', user_role or '', environment or '', 1 if result else 0))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[特性] 记录访问日志失败: {e}")
    
    def set_config(self, config_id: str, value: Any):
        """设置动态配置"""
        with self.lock:
            if config_id not in self.configs:
                logger(f"[特性] 配置不存在: {config_id}")
                return False
            
            config = self.configs[config_id]
            config.value = str(value)
            config.last_modified = datetime.now().isoformat()
        
        self._save_config_to_db(config)
        logger(f"[特性] 更新配置: {config_id} = {value}")
        
        return True
    
    def get_config(self, config_id: str, default: Any = None) -> Any:
        """获取动态配置"""
        config = self.configs.get(config_id)
        
        if not config:
            return default
        
        config.access_count += 1
        
        try:
            if config.config_type == 'int':
                return int(config.value)
            elif config.config_type == 'float':
                return float(config.value)
            elif config.config_type == 'bool':
                return config.value.lower() == 'true'
            elif config.config_type == 'json':
                return json.loads(config.value)
            else:
                return config.value
        except:
            return config.value
    
    def add_config(self, name: str, value: Any, description: str = '',
                  config_type: str = 'string', environment: str = 'all') -> str:
        """添加动态配置"""
        config_id = f"config_{int(time.time())}_{hash(os.urandom(16))}"
        
        config = DynamicConfig(
            config_id=config_id,
            name=name,
            value=str(value),
            description=description,
            config_type=config_type,
            environment=environment
        )
        
        with self.lock:
            self.configs[config_id] = config
        
        self._save_config_to_db(config)
        logger(f"[特性] 添加配置: {name}")
        
        return config_id
    
    def _save_config_to_db(self, config: DynamicConfig):
        """保存配置到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO dynamic_configs (config_id, name, value, description, config_type, environment, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (
                config.config_id, config.name, config.value,
                config.description, config.config_type,
                config.environment, config.last_modified
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[特性] 保存配置失败: {e}")
    
    def remove_config(self, config_id: str) -> bool:
        """删除动态配置"""
        with self.lock:
            if config_id not in self.configs:
                logger(f"[特性] 配置不存在: {config_id}")
                return False
            
            del self.configs[config_id]
        
        self._delete_config_from_db(config_id)
        logger(f"[特性] 删除配置: {config_id}")
        
        return True
    
    def _delete_config_from_db(self, config_id: str):
        """从数据库删除配置"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM dynamic_configs WHERE config_id = ?', (config_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[特性] 删除配置失败: {e}")
    
    def get_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """获取开关"""
        return self.flags.get(flag_id)
    
    def get_flags(self, enabled_only: bool = False) -> List[FeatureFlag]:
        """获取开关列表"""
        with self.lock:
            if enabled_only:
                return [f for f in self.flags.values() if f.enabled]
            return list(self.flags.values())
    
    def get_configs(self) -> List[DynamicConfig]:
        """获取配置列表"""
        with self.lock:
            return list(self.configs.values())
    
    def get_flag_stats(self, flag_id: str = None) -> Dict[str, Any]:
        """获取开关统计"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) as total, SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as enabled_count FROM flag_access_logs'
            params = []
            
            if flag_id:
                query += ' WHERE flag_id = ?'
                params.append(flag_id)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_access': row[0] or 0,
                'enabled_count': row[1] or 0,
                'enabled_rate': round((row[1] or 0) / max(1, row[0] or 1) * 100, 2)
            }
        except Exception as e:
            logger(f"[特性] 获取统计失败: {e}")
            return {'total_access': 0, 'enabled_count': 0, 'enabled_rate': 0.0}
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            enabled_flags = sum(1 for f in self.flags.values() if f.enabled)
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'enabled': self.config['enabled'],
                'total_flags': len(self.flags),
                'enabled_flags': enabled_flags,
                'total_configs': len(self.configs),
                'cache_ttl': self.config['cache_ttl'],
                'auto_refresh_enabled': self.config['auto_refresh_enabled']
            }
    
    def start(self):
        """启动特性开关服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[特性] 特性开关服务已启动")
    
    def stop(self):
        """停止特性开关服务"""
        self.is_running = False
        logger(f"[特性] 特性开关服务已停止")

feature_flag_service = FeatureFlagService()

