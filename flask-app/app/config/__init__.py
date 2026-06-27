# -*- coding: utf-8 -*-
"""
MTSCOS AI 配置模块
"""

# 从父目录的 config.py 模块导入 load_config
import sys
import os

# 导入父目录的 config.py 模块中的 load_config 函数
# 需要使用特殊方式导入，因为 app.config 包覆盖了 app.config.py 模块
try:
    # 尝试从 app 模块的 config 属性获取
    import importlib.util
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
    if os.path.exists(config_path):
        spec = importlib.util.spec_from_file_location("app_config_module", config_path)
        app_config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_config_module)
        load_config = app_config_module.load_config
        get_config = getattr(app_config_module, 'get_config', None)
    else:
        # 如果找不到，创建一个默认的 load_config 函数
        def load_config(config_type=None):
            return {}
        get_config = None
except Exception:
    def load_config(config_type=None):
        return {}
    get_config = None

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