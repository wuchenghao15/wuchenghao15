# -*- coding: utf-8 -*-
"""
MTSCOS AI 配置模块
"""

import sys
import os
from typing import Dict, Any

try:
    import importlib.util
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
    if os.path.exists(config_path):
        spec = importlib.util.spec_from_file_location("app_config_module", config_path)
        app_config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_config_module)
        load_config = app_config_module.load_config
        get_config = getattr(app_config_module, 'get_config', None)
        get_config_value = getattr(app_config_module, 'get_config_value', None)
        get_config_category = getattr(app_config_module, 'get_config_category', None)
        update_config = getattr(app_config_module, 'update_config', None)
        delete_config = getattr(app_config_module, 'delete_config', None)
        get_all_configs = getattr(app_config_module, 'get_all_configs', None)
        get_all_configs_with_category = getattr(app_config_module, 'get_all_configs_with_category', None)
        refresh_config = getattr(app_config_module, 'refresh_config', None)
        init_database_config = getattr(app_config_module, 'init_database_config', None)
        app_config = getattr(app_config_module, 'app_config', {})
    else:
        def load_config(config_type=None):
            return {}
        get_config = None
        get_config_value = None
        get_config_category = None
        update_config = None
        delete_config = None
        get_all_configs = None
        get_all_configs_with_category = None
        refresh_config = None
        init_database_config = None
        app_config = {}
except Exception:
    def load_config(config_type=None):
        return {}
    get_config = None
    get_config_value = None
    get_config_category = None
    update_config = None
    delete_config = None
    get_all_configs = None
    get_all_configs_with_category = None
    refresh_config = None
    init_database_config = None
    app_config = {}


class ConfigMeta(type):
    """配置元类，支持动态属性访问"""
    
    def __getattr__(cls, name):
        if name in app_config:
            return app_config[name]
        if name.endswith('_CONFIG'):
            return {}
        raise AttributeError(f"type object 'Config' has no attribute '{name}'")


class Config(metaclass=ConfigMeta):
    """配置类，用于兼容旧版蓝图导入"""
    
    DEBUG = app_config.get('DEBUG', False)
    TESTING = app_config.get('TESTING', False)
    SECRET_KEY = app_config.get('SECRET_KEY', 'mtscos-secret-key')
    DATABASE_PATH = app_config.get('DATABASE_PATH', 'app.db')
    UPLOAD_FOLDER = app_config.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = app_config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    
    NETWORK_CONFIG = app_config.get('NETWORK_CONFIG', {
        'RATE_LIMIT_PER_IP': 60,
        'RATE_LIMIT_WINDOW': 60,
        'ENABLED': True,
        'SECURITY_ENABLED': True
    })
    AI_CONFIG = app_config.get('AI_CONFIG', {})
    MONITORING_CONFIG = app_config.get('MONITORING_CONFIG', {})
    EXAM_CONFIG = app_config.get('EXAM_CONFIG', {})
    CACHE_CONFIG = app_config.get('CACHE_CONFIG', {})
    SECURITY_CONFIG = app_config.get('SECURITY_CONFIG', {})
    LOGGING_CONFIG = app_config.get('LOGGING_CONFIG', {})
    
    RATE_LIMIT_PER_IP = app_config.get('RATE_LIMIT_PER_IP', 60)
    RATE_LIMIT_WINDOW = app_config.get('RATE_LIMIT_WINDOW', 60)
    MAX_LOGIN_ATTEMPTS = app_config.get('MAX_LOGIN_ATTEMPTS', 5)
    LOCKOUT_DURATION = app_config.get('LOCKOUT_DURATION', 300)
    SESSION_TIMEOUT = app_config.get('SESSION_TIMEOUT', 3600)
    MAX_FILE_SIZE = app_config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)
    ALLOWED_EXTENSIONS = app_config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'pdf'})
    ENABLE_AI = app_config.get('ENABLE_AI', True)
    ENABLE_CACHE = app_config.get('ENABLE_CACHE', True)
    ENABLE_LOGGING = app_config.get('ENABLE_LOGGING', True)
    ENABLE_MONITORING = app_config.get('ENABLE_MONITORING', True)
    ENABLE_SECURITY = app_config.get('ENABLE_SECURITY', True)
    
    @staticmethod
    def get(name: str, default=None):
        return app_config.get(name, default)
    
    @classmethod
    def init_app(cls, app):
        for key, value in app_config.items():
            if not hasattr(cls, key):
                setattr(cls, key, value)

# 导入统一规则配置
from .unified_rules import (
    EXAM_SYSTEM_ROUTES,
    TEST_SYSTEM_ROUTES,
    LEARNING_SYSTEM_ROUTES,
    USER_SYSTEM_ROUTES,
    ADMIN_SYSTEM_ROUTES,
    ROLE_HIERARCHY,
    ROLE_DESCRIPTIONS,
    SYSTEM_RULES,
    DATA_SECURITY_RULES,
    PERMISSION_RULES,
    check_route_permission,
    check_permission_by_rule,
    get_role_level,
    is_role_higher_than,
    get_system_rule,
    init_unified_rules
)

__all__ = [
    'load_config',
    'get_config',
    'get_config_value',
    'get_config_category',
    'update_config',
    'delete_config',
    'get_all_configs',
    'get_all_configs_with_category',
    'refresh_config',
    'init_database_config',
    'Config',
    'EXAM_SYSTEM_ROUTES',
    'TEST_SYSTEM_ROUTES',
    'LEARNING_SYSTEM_ROUTES',
    'USER_SYSTEM_ROUTES',
    'ADMIN_SYSTEM_ROUTES',
    'ROLE_HIERARCHY',
    'ROLE_DESCRIPTIONS',
    'SYSTEM_RULES',
    'DATA_SECURITY_RULES',
    'PERMISSION_RULES',
    'check_route_permission',
    'check_permission_by_rule',
    'get_role_level',
    'is_role_higher_than',
    'get_system_rule',
    'init_unified_rules'
]