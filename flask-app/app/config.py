# -*- coding: utf-8 -*-
# Configuration Management System
"""
统一管理系统配置，支持从多种来源加载配置
"""

import os
import logging
import time
import threading
from typing import Dict, Any

# 配置日志
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    'ENV': 'development',
    'DEBUG': True,
    'SECRET_KEY': 'dev-secret-key',
    'VERSION': '3.0.0',  # 系统主版本号
    'INTERNAL_VERSION': '3.0.0.5678',  # 内部版本号
    'TEST_VERSION': '3.0.0-beta.2',  # 测试版本号
    'SANDBOX_VERSION': '3.0.0-sandbox.4',  # 沙盒版本号
    'BUILD_NUMBER': 5678,  # 构建号
    'BUILD_DATE': '2026-03-03',  # 构建日期

    # 集群配置
    'CLUSTER_ENABLED': True,  # 是否启用集群模式
    'CLUSTER_NAME': 'mtscos-cluster',  # 集群名称
    'CLUSTER_NODES': ['127.0.0.1:8443', '127.0.0.1:8444', '127.0.0.1:8445'],  # 集群节点列表
    'CLUSTER_NODE_ID': 'node-1',  # 当前节点ID
    'CLUSTER_NODE_ROLE': 'master',  # 根服务器设置为主节点
    'CLUSTER_HEALTH_CHECK_INTERVAL': 15,  # 健康检查间隔（秒）
    'CLUSTER_DATA_SYNC_INTERVAL': 30,  # 数据同步间隔（秒）
    'CLUSTER_COMMUNICATION_PORT': 9443,  # 集群通信端口
    'CLUSTER_LEADER_ELECTION_ENABLED': False,  # 根服务器固定为主节点
    'CLUSTER_LEADER_ELECTION_TIMEOUT': 10,  # 领导者选举超时（秒）
    'CLUSTER_LEADER_HEARTBEAT_INTERVAL': 5,  # 领导者心跳间隔（秒）
    'CLUSTER_MONITORING_ENABLED': True,  # 是否启用集群监控

    # 根服务器配置
    'SERVER_HOST': '0.0.0.0',  # 根服务器监听所有网络接口
    'SERVER_PORT': 8443,  # 根服务器端口
    'PROTOCOL': 'https',  # 协议：http或https
    'HTTPS_ENABLED': True,
    'SSL_CERT_PATH': 'ssl/cert.pem',
    'SSL_KEY_PATH': 'ssl/key.pem',
    'ROOT_SERVER_ENABLED': True,  # 启用根服务器
    'ROOT_SERVER_HOST': '127.0.0.1',  # 根服务器主机
    'ROOT_SERVER_PORT': 8443,  # 根服务器端口

    # 数据库配置
    'DATABASE_URI': 'sqlite:///app.db',
    'DATABASE_TYPE': 'sqlite',
    'DATABASE_NAME': 'app.db',
    'DATABASE_HOST': '',
    'DATABASE_PORT': '',
    'DATABASE_USER': '',
    'DATABASE_PASSWORD': '',

    # 安全配置
    'SECURITY_ENABLED': True,
    'PASSWORD_HASH_ALGORITHM': 'pbkdf2_sha256',
    'SESSION_TIMEOUT': 3600,  # 会话超时时间（秒）
    'MAX_LOGIN_ATTEMPTS': 5,  # 最大登录尝试次数
    'LOCKOUT_DURATION': 300,  # 锁定时长（秒）

    # API配置
    'API_RATE_LIMIT': 100,  # 每分钟请求限制
    'API_VERSION': 'v1',
    'API_DEBUG': True,

    # AI配置
    'AI_ENABLED': True,
    'AI_MODEL_PATH': './models',
    'AI_MAX_TOKENS': 4096,
    'AI_TEMPERATURE': 0.7,

    # 缓存配置
    'CACHE_ENABLED': True,
    'CACHE_TYPE': 'simple',
    'CACHE_TIMEOUT': 300,

    # 日志配置
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'app.log',
    'LOG_ROTATION': True,
    'LOG_MAX_SIZE': 10 * 1024 * 1024,  # 10MB

    # 静态文件配置
    'STATIC_FOLDER': 'static',
    'TEMPLATE_FOLDER': 'templates',

    # 邮件配置
    'MAIL_ENABLED': False,
    'MAIL_SERVER': 'smtp.example.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': '',
    'MAIL_PASSWORD': '',
    'MAIL_DEFAULT_SENDER': 'admin@example.com',

    # 定时任务配置
    'SCHEDULER_ENABLED': True,
    'SCHEDULER_INTERVAL': 60,  # 定时任务间隔（秒）

    # 备份配置
    'BACKUP_ENABLED': True,
    'BACKUP_INTERVAL': 3600,  # 备份间隔（秒）
    'BACKUP_RETENTION': 7,  # 备份保留天数

    # 监控配置
    'MONITORING_ENABLED': True,
    'METRICS_ENABLED': True,
    'ALERTING_ENABLED': True,

    # 国际化配置
    'LANGUAGES': ['zh', 'en'],
    'DEFAULT_LANGUAGE': 'zh',
    'TIMEZONE': 'Asia/Shanghai',
}


class ConfigManager:
    """
    配置管理器 - 统一管理系统配置
    """
    
    _config_cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 300  # 缓存超时时间（秒）

    @staticmethod
    def load_config(config_type=None):
        """
        加载配置
        
        Args:
            config_type: 配置类型，可选值：'production', 'development', 'test'
        
        Returns:
            配置字典
        """
        # 尝试从缓存获取
        cache_key = config_type or 'default'
        cached_config = ConfigManager._get_from_cache(cache_key)
        if cached_config:
            return cached_config

        # 创建配置副本
        config = DEFAULT_CONFIG.copy()

        # 根据配置类型覆盖配置
        if config_type == 'production':
            config.update({
                'ENV': 'production',
                'DEBUG': False,
                'API_DEBUG': False,
                'HTTPS_ENABLED': True,
            })
        elif config_type == 'test':
            config.update({
                'ENV': 'test',
                'DEBUG': True,
                'DATABASE_URI': 'sqlite:///test.db',
            })
        else:
            config.update({
                'ENV': 'development',
                'DEBUG': True,
            })

        # 从环境变量覆盖配置
        ConfigManager._load_from_env(config)

        # 添加到缓存
        ConfigManager._add_to_cache(cache_key, config)

        logger.info(f"[配置管理] 配置加载完成，环境: {config['ENV']}")
        return config

    @staticmethod
    def _load_from_env(config):
        """
        从环境变量加载配置
        """
        env_mapping = {
            'SECRET_KEY': 'SECRET_KEY',
            'DATABASE_URI': 'DATABASE_URI',
            'SERVER_PORT': 'SERVER_PORT',
            'HTTPS_ENABLED': 'HTTPS_ENABLED',
        }
        
        for config_key, env_key in env_mapping.items():
            if env_key in os.environ:
                value = os.environ[env_key]
                # 尝试转换类型
                if value.lower() == 'true':
                    config[config_key] = True
                elif value.lower() == 'false':
                    config[config_key] = False
                elif value.isdigit():
                    config[config_key] = int(value)
                else:
                    config[config_key] = value

    @staticmethod
    def _get_from_cache(key):
        """从缓存获取配置"""
        with ConfigManager._cache_lock:
            if key in ConfigManager._config_cache:
                cached_data = ConfigManager._config_cache[key]
                if time.time() - cached_data['timestamp'] < ConfigManager._cache_ttl:
                    return cached_data['config']
                else:
                    del ConfigManager._config_cache[key]
            return None

    @staticmethod
    def _add_to_cache(key, config):
        """将配置添加到缓存"""
        with ConfigManager._cache_lock:
            ConfigManager._config_cache[key] = {
                'config': config,
                'timestamp': time.time()
            }

    @staticmethod
    def get_config(key, default=None):
        """
        获取单个配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        """
        config = ConfigManager.load_config()
        return config.get(key, default)

    @staticmethod
    def set_config(key, value):
        """
        设置配置值（运行时）
        
        Args:
            key: 配置键
            value: 配置值
        """
        config = ConfigManager.load_config()
        config[key] = value
        # 更新缓存
        ConfigManager._add_to_cache('runtime', config)

    @staticmethod
    def reload_config():
        """重新加载配置"""
        ConfigManager._config_cache.clear()
        logger.info("[配置管理] 配置已重新加载")


def load_config(config_type=None):
    """
    便捷函数：加载配置
    
    Args:
        config_type: 配置类型
    
    Returns:
        配置字典
    """
    return ConfigManager.load_config(config_type)


if __name__ == '__main__':
    # 测试配置加载
    config = load_config('development')
    print(f"环境: {config['ENV']}")
    print(f"版本: {config['VERSION']}")
    print(f"调试模式: {config['DEBUG']}")