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
    'CLUSTER_COMMUNICATION_PORT': 9443,  # 集群通信端口，使用443的变体，便于HTTPS
    'CLUSTER_LEADER_ELECTION_ENABLED': False,  # 根服务器固定为主节点，不需要选举
    'CLUSTER_LEADER_ELECTION_TIMEOUT': 10,  # 领导者选举超时（秒）
    'CLUSTER_LEADER_HEARTBEAT_INTERVAL': 5,  # 领导者心跳间隔（秒）
    'CLUSTER_MONITORING_ENABLED': True,  # 是否启用集群监控
    
    # 根服务器配置
    'SERVER_HOST': '0.0.0.0',  # 根服务器监听所有网络接口
    'SERVER_PORT': 8443,  # 根服务器端口，使用443的变体，便于HTTPS
    'PROTOCOL': 'https',  # 协议：http或https
    'HTTPS_ENABLED': True,
    'SSL_CERT_PATH': 'ssl/cert.pem',
    'SSL_KEY_PATH': 'ssl/key.pem',
    'ROOT_SERVER_ENABLED': True,  # 启用根服务器
    'ROOT_SERVER_HOST': '127.0.0.1',  # 根服务器主机
    'ROOT_SERVER_PORT': 8443,  # 根服务器端口
    
    # 数据库配置
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///app.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'DATABASE_PATH': 'app.db',
    'DATABASE_TYPE': 'sqlite',  # 数据库类型：sqlite, mysql, postgresql
    'DATABASE_HOST': 'localhost',
    'DATABASE_USER': '',
    'DATABASE_PASSWORD': '',
    'DATABASE_NAME': 'app',
    
    # 云端数据库配置
    'CLOUD_DATABASE_ENABLED': False,  # 是否启用云端数据库
    'CLOUD_DATABASE_TYPE': 'postgresql',  # 云端数据库类型
    'CLOUD_DATABASE_HOST': 'localhost',  # 云端数据库主机
    'CLOUD_DATABASE_PORT': 5432,  # 云端数据库端口
    'CLOUD_DATABASE_USER': 'postgres',  # 云端数据库用户名
    'CLOUD_DATABASE_PASSWORD': 'password',  # 云端数据库密码
    'CLOUD_DATABASE_NAME': 'mtscos_ai',  # 云端数据库名称
    
    # 安全配置
    'SECURITY_CONFIG': {
        'ANTI_DECOMPILE': True,  # 启用反编译保护
        'ANTI_PENETRATION': True,  # 启用防渗透保护
        'ANTI_PRIVILEGE_ESCALATION': True,  # 启用防提权保护
        'ENCRYPT_SENSITIVE_DATA': True,  # 加密敏感数据
        'API_KEY_REQUIRED': True,  # API请求需要密钥
        'RATE_LIMITING': True,  # 启用速率限制
        'IP_WHITELIST': [],  # IP白名单
        'SESSION_TIMEOUT': 3600,  # 会话超时时间（秒）
        'MAX_LOGIN_ATTEMPTS': 5,  # 最大登录尝试次数
        'LOCKOUT_DURATION': 300,  # 锁定时长（秒）
        'TWO_FACTOR_AUTH': True,  # 启用双因素认证
    },
    
    # OAuth配置
    'OAUTH_CONFIG': {
        'GITHUB': {
            'CLIENT_ID': os.environ.get('GITHUB_CLIENT_ID', ''),
            'CLIENT_SECRET': os.environ.get('GITHUB_CLIENT_SECRET', ''),
            'AUTHORIZE_URL': 'https://github.com/login/oauth/authorize',
            'TOKEN_URL': 'https://github.com/login/oauth/access_token',
            'USER_INFO_URL': 'https://api.github.com/user',
            'SCOPE': 'user:email',
            'REDIRECT_URI': 'https://localhost:8443/auth/github/callback'
        },
        'GOOGLE': {
            'CLIENT_ID': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'CLIENT_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'AUTHORIZE_URL': 'https://accounts.google.com/o/oauth2/auth',
            'TOKEN_URL': 'https://oauth2.googleapis.com/token',
            'USER_INFO_URL': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'SCOPE': 'email profile',
            'REDIRECT_URI': 'https://localhost:8443/auth/google/callback'
        },
        'WEIXIN': {
            'APP_ID': os.environ.get('WEIXIN_APP_ID', ''),
            'APP_SECRET': os.environ.get('WEIXIN_APP_SECRET', ''),
            'AUTHORIZE_URL': 'https://open.weixin.qq.com/connect/qrconnect',
            'TOKEN_URL': 'https://api.weixin.qq.com/sns/oauth2/access_token',
            'USER_INFO_URL': 'https://api.weixin.qq.com/sns/userinfo',
            'SCOPE': 'snsapi_login',
            'REDIRECT_URI': 'https://localhost:8443/auth/weixin/callback'
        }
    },
    
    # JSON配置
    'JSON_AS_ASCII': False,
    'TEMPLATES_AUTO_RELOAD': True,
    'SEND_FILE_MAX_AGE_DEFAULT': 0,
    
    # 配置文件路径
    'LOG_LEVEL': 'INFO',
    'AI_CONFIG_PATH': 'ai_config.json',
    'SYSTEM_CONFIG_PATH': 'system_config.json',
    # AI模型配置
    'MODEL_PATH': 'models/',
    'AI_CONFIG': {
        'MONITORING_ENABLED': True,
        'LEARNING_ENABLED': True,
        'AUTO_ADAPT': True,
        'AI_ENHANCEMENT': True,
        'AUTO_OPTIMIZATION': True,
        'AUTO_CLOSURE': True,
        'SELF_OPTIMIZATION': True
    },
    
    # 网络配置
    'NETWORK_CONFIG': {
        'MAX_CONNECTIONS': 100,
        'TIMEOUT': 30,
        'RETRY_COUNT': 3,
        'CACHE_SIZE': 1000,
        'CACHE_TTL': 3600
    },
    
    # 信道配置
    'CHANNEL_CONFIG': {
        'MAX_CHANNELS': 50,
        'CHANNEL_TIMEOUT': 60,
        'MAX_MSG_PER_CHANNEL': 1000
    },
    
    # 规则配置
    'RULES_CONFIG': {
        'MAX_REQUESTS_PER_MINUTE': 100,
        'MAX_LOGIN_ATTEMPTS': 5,
        'LOCKOUT_DURATION': 300,  # 锁定时长（秒）
        'PASSWORD_EXPIRY_DAYS': 90
    },
    
    # 脚本配置
    'SCRIPT_CONFIG': {
        'AUTO_RUN_SCRIPTS': True,
        'SCRIPT_TIMEOUT': 30,
        'SCRIPT_LOG_PATH': 'script.log'
    },
    
    # 机制配置
    'MECHANISM_CONFIG': {
        'AUTO_BACKUP_ENABLED': True,
        'BACKUP_INTERVAL': 86400,  # 备份间隔（秒）
        'AUTO_UPDATE_ENABLED': False,
        'CACHE_ENABLED': True,
        'LOGGING_ENABLED': True
    },
    
    # 日志相关配置
    'LOG_SIZE_FILE': 'system_size.log',
    'LOG_MAX_BYTES': 10485760,
    'LOG_BACKUP_COUNT': 10,
    'LOG_TIME_FILE': 'system_time.log',
    'LOG_ROTATE_WHEN': 'D',
    'LOG_ROTATE_INTERVAL': 1,
    'LOG_ROTATE_BACKUP_COUNT': 7
}

# 保持向后兼容 - 原Config类
class Config:
    """
    原始配置类，用于向后兼容
    """
    DEBUG = DEFAULT_CONFIG['DEBUG']
    SECRET_KEY = DEFAULT_CONFIG['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = DEFAULT_CONFIG['SQLALCHEMY_DATABASE_URI']
    SQLALCHEMY_TRACK_MODIFICATIONS = DEFAULT_CONFIG['SQLALCHEMY_TRACK_MODIFICATIONS']
    DATABASE_PATH = DEFAULT_CONFIG['DATABASE_PATH']
    DATABASE_TYPE = DEFAULT_CONFIG['DATABASE_TYPE']
    DATABASE_HOST = DEFAULT_CONFIG['DATABASE_HOST']
    DATABASE_USER = DEFAULT_CONFIG['DATABASE_USER']
    DATABASE_PASSWORD = DEFAULT_CONFIG['DATABASE_PASSWORD']
    DATABASE_NAME = DEFAULT_CONFIG['DATABASE_NAME']
    AI_CONFIG_PATH = DEFAULT_CONFIG['AI_CONFIG_PATH']
    SYSTEM_CONFIG_PATH = DEFAULT_CONFIG['SYSTEM_CONFIG_PATH']
    LOG_LEVEL = DEFAULT_CONFIG['LOG_LEVEL']
    NETWORK_CONFIG = DEFAULT_CONFIG['NETWORK_CONFIG']
    MODEL_PATH = DEFAULT_CONFIG['MODEL_PATH']
    AI_CONFIG = DEFAULT_CONFIG['AI_CONFIG']
    # 密码哈希配置
    HASH_ALGORITHM = 'sha256'
    HASH_ITERATIONS = 100000
    # 版本号配置
    VERSION = DEFAULT_CONFIG['VERSION']
    INTERNAL_VERSION = DEFAULT_CONFIG['INTERNAL_VERSION']
    TEST_VERSION = DEFAULT_CONFIG['TEST_VERSION']
    SANDBOX_VERSION = DEFAULT_CONFIG['SANDBOX_VERSION']
    BUILD_NUMBER = DEFAULT_CONFIG['BUILD_NUMBER']
    BUILD_DATE = DEFAULT_CONFIG['BUILD_DATE']
    # 云端数据库配置
    CLOUD_DATABASE_ENABLED = DEFAULT_CONFIG['CLOUD_DATABASE_ENABLED']
    CLOUD_DATABASE_TYPE = DEFAULT_CONFIG['CLOUD_DATABASE_TYPE']
    CLOUD_DATABASE_HOST = DEFAULT_CONFIG['CLOUD_DATABASE_HOST']
    CLOUD_DATABASE_PORT = DEFAULT_CONFIG['CLOUD_DATABASE_PORT']
    CLOUD_DATABASE_USER = DEFAULT_CONFIG['CLOUD_DATABASE_USER']
    CLOUD_DATABASE_PASSWORD = DEFAULT_CONFIG['CLOUD_DATABASE_PASSWORD']
    CLOUD_DATABASE_NAME = DEFAULT_CONFIG['CLOUD_DATABASE_NAME']
    # 安全配置
    SECURITY_CONFIG = DEFAULT_CONFIG['SECURITY_CONFIG']
    # 日志相关配置
    LOG_SIZE_FILE = DEFAULT_CONFIG['LOG_SIZE_FILE']
    LOG_MAX_BYTES = DEFAULT_CONFIG['LOG_MAX_BYTES']
    LOG_BACKUP_COUNT = DEFAULT_CONFIG['LOG_BACKUP_COUNT']
    LOG_TIME_FILE = DEFAULT_CONFIG['LOG_TIME_FILE']
    LOG_ROTATE_WHEN = DEFAULT_CONFIG['LOG_ROTATE_WHEN']
    LOG_ROTATE_INTERVAL = DEFAULT_CONFIG['LOG_ROTATE_INTERVAL']
    LOG_ROTATE_BACKUP_COUNT = DEFAULT_CONFIG['LOG_ROTATE_BACKUP_COUNT']

class ConfigManager:
    """
    配置管理器，负责加载和管理系统配置
    """
    
    # 配置缓存
    _config_cache = {}
    _cache_lock = threading.RLock()
    _cache_ttl = 300  # 缓存过期时间（秒）
    
    @staticmethod
    def load_config(config_type: str = None) -> Dict[str, Any]:
        """
        加载配置
        
        Args:
            config_type: 配置类型，可选值：'production', 'development', 'test'
        
        Returns:
            配置字典
        """
        # 尝试从缓存获取配置
        cache_key = f"config_{config_type or 'default'}"
        cached_config = ConfigManager._get_from_cache(cache_key)
        if cached_config:
            logger.debug(f"[配置管理] 从缓存加载配置: {config_type or 'default'}")
            return cached_config
        
        logger.info(f"[配置管理] 加载配置，类型: {config_type or 'default'}")
        
        # 1. 从默认配置开始
        config = DEFAULT_CONFIG.copy()
        
        # 2. 根据配置类型加载特定配置
        if config_type:
            config.update(ConfigManager._load_env_config(config_type))
        
        # 3. 从环境变量加载配置（优先级高于默认配置）
        config.update(ConfigManager._load_env_vars())
        
        # 4. 从文件加载配置（优先级最高）
        config.update(ConfigManager._load_config_from_file())
        
        # 5. 从数据库加载配置（优先级最高）
        try:
            config.update(ConfigManager._load_config_from_db())
        except Exception as e:
            logger.warning(f"[配置管理] 从数据库加载配置失败: {str(e)}")
        
        # 将配置添加到缓存
        ConfigManager._add_to_cache(cache_key, config)
        
        logger.info(f"[配置管理] 配置加载完成，环境: {config['ENV']}")
        return config
    
    @staticmethod
    def _get_from_cache(key):
        """从缓存获取配置"""
        with ConfigManager._cache_lock:
            if key in ConfigManager._config_cache:
                cached_data = ConfigManager._config_cache[key]
                if time.time() - cached_data['timestamp'] < ConfigManager._cache_ttl:
                    return cached_data['config']
                else:
                    # 缓存过期，删除
                    del ConfigManager._config_cache[key]
            return None
    
    @staticmethod
    def _add_to_cache(key, config):
        """将配置添加到缓存"""
        with ConfigManager._cache_lock:
            # 检查缓存大小
            if len(ConfigManager._config_cache) >= 10:  # 最多缓存10个配置
                # 删除最早的缓存项
                oldest_key = min(ConfigManager._config_cache, key=lambda k: ConfigManager._config_cache[k]['timestamp'])
                del ConfigManager._config_cache[oldest_key]
            
            # 添加新缓存项
            ConfigManager._config_cache[key] = {
                'config': config,
                'timestamp': time.time()
            }
    
    @staticmethod
    def clear_cache():
        """清空配置缓存"""
        with ConfigManager._cache_lock:
            ConfigManager._config_cache.clear()
            logger.info("[配置管理] 配置缓存已清空")
    
    @staticmethod
    def _load_env_config(env: str) -> Dict[str, Any]:
        """
        根据环境加载配置
        
        Args:
            env: 环境名称
        
        Returns:
            环境特定配置
        """
        env_configs = {
            'production': {
                'ENV': 'production',
                'DEBUG': False,
                'LOG_LEVEL': 'WARNING'
            },
            'development': {
                'ENV': 'development',
                'DEBUG': True,
                'LOG_LEVEL': 'INFO'
            },
            'test': {
                'ENV': 'test',
                'DEBUG': True,
                'TESTING': True,
                'LOG_LEVEL': 'DEBUG'
            }
        }
        
        return env_configs.get(env, {})
    
    @staticmethod
    def _load_env_vars() -> Dict[str, Any]:
        """
        从环境变量加载配置
        
        Returns:
            环境变量配置
        """
        env_config = {}
        
        # 支持的环境变量列表
        env_vars = [
            'ENV', 'DEBUG', 'SECRET_KEY', 'SQLALCHEMY_DATABASE_URI',
            'SQLALCHEMY_TRACK_MODIFICATIONS', 'DATABASE_PATH', 'LOG_LEVEL'
        ]
        
        for var in env_vars:
            if var in os.environ:
                value = os.environ[var]
                # 转换布尔值
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                env_config[var] = value
                logger.info(f"[配置管理] 从环境变量加载配置: {var}={value}")
        
        return env_config
    
    @staticmethod
    def _load_config_from_file() -> Dict[str, Any]:
        """
        从文件加载配置
        
        Returns:
            文件配置
        """
        file_config = {}
        
        # 检查是否存在配置文件
        config_files = [
            'system_config.json',
            'config.json',
            '.env'  # 简单的.env文件支持
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                logger.info(f"[配置管理] 从文件加载配置: {config_file}")
                # 简单的JSON配置文件支持
                if config_file.endswith('.json'):
                    try:
                        import json
                        with open(config_file, 'r', encoding='utf-8') as f:
                            file_config.update(json.load(f))
                    except Exception as e:
                        logger.error(f"[配置管理] 从JSON文件加载配置失败: {config_file}, 错误: {str(e)}")
                # 简单的.env文件支持
                elif config_file == '.env':
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    if '=' in line:
                                        key, value = line.split('=', 1)
                                        file_config[key.strip()] = value.strip()
                    except Exception as e:
                        logger.error(f"[配置管理] 从.env文件加载配置失败: {config_file}, 错误: {str(e)}")
        
        return file_config
    
    @staticmethod
    def _load_config_from_db() -> Dict[str, Any]:
        """
        从数据库加载配置
        
        Returns:
            数据库配置
        """
        db_config = {}
        
        try:
            # 使用 SystemConfigManager 从数据库加载配置
            from app.models.system_config import SystemConfigManager
            
            # 初始化默认配置（如果表不存在或配置缺失）
            SystemConfigManager.init_default_configs()
            
            # 直接使用 SystemConfigManager 获取配置
            
            # 特别处理应用端口配置
            app_port = SystemConfigManager.get_config('app_port')
            if app_port:
                db_config['SERVER_PORT'] = app_port
                logger.info(f"[配置管理] 从数据库加载应用端口: SERVER_PORT={app_port}")
            
            # 特别处理调试模式配置
            debug_mode = SystemConfigManager.get_config('debug_mode')
            if debug_mode is not None:
                db_config['DEBUG'] = debug_mode
                logger.info(f"[配置管理] 从数据库加载调试模式: DEBUG={debug_mode}")
                db_config['ENV'] = 'development' if debug_mode else 'production'
                logger.info(f"[配置管理] 从数据库加载环境配置: ENV={db_config['ENV']}")
            
            # 特别处理应用名称配置
            app_name = SystemConfigManager.get_config('app_name')
            if app_name:
                db_config['APP_NAME'] = app_name
                logger.info(f"[配置管理] 从数据库加载应用名称: APP_NAME={app_name}")
            
            # 特别处理应用版本配置
            app_version = SystemConfigManager.get_config('app_version')
            if app_version:
                db_config['APP_VERSION'] = app_version
                db_config['VERSION'] = app_version
                logger.info(f"[配置管理] 从数据库加载应用版本: APP_VERSION={app_version}, VERSION={app_version}")
            
            # 特别处理AI配置
            ai_model_type = SystemConfigManager.get_config('ai_model_type')
            if ai_model_type:
                db_config['AI_MODEL_TYPE'] = ai_model_type
                logger.info(f"[配置管理] 从数据库加载AI模型类型: AI_MODEL_TYPE={ai_model_type}")
            
            ai_temperature = SystemConfigManager.get_config('ai_temperature')
            if ai_temperature is not None:
                db_config['AI_TEMPERATURE'] = ai_temperature
                logger.info(f"[配置管理] 从数据库加载AI温度参数: AI_TEMPERATURE={ai_temperature}")
            
            ai_max_tokens = SystemConfigManager.get_config('ai_max_tokens')
            if ai_max_tokens is not None:
                db_config['AI_MAX_TOKENS'] = ai_max_tokens
                logger.info(f"[配置管理] 从数据库加载AI最大令牌数: AI_MAX_TOKENS={ai_max_tokens}")
            
            # 加载所有其他配置
            from app.models.system_config import SystemConfig
            # 使用正确的filter方法调用
            configs = SystemConfig.filter(where_clause="is_active = ?", where_params=(True,))
            
            for config in configs:
                key = config.key
                value = SystemConfigManager.get_config(key)
                
                # 对于特定的配置键，转换为大写以匹配配置系统
                config_key = key.upper()
                # 只有在还没有设置的情况下才设置
                if config_key not in db_config:
                    db_config[config_key] = value
                    logger.info(f"[配置管理] 从数据库加载配置: {config_key}={value}")
        except Exception as e:
            logger.error(f"[配置管理] 从数据库加载配置失败: {str(e)}")
        
        return db_config
    
    @staticmethod
    def save_config_to_db(config: Dict[str, Any]) -> None:
        """
        将配置保存到数据库
        
        Args:
            config: 要保存的配置字典
        """
        try:
            from app.models.system_config import SystemConfigManager
            
            logger.info("[配置管理] 开始将配置保存到数据库...")
            
            # 保存重要的系统配置
            config_mappings = {
                'app_name': config.get('APP_NAME', 'MTSCOS AI Project'),
                'app_version': config.get('VERSION', '1.0.0'),
                'app_port': config.get('SERVER_PORT', 8888),
                'debug_mode': config.get('DEBUG', True),
                'ai_model_type': config.get('AI_MODEL_TYPE', 'gpt-4o-mini'),
                'ai_temperature': config.get('AI_TEMPERATURE', 0.7),
                'ai_max_tokens': config.get('AI_MAX_TOKENS', 2000)
            }
            
            for key, value in config_mappings.items():
                # 确定数据类型
                if isinstance(value, bool):
                    data_type = 'boolean'
                elif isinstance(value, (int, float)):
                    data_type = 'number'
                elif isinstance(value, (dict, list)):
                    data_type = 'object'
                else:
                    data_type = 'string'
                
                # 保存配置
                SystemConfigManager.set_config(
                    key=key,
                    value=value,
                    description=f"系统配置项: {key}",
                    category='app_config' if key.startswith('app_') else 'ai_config',
                    data_type=data_type
                )
                logger.info(f"[配置管理] 保存数据库配置: {key}={value}")
            
            # 清空配置缓存，确保下次加载时获取最新配置
            ConfigManager.clear_cache()
            
            logger.info("[配置管理] 配置保存到数据库完成")
        except Exception as e:
            logger.error(f"[配置管理] 保存配置到数据库失败: {str(e)}")

# 导出配置加载函数
def load_config(config_type: str = None) -> Dict[str, Any]:
    """
    加载配置的便捷函数
    
    Args:
        config_type: 配置类型
    
    Returns:
        配置字典
    """
    return ConfigManager.load_config(config_type)

