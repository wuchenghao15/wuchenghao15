# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
环境管理模块
用于统一管理环境配置
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    @staticmethod
    def load_config(env_type: str) -> dict:
        """加载配置"""
        return {
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key'),
            'ENV': env_type,
            'DEBUG': env_type == 'development'
        }


class EnvironmentManager:
    """环境管理器: 用于统一管理环境配置"""

    SUPPORTED_ENVIRONMENTS = ['development', 'production', 'test']

    def __init__(self):
        self._current_environment = None
        self._environment_config = None
        self._environment_variables = {}
        self._initialize_environment()

    def _initialize_environment(self):
        """初始化环境"""
        env_type = os.environ.get('APP_ENV', 'production')
        self._current_environment = env_type.lower()

        if self._current_environment not in self.SUPPORTED_ENVIRONMENTS:
            print(f"警告: 环境类型 {self._current_environment} 不受支持,使用默认环境 production")
            self._current_environment = 'production'

        self._load_environment_config()
        self._load_environment_variables()

    def _load_environment_config(self):
        """加载环境配置"""
        config_dict = ConfigManager.load_config(self._current_environment)

        class DynamicConfig:
            """动态配置类: 基于当前环境配置"""

            def __init__(self, config_dict):
                for key, value in config_dict.items():
                    setattr(self, key, value)

            def validate_config(self):
                """验证配置完整性"""
                required_keys = ['SECRET_KEY', 'ENV', 'DEBUG']
                for key in required_keys:
                    if not hasattr(self, key):
                        raise ValueError(f"缺少必要配置项: {key}")

        self._environment_config = DynamicConfig(config_dict)
        print(f"✓ 加载环境配置: {self._current_environment.capitalize()}")

    def _load_environment_variables(self):
        """加载环境变量"""
        prefixes = ['APP_', 'DATABASE_', 'SECRET_', 'AI_', 'LOG_']

        for key, value in os.environ.items():
            for prefix in prefixes:
                if key.startswith(prefix):
                    self._environment_variables[key] = value
                    break

        print(f"✓ 加载了 {len(self._environment_variables)} 个环境变量")

    def get_current_environment(self) -> str:
        """获取当前环境类型

        Returns:
            str: 当前环境类型
        """
        return self._current_environment

    def get_environment_config(self):
        """获取当前环境的配置

        Returns:
            当前环境的配置对象
        """
        return self._environment_config

    def get_environment_info(self) -> dict:
        """获取环境信息"""
        return {
            'current_environment': self._current_environment,
            'supported_environments': self.SUPPORTED_ENVIRONMENTS,
            'config_class': type(self._environment_config).__name__,
            'python_version': sys.version,
            'app_debug': getattr(self._environment_config, 'DEBUG', False),
            'app_port': os.environ.get('PORT', '5000'),
            'environment_variables_count': len(self._environment_variables)
        }

    def print_environment_info(self):
        """打印环境信息"""
        info = self.get_environment_info()
        print("=" * 50)
        print("环境信息")
        print("=" * 50)
        print(f"当前环境: {info['current_environment']}")
        print(f"支持的环境: {', '.join(info['supported_environments'])}")
        print(f"配置类: {info['config_class']}")
        print(f"Python版本: {info['python_version']}")
        print(f"调试模式: {'开启' if info['app_debug'] else '关闭'}")
        print(f"应用端口: {info['app_port']}")
        print(f"环境变量数量: {info['environment_variables_count']}")
        print("=" * 50)


environment_manager = EnvironmentManager()

__all__ = ['environment_manager', 'EnvironmentManager']
