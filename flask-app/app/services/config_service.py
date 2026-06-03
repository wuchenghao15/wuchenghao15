#!/usr/bin/env python3
"""
配置服务 - 用于从数据库加载和管理系统配置
"""

from app.models.system_config import SystemConfig
from app.utils.logging import logger


class ConfigService:
    """配置服务: 负责从数据库加载和管理系统配置"""

    _instance = None
    _config_cache = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置服务"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config_cache = {}

    def load_config_from_db(self):
        """从数据库加载所有配置"""
        logger.info("从数据库加载系统配置")

        try:
            configs = SystemConfig.get_all_configs()
            self._config_cache.clear()

            for config in configs:
                value = self._convert_config_value(config.config_value, config.config_type)
                self._config_cache[config.config_key] = value

            logger.info(f"成功从数据库加载 {len(self._config_cache)} 个配置项")
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
        return self._config_cache

    def _convert_config_value(self, value, config_type):
        """根据配置类型转换值"""
        try:
            if config_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif config_type == "integer":
                return int(value)
            elif config_type == "float":
                return float(value)
            elif config_type == "json":
                import json
                return json.loads(value)
            else:
                return value
        except Exception as e:
            logger.error(f"转换配置值失败: {str(e)}")
            return value

    def get_config(self, key, default=None):
        """获取配置值"""
        if not self._config_cache:
            self.load_config_from_db()
        return self._config_cache.get(key, default)

    def set_config(self, key, value, config_type="string", description=""):
        """设置配置值"""
        str_value = self._convert_to_string(value, config_type)

        config = SystemConfig.get_by_key(key)
        if config:
            config.config_value = str_value
            config.config_type = config_type
            config.description = description
            config.save()
        else:
            config = SystemConfig(
                config_key=key,
                config_value=str_value,
                config_type=config_type,
                description=description
            )
            config.save()

        self._config_cache[key] = value
        logger.info(f"更新配置: {key} -> {value}")

    def _convert_to_string(self, value, config_type):
        """将值转换为字符串"""
        if config_type == "json":
            import json
            return json.dumps(value)
        return str(value)

    def get_all_configs(self):
        """获取所有配置"""
        if not self._config_cache:
            self.load_config_from_db()
        return self._config_cache
