# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置存储系统
Unified Configuration Storage System

特性:
- 配置变更追踪
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict
import threading
import logging

logger = logging.getLogger('config_storage')


class ConfigScope(Enum):
    """配置作用域"""
    SYSTEM = "system"           # 系统级配置
    MODULE = "module"           # 模块级配置
    COMPONENT = "component"     # 组件级配置
    USER = "user"               # 用户级配置


class ConfigType(Enum):
    """配置类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    JSON = "json"


class ConfigSource(Enum):
    """配置来源"""
    DEFAULT = "default"         # 默认配置
    DATABASE = "database"       # 数据库配置
    AI_RECOMMENDED = "ai_recommended"  # AI推荐配置
    USER_CUSTOM = "user_custom" # 用户自定义配置


class SystemConfig:
    """系统配置项"""
    
    def __init__(self, key: str, name: str, config_type: ConfigType):
        self.key = key
        self.name = name
        self.type = config_type
        self.scope = ConfigScope.SYSTEM
        
        self.value = None
        self.default_value = None
        self.description = ""
        self.options = []
        
        self.source = ConfigSource.DEFAULT
        self.ai_score = 0.0
        self.ai_reason = ""
        
        self.module = None
        self.component = None
        
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.last_used_at = None
        
        self.version = "1.0.0"
        self.history = []
        
        self.metadata = {}
    
    def set_value(self, value, source: ConfigSource = ConfigSource.USER_CUSTOM):
        """设置值"""
        # 记录历史
        if self.value is not None:
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'value': self.value,
                'source': self.source.value
            })
            # 保留最近10条历史
            if len(self.history) > 10:
                self.history = self.history[-10:]
        
        self.value = value
        self.source = source
        self.updated_at = datetime.now().isoformat()
        
        return True
    
    def apply_ai_recommendation(self, value, score: float, reason: str):
        """应用AI推荐"""
        self.set_value(value, ConfigSource.AI_RECOMMENDED)
        self.ai_score = score
        self.ai_reason = reason
        
        logger.info(f"AI推荐应用: {self.key} -> {value} (评分: {score})")
    
    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'name': self.name,
            'type': self.type.value,
            'scope': self.scope.value,
            'value': self.value,
            'default_value': self.default_value,
            'description': self.description,
            'options': self.options,
            'source': self.source.value,
            'ai_score': self.ai_score,
            'ai_reason': self.ai_reason,
            'module': self.module,
            'component': self.component,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_used_at': self.last_used_at,
            'version': self.version,
            'history': self.history,
            'metadata': self.metadata
        }


class UnifiedConfigStorage:
    """统一配置存储系统"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config.db'
        )
        
        self.configs = {}
        self.modules = {}
        self.lock = threading.Lock()
        
        self._init_database()
        self._load_configs()
        self._register_default_configs()
        
        # AI配置优化器
        self.ai_optimizer = AIConfigOptimizer(self)
        
        # 配置缓存
        self.cache = {}
        self.cache_ttl = 300  # 5分钟
        
        logger.info("统一配置存储系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        import sqlite3
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    value TEXT,
                    default_value TEXT,
                    description TEXT,
                    options TEXT,
                    source TEXT NOT NULL,
                    ai_score REAL DEFAULT 0.0,
                    ai_reason TEXT,
                    module TEXT,
                    component TEXT,
                    version TEXT DEFAULT '1.0.0',
                    history TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_used_at TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_config_key ON system_configs (key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_config_scope ON system_configs (scope)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_config_module ON system_configs (module)')
            
            conn.commit()
    
    def _load_configs(self):
        """从数据库加载配置"""
        import sqlite3
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM system_configs')
                rows = cursor.fetchall()
                
                columns = [desc[0] for desc in cursor.description]
                
                for row in rows:
                    config_data = dict(zip(columns, row))
                    
                    config = SystemConfig(
                        config_data['key'],
                        config_data['name'],
                        ConfigType(config_data['type'])
                    )
                    
                    config.scope = ConfigScope(config_data['scope'])
                    config.source = ConfigSource(config_data['source'])
                    
                    # 解析JSON字段
                    if config_data['value']:
                        try:
                            config.value = json.loads(config_data['value'])
                        except Exception:
                            config.value = config_data['value']
                    
                    if config_data['default_value']:
                        try:
                            config.default_value = json.loads(config_data['default_value'])
                        except Exception:
                            config.default_value = config_data['default_value']
                    
                    if config_data['options']:
                        try:
                            config.options = json.loads(config_data['options'])
                        except Exception:
                            config.options = []
                    
                    if config_data['history']:
                        try:
                            config.history = json.loads(config_data['history'])
                        except Exception:
                            config.history = []
                    
                    if config_data['metadata']:
                        try:
                            config.metadata = json.loads(config_data['metadata'])
                        except Exception:
                            config.metadata = {}
                    
                    config.description = config_data['description']
                    config.ai_score = config_data['ai_score'] or 0.0
                    config.ai_reason = config_data['ai_reason'] or ""
                    config.module = config_data['module']
                    config.component = config_data['component']
                    config.version = config_data['version'] or "1.0.0"
                    config.created_at = config_data['created_at']
                    config.updated_at = config_data['updated_at']
                    config.last_used_at = config_data['last_used_at']
                    
                    self.configs[config.key] = config
            
            logger.info(f"从数据库加载了 {len(self.configs)} 个配置项")
        
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
    
    def _save_config_to_db(self, config: SystemConfig):
        """保存配置到数据库"""
        import sqlite3
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                value_json = json.dumps(config.value) if config.value is not None else None
                default_json = json.dumps(config.default_value) if config.default_value is not None else None
                options_json = json.dumps(config.options) if config.options else None
                history_json = json.dumps(config.history) if config.history else None
                metadata_json = json.dumps(config.metadata) if config.metadata else None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO system_configs (
                        key, name, type, scope, value, default_value, description,
                        options, source, ai_score, ai_reason, module, component,
                        version, history, metadata, created_at, updated_at, last_used_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    config.key, config.name, config.type.value, config.scope.value,
                    value_json, default_json, config.description,
                    options_json, config.source.value, config.ai_score, config.ai_reason,
                    config.module, config.component, config.version,
                    history_json, metadata_json, config.created_at,
                    config.updated_at, config.last_used_at
                ))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def _register_default_configs(self):
        """注册默认配置"""
        default_configs = [
            # AI服务配置
            {
                'key': 'ai.service_enabled',
                'name': 'AI服务启用',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用AI服务',
                'module': 'ai_service'
            },
            {
                'key': 'ai.auto_learning_enabled',
                'name': 'AI自动学习',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用AI自动学习',
                'module': 'ai_service'
            },
            {
                'key': 'ai.recommendation_enabled',
                'name': 'AI推荐',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用AI推荐功能',
                'module': 'ai_service'
            },
            # 自动升级配置
            {
                'key': 'auto_upgrade.enabled',
                'name': '自动升级',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用自动升级',
                'module': 'auto_upgrade'
            },
            {
                'key': 'auto_upgrade.check_interval',
                'name': '升级检查间隔',
                'type': ConfigType.INTEGER,
                'scope': ConfigScope.SYSTEM,
                'default_value': 3600,
                'description': '升级检查间隔(秒)',
                'module': 'auto_upgrade',
                'options': [1800, 3600, 7200, 86400]
            },
            # 备份配置
            {
                'key': 'backup.enabled',
                'name': '备份启用',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用备份',
                'module': 'backup'
            },
            {
                'key': 'backup.interval',
                'name': '备份间隔',
                'type': ConfigType.INTEGER,
                'scope': ConfigScope.SYSTEM,
                'default_value': 86400,
                'description': '备份间隔(秒)',
                'module': 'backup',
                'options': [3600, 7200, 86400, 172800]
            },
            {
                'key': 'backup.dual_backup',
                'name': '双备份',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用双备份',
                'module': 'backup'
            },
            # 证书配置
            {
                'key': 'certificate.auto_renew',
                'name': '证书自动续期',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用证书自动续期',
                'module': 'certificate'
            },
            # 任务配置
            {
                'key': 'task.auto_assignment',
                'name': '任务自动分配',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用任务自动分配',
                'module': 'task_center'
            },
            {
                'key': 'task.priority_threshold',
                'name': '任务优先级阈值',
                'type': ConfigType.INTEGER,
                'scope': ConfigScope.SYSTEM,
                'default_value': 3,
                'description': '任务优先级阈值',
                'module': 'task_center',
                'options': [1, 2, 3, 4, 5]
            },
            # 监控配置
            {
                'key': 'monitoring.enabled',
                'name': '监控启用',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用系统监控',
                'module': 'monitoring'
            },
            {
                'key': 'monitoring.check_interval',
                'name': '监控检查间隔',
                'type': ConfigType.INTEGER,
                'scope': ConfigScope.SYSTEM,
                'default_value': 60,
                'description': '监控检查间隔(秒)',
                'module': 'monitoring',
                'options': [10, 30, 60, 120]
            },
            # 数据矩阵配置
            {
                'key': 'matrix.enabled',
                'name': '数据矩阵',
                'type': ConfigType.BOOLEAN,
                'scope': ConfigScope.SYSTEM,
                'default_value': True,
                'description': '是否启用数据矩阵',
                'module': 'data_matrix'
            },
            {
                'key': 'matrix.refresh_interval',
                'name': '矩阵刷新间隔',
                'type': ConfigType.INTEGER,
                'scope': ConfigScope.SYSTEM,
                'default_value': 300,
                'description': '数据矩阵刷新间隔(秒)',
                'module': 'data_matrix',
                'options': [60, 120, 300, 600]
            },
        ]
        
        for config_data in default_configs:
            key = config_data['key']
            if key not in self.configs:
                config = SystemConfig(
                    key,
                    config_data['name'],
                    config_data['type']
                )
                
                config.scope = config_data['scope']
                config.default_value = config_data['default_value']
                config.value = config_data['default_value']
                config.description = config_data.get('description', '')
                config.module = config_data.get('module')
                config.options = config_data.get('options', [])
                config.source = ConfigSource.DEFAULT
                
                self.configs[key] = config
                self._save_config_to_db(config)
        
        logger.info(f"注册了 {len(default_configs)} 个默认配置")
    
    def get_config(self, key: str, use_cache: bool = True) -> Optional[SystemConfig]:
        """获取配置"""
        # 检查缓存
        if use_cache and key in self.cache:
            cached = self.cache[key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['config']
        
        config = self.configs.get(key)
        
        if config:
            config.last_used_at = datetime.now().isoformat()
            self._save_config_to_db(config)
            
            # 更新缓存
            self.cache[key] = {
                'timestamp': time.time(),
                'config': config
            }
        
        return config
    
    def get_config_value(self, key: str, default=None):
        """获取配置值"""
        config = self.get_config(key)
        if config:
            return config.value if config.value is not None else default
        return default
    
    def set_config(self, key: str, value, source: ConfigSource = ConfigSource.USER_CUSTOM) -> bool:
        """设置配置"""
        config = self.get_config(key)
        
        if not config:
            logger.error(f"配置不存在: {key}")
            return False
        
        config.set_value(value, source)
        
        # 保存到数据库
        self._save_config_to_db(config)
        
        # 更新缓存
        if key in self.cache:
            self.cache[key]['config'] = config
            self.cache[key]['timestamp'] = time.time()
        
        # 触发AI优化
        self.ai_optimizer.on_config_change(key, value)
        
        logger.info(f"配置更新: {key} -> {value}")
        return True
    
    def create_config(self, key: str, name: str, config_type: ConfigType, **kwargs) -> bool:
        """创建配置"""
        if key in self.configs:
            logger.error(f"配置已存在: {key}")
            return False
        
        config = SystemConfig(key, name, config_type)
        
        if 'scope' in kwargs:
            config.scope = kwargs['scope']
        if 'default_value' in kwargs:
            config.default_value = kwargs['default_value']
            config.value = kwargs['default_value']
        if 'description' in kwargs:
            config.description = kwargs['description']
        if 'options' in kwargs:
            config.options = kwargs['options']
        if 'module' in kwargs:
            config.module = kwargs['module']
        if 'component' in kwargs:
            config.component = kwargs['component']
        if 'metadata' in kwargs:
            config.metadata = kwargs['metadata']
        
        self.configs[key] = config
        self._save_config_to_db(config)
        
        logger.info(f"创建配置: {key}")
        return True
    
    def delete_config(self, key: str) -> bool:
        """删除配置"""
        if key not in self.configs:
            return False
        
        # 从数据库删除
        import sqlite3
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM system_configs WHERE key = ?', (key,))
                conn.commit()
        except Exception as e:
            logger.error(f"删除配置失败: {str(e)}")
            return False
        
        del self.configs[key]
        
        if key in self.cache:
            del self.cache[key]
        
        logger.info(f"删除配置: {key}")
        return True
    
    def list_configs(self, scope: ConfigScope = None, module: str = None) -> List[Dict]:
        """列出配置"""
        results = []
        
        for config in self.configs.values():
            if scope and config.scope != scope:
                continue
            if module and config.module != module:
                continue
            
            results.append(config.to_dict())
        
        return sorted(results, key=lambda x: x['key'])
    
    def get_module_configs(self, module: str) -> Dict:
        """获取模块配置"""
        configs = self.list_configs(module=module)
        result = {}
        for config in configs:
            result[config['key']] = config['value']
        return result
    
    def apply_ai_recommendations(self):
        """应用AI推荐"""
        recommendations = self.ai_optimizer.generate_recommendations()
        
        for key, rec in recommendations.items():
            config = self.get_config(key)
            if config:
                config.apply_ai_recommendation(rec['value'], rec['score'], rec['reason'])
                self._save_config_to_db(config)
        
        logger.info(f"应用了 {len(recommendations)} 个AI推荐")
        return recommendations
    
    def get_ai_recommendations(self) -> Dict:
        """获取AI推荐"""
        return self.ai_optimizer.generate_recommendations()
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        total_configs = len(self.configs)
        by_scope = defaultdict(int)
        by_module = defaultdict(int)
        ai_recommended = sum(1 for c in self.configs.values() if c.source == ConfigSource.AI_RECOMMENDED)
        
        for config in self.configs.values():
            by_scope[config.scope.value] += 1
            if config.module:
                by_module[config.module] += 1
        
        return {
            'total_configs': total_configs,
            'ai_recommended': ai_recommended,
            'by_scope': dict(by_scope),
            'by_module': dict(by_module),
            'ai_optimization_enabled': self.ai_optimizer.enabled
        }


class AIConfigOptimizer:
    """AI配置优化器"""
    
    def __init__(self, storage: UnifiedConfigStorage):
        self.storage = storage
        self.enabled = True
        
        # 配置匹配规则
        self.matching_rules = {
            'ai.auto_learning_enabled': {
                'dependencies': ['ai.service_enabled'],
                'condition': lambda c: c.get('ai.service_enabled') == True,
                'recommendation': True,
                'score': 0.9,
                'reason': 'AI服务已启用,建议启用自动学习以提升AI能力'
            },
            'ai.recommendation_enabled': {
                'dependencies': ['ai.auto_learning_enabled'],
                'condition': lambda c: c.get('ai.auto_learning_enabled') == True,
                'recommendation': True,
                'score': 0.95,
                'reason': 'AI自动学习已启用,建议启用AI推荐功能'
            },
            'backup.dual_backup': {
                'dependencies': ['backup.enabled'],
                'condition': lambda c: c.get('backup.enabled') == True,
                'recommendation': True,
                'score': 0.88,
                'reason': '备份已启用,建议启用双备份提高数据安全性'
            },
            'task.auto_assignment': {
                'dependencies': ['ai.service_enabled'],
                'condition': lambda c: c.get('ai.service_enabled') == True,
                'recommendation': True,
                'score': 0.85,
                'reason': 'AI服务已启用,建议启用任务自动分配'
            },
            'matrix.enabled': {
                'dependencies': ['ai.service_enabled'],
                'condition': lambda c: c.get('ai.service_enabled') == True,
                'recommendation': True,
                'score': 0.82,
                'reason': 'AI服务已启用,建议启用数据矩阵支持AI分析'
            },
        }
    
    def on_config_change(self, key: str, value):
        """配置变更时触发优化"""
        if not self.enabled:
            return
        
        recommendations = self.generate_recommendations()
        
        for rec_key, rec in recommendations.items():
            if rec['score'] > 0.8:
                config = self.storage.get_config(rec_key)
                if config and config.value != rec['value']:
                    logger.info(f"AI推荐配置: {rec_key} -> {rec['value']}")
    
    def generate_recommendations(self) -> Dict:
        """生成推荐"""
        recommendations = {}
        current_configs = self._get_current_configs_dict()
        
        for key, rule in self.matching_rules.items():
            if 'condition' in rule and not rule['condition'](current_configs):
                continue
            
            current_value = current_configs.get(key)
            if current_value == rule['recommendation']:
                continue
            
            recommendations[key] = {
                'value': rule['recommendation'],
                'score': rule['score'],
                'reason': rule['reason'],
                'current_value': current_value
            }
        
        return recommendations
    
    def _get_current_configs_dict(self) -> Dict:
        """获取当前配置字典"""
        return {
            key: config.value
            for key, config in self.storage.configs.items()
        }
    
    def analyze_configs(self) -> Dict:
        """分析配置状态"""
        current_configs = self._get_current_configs_dict()
        recommendations = self.generate_recommendations()
        
        total_rules = len(self.matching_rules)
        matched_rules = sum(
            1 for rule in self.matching_rules.values()
            if rule['condition'](current_configs)
        )
        
        return {
            'total_rules': total_rules,
            'matched_rules': matched_rules,
            'match_rate': matched_rules / total_rules * 100,
            'recommendations_count': len(recommendations),
            'recommendations': recommendations
        }


# 全局实例
config_storage = UnifiedConfigStorage()
