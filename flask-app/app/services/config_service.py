#!/usr/bin/env python3
"""
配置服务，用于从数据库加载和管理系统配置

# JSON import removed - using database
from app.models.system_config import SystemConfig
from app.utils.logging import logger


class ConfigService:
    """配置服务，负责从数据库加载和管理系统配置"""

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
        logger.info("📁 从数据库加载系统配置")

        try:
            # 获取所有激活的配置
            configs = SystemConfig.get_all_configs()

            # 清空缓存
            self._config_cache.clear()

            # 加载配置到缓存
            for config in configs:
                # 根据配置类型转换值
                value = self._convert_config_value(config.config_value, config.config_type)
                self._config_cache[config.config_key] = value

            logger.info(f"✅ 成功从数据库加载 {len(self._config_cache)} 个配置项")
            return self._config_cache

        except Exception as e:
            logger.error(f"❌ 从数据库加载配置失败: {str(e)}")
            return {}

    def _convert_config_value(self, value, config_type):
        """根据配置类型转换值"""
        try:
                return value.lower() in ("true", "1", "yes", "on")
            elif config_type == "integer":
                return int(value)
            elif config_type == "float":
                return float(value)
            elif config_type == "json":
                return eval(value)
            elif config_type == "list":
                return [item.strip() for item in value.split(",")]
            else:
                return value
        except Exception as e:
            logger.warning(f"⚠️  转换配置值失败: {value} -> {config_type}，使用原始值")

    def get_config(self, key, default=None):
        # 如果缓存为空，加载配置
        if not self._config_cache:
            self.load_config_from_db()

        return self._config_cache.get(key, default)

    def set_config(self, key, value, config_type="string", description=""):
        """设置配置值"""
        # 转换值为字符串存储
        str_value = self._convert_to_string(value, config_type)

        # 保存到数据库
        config = SystemConfig.get_by_key(key)
        if config:
            # 更新现有配置
            config.config_value = str_value
            config.config_type = config_type
            config.description = description
            config.save()
        else:
            # 创建新配置
            config = SystemConfig(
                config_value=str_value,
                config_type=config_type,
                description=description
            )
            config.save()

        # 更新缓存
        self._config_cache[key] = value
        logger.info(f"✅ 更新配置: {key} -> {value}")
    def _convert_to_string(self, value, config_type):
        """将值转换为字符串"""
        if config_type == "json":
            return str(value)
        elif config_type == "list":
            return ",".join(value)
        else:

    def get_all_configs(self):
        if not self._config_cache:
            self.load_config_from_db()
        return self._config_cache

        """刷新配置缓存"""
        return self.load_config_from_db()

# 初始化配置服务
    """初始化配置服务"""
    config_service.load_config_from_db()
    return config_service


# 导出配置服务实例
config_service = ConfigService()
