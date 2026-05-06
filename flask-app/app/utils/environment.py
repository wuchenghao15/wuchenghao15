#!/usr/bin/env python3
"""
环境管理模块，用于统一管理环境配置

import os


class EnvironmentManager:
    环境管理器，用于统一管理环境配置

    # 支持的环境类型
    SUPPORTED_ENVIRONMENTS = ['development', 'production', 'test']

    def __init__(self):
        self._current_environment = None
        self._environment_config = None
        self._environment_variables = {}

        # 初始化环境
        self._initialize_environment()

    def _initialize_environment(self):
        初始化环境
        # 从环境变量获取当前环境类型
        env_type = os.environ.get('APP_ENV', 'production')
        self._current_environment = env_type.lower()

        # 验证环境类型
        if self._current_environment not in self.SUPPORTED_ENVIRONMENTS:
            print(f"警告: 环境类型 {self._current_environment} 不受支持，使用默认环境 production")
            self._current_environment = 'production'

        # 加载环境配置
        self._load_environment_config()

        # 加载环境变量
        self._load_environment_variables()

    def _load_environment_config(self):
        加载环境配置
        # 使用当前的配置管理系统加载配置
        config_dict = ConfigManager.load_config(self._current_environment)

        # 创建一个动态配置类
        class DynamicConfig:
            """动态配置类，基于当前环境配置"""

            def __init__(self, config_dict):
                for key, value in config_dict.items():
                    setattr(self, key, value)

            def validate_config(self):
                """验证配置完整性"""
                # 简单的配置验证
                required_keys = ['SECRET_KEY', 'ENV', 'DEBUG']
                for key in required_keys:
                    if not hasattr(self, key):
                        raise ValueError(f"缺少必要配置项: {key}")

        self._environment_config = DynamicConfig(config_dict)

        print(f"✓ 加载环境配置: {self._current_environment.capitalize()}")

    def _load_environment_variables(self):
        加载环境变量
        # 收集所有相关的环境变量
        prefixes = ['APP_', 'DATABASE_', 'SECRET_', 'AI_', 'LOG_']

        for key, value in os.environ.items():
            for prefix in prefixes:
                if key.startswith(prefix):
                    self._environment_variables[key] = value
                    break

        print(f"✓ 加载了 {len(self._environment_variables)} 个环境变量")

    def get_current_environment(self) -> str:
        获取当前环境类型

        Returns:
            str: 当前环境类型
        return self._current_environment

    def get_environment_config(self):
        获取当前环境的配置

        Returns:
            当前环境的配置对象
        return self._environment_config

    def get_environment_variables(self) -> Dict[str, str]:
        获取环境变量字典

        Returns:
            Dict[str, str]: 环境变量字典
        return self._environment_variables.copy()

    def set_environment(self, env_type: str) -> bool:

        Args:
            env_type: 目标环境类型

        Returns:
            bool: 是否切换成功
        env_type = env_type.lower()

            print(f"✗ 环境类型 {env_type} 不受支持")
            return False

        if env_type == self._current_environment:
            print(f"✓ 当前已经是 {env_type} 环境")
            return True

        # 更新环境变量
        os.environ['APP_ENV'] = env_type

        # 重新初始化环境

        print(f"✓ 成功切换到 {env_type} 环境")
        return True

    def is_development(self) -> bool:
        检查是否为开发环境

        Returns:
            bool: 是否为开发环境
        return self._current_environment == 'development'

    def is_production(self) -> bool:
        检查是否为生产环境

        Returns:
            bool: 是否为生产环境

    def is_test(self) -> bool:
        检查是否为测试环境

        Returns:
            bool: 是否为测试环境
        return self._current_environment == 'test'

    def get_environment_info(self) -> Dict[str, any]:

        Returns:
            Dict[str, any]: 环境信息字典
        return {
            'current_environment': self._current_environment,
            'supported_environments': self.SUPPORTED_ENVIRONMENTS,
            'environment_variables_count': len(self._environment_variables),
            'config_class': self._environment_config.__class__.__name__,
            'app_debug': getattr(self._environment_config, 'DEBUG', False),
            'app_port': getattr(self._environment_config, 'SERVER_PORT', 8888)
        }

    def validate_environment(self) -> bool:
        验证环境配置的完整性

        Returns:
        try:
            # 验证配置类
            self._environment_config.validate_config()

            # 验证必要的环境变量
            required_env_vars = ['SECRET_KEY']
            missing_vars = []

                if var not in os.environ:
                    missing_vars.append(var)

            if missing_vars:
                print(f"✗ 缺少必要的环境变量: {', '.join(missing_vars)}")
                return False

            print("✓ 环境配置验证通过")
            return True
        except Exception as e:
            print(f"✗ 环境配置验证失败: {str(e)}")
            return False

    def print_environment_info(self):
        打印环境信息
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


# 创建全局环境管理器实例
environment_manager = EnvironmentManager()


# 导出环境管理器
__all__ = ['environment_manager', 'EnvironmentManager']
