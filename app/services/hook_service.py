#!/usr/bin/env python3
"""
MTSCOS Hook Service
===================
实现系统生命周期钩子系统，支持在应用启动、登录、退出等关键节点执行自定义逻辑。
"""
import os
import json
import logging
from datetime import datetime
from typing import Callable, Dict, List, Any

logger = logging.getLogger('HookService')


class HookService:
    """系统钩子服务"""
    
    def __init__(self):
        self._hooks: Dict[str, List[Dict[str, Any]]] = {}
        self._hook_handlers: Dict[str, List[Callable]] = {}
        self._config = self._load_config()
        self._initialized = False
        logger.info("[HookService] 初始化系统钩子服务")
    
    def _load_config(self) -> Dict:
        """加载hooks配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        '.trae-cn', 'hooks.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('mtscos', {})
        except Exception as e:
            logger.error(f"加载hooks配置失败: {e}")
        
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'enabled': True,
            'version': '1.0.0',
            'hooks': {
                'before_app_start': [],
                'after_app_start': [],
                'before_render': [],
                'after_login': [],
                'before_logout': [],
                'error_occurred': []
            },
            'config': {
                'particle_effects': {
                    'enabled': True,
                    'particles_count': 60
                },
                'glassmorphism': {
                    'enabled': True,
                    'blur_radius': '20px'
                }
            }
        }
    
    def register_hook(self, hook_name: str, handler: Callable, priority: int = 10):
        """注册钩子处理器"""
        if hook_name not in self._hook_handlers:
            self._hook_handlers[hook_name] = []
        
        self._hook_handlers[hook_name].append({
            'handler': handler,
            'priority': priority
        })
        
        self._hook_handlers[hook_name].sort(key=lambda x: x['priority'])
        logger.info(f"[HookService] 注册钩子: {hook_name}, 优先级: {priority}")
    
    def trigger_hook(self, hook_name: str, **kwargs) -> List[Any]:
        """触发钩子"""
        results = []
        
        if hook_name not in self._hook_handlers:
            return results
        
        logger.info(f"[HookService] 触发钩子: {hook_name}, 参数: {list(kwargs.keys())}")
        
        for item in self._hook_handlers[hook_name]:
            try:
                result = item['handler'](**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"[HookService] 钩子 {hook_name} 执行失败: {e}")
        
        return results
    
    def initialize(self):
        """初始化钩子系统"""
        if self._initialized:
            return
        
        logger.info("[HookService] 启动钩子系统初始化...")
        
        enabled_hooks = self._config.get('hooks', {})
        
        for hook_name, hooks in enabled_hooks.items():
            for hook in hooks:
                if hook.get('enabled', True):
                    logger.info(f"[HookService] 加载钩子配置: {hook['name']} ({hook_name})")
        
        self._initialized = True
        
        logger.info("[HookService] 钩子系统初始化完成")
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """获取配置"""
        if key is None:
            return self._config
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def is_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        config = self._config.get('config', {})
        feature_config = config.get(feature, {})
        return feature_config.get('enabled', False)


hook_service = HookService()


def init_hooks(app=None):
    """初始化系统钩子"""
    logger.info("[MTSCOS] 初始化系统钩子服务...")
    
    hook_service.initialize()
    
    if hook_service.is_enabled('particle_effects'):
        logger.info("[MTSCOS] ✓ 粒子效果功能已启用")
    
    if hook_service.is_enabled('glassmorphism'):
        logger.info("[MTSCOS] ✓ 毛玻璃效果功能已启用")
    
    return hook_service