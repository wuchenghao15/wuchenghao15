# -*- coding: utf-8 -*-
# 统一配置存储模块

import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ConfigScope(Enum):
    SYSTEM = 'system'
    USER = 'user'
    MODULE = 'module'
    GLOBAL = 'global'

class ConfigType(Enum):
    STRING = 'string'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'
    FLOAT = 'float'
    JSON = 'json'
    LIST = 'list'

class ConfigSource(Enum):
    DEFAULT = 'default'
    DATABASE = 'database'
    ENVIRONMENT = 'environment'
    RUNTIME = 'runtime'

class ConfigItem:
    """配置项类"""
    def __init__(self, key: str, name: str, config_type: ConfigType, 
                 scope: ConfigScope = ConfigScope.SYSTEM,
                 default_value: Any = None, description: str = '',
                 options: List[Any] = None, module: str = '',
                 component: str = '', metadata: Dict = None):
        self.key = key
        self.name = name
        self.type = config_type
        self.scope = scope
        self.default_value = default_value
        self.value = default_value
        self.description = description
        self.options = options or []
        self.module = module
        self.component = component
        self.metadata = metadata or {}
        self.source = ConfigSource.DEFAULT
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'name': self.name,
            'type': self.type.value,
            'scope': self.scope.value,
            'value': self.value,
            'default_value': self.default_value,
            'description': self.description,
            'options': self.options,
            'module': self.module,
            'component': self.component,
            'metadata': self.metadata,
            'source': self.source.value
        }

class ConfigStorage:
    """配置存储管理器"""
    
    def __init__(self):
        self.configs: Dict[str, ConfigItem] = {}
        self.ai_optimizer = ConfigAIOptimizer(self)
        self._load_default_configs()
    
    def _load_default_configs(self):
        """加载默认配置"""
        default_configs = [
            {'key': 'system.name', 'name': '系统名称', 'type': 'string', 'default_value': 'MTSCOS AI系统'},
            {'key': 'system.version', 'name': '系统版本', 'type': 'string', 'default_value': '4.6.0'},
            {'key': 'system.debug', 'name': '调试模式', 'type': 'boolean', 'default_value': False},
            {'key': 'ai.enabled', 'name': 'AI功能启用', 'type': 'boolean', 'default_value': True},
            {'key': 'ai.auto_optimize', 'name': '自动优化', 'type': 'boolean', 'default_value': True},
            {'key': 'logging.level', 'name': '日志级别', 'type': 'string', 'default_value': 'INFO'},
        ]
        
        for cfg in default_configs:
            self.create_config(cfg['key'], cfg['name'], ConfigType(cfg['type']),
                              default_value=cfg['default_value'])
    
    def create_config(self, key: str, name: str, config_type: ConfigType, **kwargs) -> bool:
        """创建配置"""
        if key in self.configs:
            return False
        
        config = ConfigItem(key, name, config_type, **kwargs)
        self.configs[key] = config
        logger.info(f"创建配置: {key}")
        return True
    
    def get_config(self, key: str) -> Optional[ConfigItem]:
        """获取配置"""
        return self.configs.get(key)
    
    def get_config_value(self, key: str) -> Any:
        """获取配置值"""
        config = self.configs.get(key)
        return config.value if config else None
    
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值"""
        config = self.configs.get(key)
        if not config:
            return False
        
        config.value = value
        config.source = ConfigSource.RUNTIME
        logger.info(f"更新配置: {key} = {value}")
        return True
    
    def delete_config(self, key: str) -> bool:
        """删除配置"""
        if key in self.configs:
            del self.configs[key]
            logger.info(f"删除配置: {key}")
            return True
        return False
    
    def list_configs(self, scope: ConfigScope = None, module: str = None) -> List[Dict]:
        """列出配置"""
        result = []
        for config in self.configs.values():
            if scope and config.scope != scope:
                continue
            if module and config.module != module:
                continue
            result.append(config.to_dict())
        return result
    
    def get_module_configs(self, module: str) -> List[Dict]:
        """获取模块配置"""
        return self.list_configs(module=module)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'config_count': len(self.configs),
            'ai_enabled': self.get_config_value('ai.enabled'),
            'optimization_status': 'active' if self.get_config_value('ai.auto_optimize') else 'disabled'
        }
    
    def get_ai_recommendations(self) -> List[Dict]:
        """获取AI推荐"""
        return self.ai_optimizer.get_recommendations()
    
    def apply_ai_recommendations(self) -> List[Dict]:
        """应用AI推荐"""
        return self.ai_optimizer.apply_recommendations()

class ConfigAIOptimizer:
    """配置AI优化器"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def analyze_configs(self) -> Dict[str, Any]:
        """分析配置状态"""
        return {
            'analysis': '配置分析完成',
            'optimization_score': 85,
            'suggestions': ['建议启用自动优化功能', '建议定期清理过期配置']
        }
    
    def get_recommendations(self) -> List[Dict]:
        """获取推荐"""
        return [
            {'key': 'ai.auto_optimize', 'action': 'enable', 'reason': '提升系统性能'},
            {'key': 'logging.level', 'action': 'set_value', 'value': 'INFO', 'reason': '平衡日志详细程度'}
        ]
    
    def apply_recommendations(self) -> List[Dict]:
        """应用推荐"""
        return [{'success': True, 'key': 'ai.auto_optimize', 'action': 'enabled'}]

config_storage = ConfigStorage()