# -*- coding: utf-8 -*-
# Configuration Management System - 支持多数据库分离
"""
统一管理系统配置,支持从多种来源加载配置
优先从数据库读取配置,数据库中不存在的配置使用默认值
"""

import os
import logging
import signal
import traceback
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """超时异常"""
    pass

def timeout_wrapper(timeout_seconds=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"函数 {func.__name__} 执行超时({timeout_seconds}秒)")
            
            old_handler = signal.signal(signal.SIGALRM, handler)
            try:
                signal.alarm(timeout_seconds)
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

# ==================== 基础配置 ====================
BASE_CONFIG = {
    'ENV': 'development',
    'DEBUG': True,
    'SECRET_KEY': 'mtscos_ai_secret_key_2026',
    'VERSION': '3.1.0',
    'BUILD_NUMBER': 5679,
    'BUILD_DATE': '2026-06-26',
}

# ==================== 服务器配置 ====================
SERVER_CONFIG = {
    'SERVER_HOST': '0.0.0.0',
    'SERVER_PORT': 8443,
    'PROTOCOL': 'https',
    'HTTPS_ENABLED': True,
    'SSL_CERT_PATH': 'ssl/cert.pem',
    'SSL_KEY_PATH': 'ssl/key.pem',
}

# ==================== 数据库配置 ====================
DATABASE_CONFIG = {
    'DATABASE_DIR': 'databases',
    'DATA_SEPARATION_ENABLED': True,
    'READ_WRITE_SPLIT_ENABLED': True,
    'READ_REPLICATION_LAG': 1,
    
    'DATABASES': {
        'users': {'name': 'users', 'file': 'users.db', 'description': '用户数据', 'role': 'master'},
        'questions': {'name': 'questions', 'file': 'questions.db', 'description': '题库数据', 'role': 'slave'},
        'exams': {'name': 'exams', 'file': 'exams.db', 'description': '考试数据', 'role': 'slave'},
        'system': {'name': 'system', 'file': 'system.db', 'description': '系统配置', 'role': 'master'},
        'api': {'name': 'api', 'file': 'api.db', 'description': 'API数据', 'role': 'slave'},
        'route': {'name': 'route', 'file': 'route.db', 'description': '路由数据', 'role': 'slave'},
        'customs': {'name': 'customs', 'file': 'customs.db', 'description': '海关数据', 'role': 'slave'},
    },
}

# ==================== 集群配置 ====================
CLUSTER_CONFIG = {
    'CLUSTER_ENABLED': True,
    'CLUSTER_NAME': 'mtscos-cluster',
    'CLUSTER_HEALTH_CHECK_INTERVAL': 15,
    'CLUSTER_DATA_SYNC_INTERVAL': 30,
    'CLUSTER_NODES': [
        {'id': 'node-master', 'host': '127.0.0.1', 'port': 8443, 'role': 'master'},
        {'id': 'node-worker-1', 'host': '127.0.0.1', 'port': 8444, 'role': 'worker'},
        {'id': 'node-worker-2', 'host': '127.0.0.1', 'port': 8445, 'role': 'worker'},
    ],
}

# ==================== 负载均衡配置 ====================
LOAD_BALANCER_CONFIG = {
    'LOAD_BALANCER_ENABLED': True,
    'LOAD_BALANCER_ALGORITHM': 'round_robin',
    'LOAD_BALANCER_LISTEN_ADDRESS': '0.0.0.0',
    'LOAD_BALANCER_LISTEN_PORT': 8080,
    'LOAD_BALANCER_MAX_CONNECTIONS': 1000,
    'LOAD_BALANCER_CONNECTION_TIMEOUT': 30,
    'LOAD_BALANCER_HEALTH_CHECK_ENABLED': True,
    'LOAD_BALANCER_HEALTH_CHECK_INTERVAL': 10,
    'LOAD_BALANCER_HEALTH_CHECK_TIMEOUT': 5,
    'LOAD_BALANCER_HEALTH_CHECK_PATH': '/health',
}

# ==================== 多级缓存配置 ====================
CACHE_CONFIG = {
    'CACHE_ENABLED': True,
    'CACHE_TYPE': 'multi_level',
    'CACHE_TIMEOUT': 300,
    'CACHE_AUTO_PROMOTE': True,
    'CACHE_AUTO_DEMOTE': True,
    
    'CACHE_L1_ENABLED': True,
    'CACHE_L1_MAX_SIZE': 1000,
    'CACHE_L1_TTL': 300,
    'CACHE_L1_POLICY': 'lru',
    
    'CACHE_L2_ENABLED': True,
    'CACHE_L2_DIR': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cache/l2',
    'CACHE_L2_MAX_SIZE': 100 * 1024 * 1024,
    'CACHE_L2_TTL': 3600,
    
    'CACHE_L3_ENABLED': True,
    'CACHE_L3_DB_PATH': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cache/l3/cache.db',
    'CACHE_L3_TTL': 86400,
}

# ==================== 分布式数据库配置 ====================
DISTRIBUTED_DB_CONFIG = {
    'DISTRIBUTED_DB_ENABLED': True,
    'SHARDING_STRATEGY': 'hash',
    'SHARD_COUNT': 4,
    'REPLICA_COUNT': 2,
    'CONSISTENCY_LEVEL': 'eventual',
    'DISTRIBUTED_TRANSACTIONS': True,
    'CROSS_SHARD_QUERY': True,
    
    'SHARDED_TABLES': {
        'users': {'sharded': True, 'shard_key': 'id', 'strategy': 'hash', 'shards': 4},
        'orders': {'sharded': True, 'shard_key': 'user_id', 'strategy': 'hash', 'shards': 4},
        'logs': {'sharded': True, 'shard_key': 'created_at', 'strategy': 'time', 'shards': 12},
        'config': {'sharded': False},
    },
}

# ==================== 安全配置 ====================
SECURITY_CONFIG = {
    'SECURITY_ENABLED': True,
    'PASSWORD_HASH_ALGORITHM': 'pbkdf2_sha256',
    'SESSION_TIMEOUT': 3600,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,
}

# ==================== API配置 ====================
API_CONFIG = {
    'API_RATE_LIMIT': 100,
    'API_VERSION': 'v1',
    'API_DEBUG': True,
}

# ==================== AI配置 ====================
AI_CONFIG = {
    'AI_ENABLED': True,
    'AI_MODEL_PATH': './models',
    'AI_MAX_TOKENS': 4096,
    'AI_TEMPERATURE': 0.7,
}

# ==================== 日志配置 ====================
LOG_CONFIG = {
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'app.log',
    'LOG_ROTATION': True,
    'LOG_MAX_SIZE': 10 * 1024 * 1024,
}

# ==================== 高可用性配置 ====================
HA_CONFIG = {
    'HIGH_AVAILABILITY_ENABLED': True,
    'AUTO_FAILOVER_ENABLED': True,
    'FAILOVER_TIMEOUT': 30,
}

# 合并所有配置
DEFAULT_CONFIG = {
    **BASE_CONFIG,
    **SERVER_CONFIG,
    **DATABASE_CONFIG,
    **CLUSTER_CONFIG,
    **LOAD_BALANCER_CONFIG,
    **CACHE_CONFIG,
    **DISTRIBUTED_DB_CONFIG,
    **SECURITY_CONFIG,
    **API_CONFIG,
    **AI_CONFIG,
    **LOG_CONFIG,
    **HA_CONFIG,
}

# 全局数据库配置管理器实例
_db_config_manager = None

@timeout_wrapper(timeout_seconds=5)
def _import_db_config_manager():
    """导入数据库配置管理器（带超时）"""
    from app.services.db_config_manager import db_config_manager
    return db_config_manager

def get_db_config_manager():
    """获取数据库配置管理器实例"""
    global _db_config_manager
    if _db_config_manager is None:
        try:
            _db_config_manager = _import_db_config_manager()
            logger.info("[配置] 数据库配置管理器加载成功")
        except TimeoutError as e:
            logger.warning(f"[配置] 数据库配置管理器加载超时({str(e)})，使用默认配置")
            _db_config_manager = None
        except ImportError as e:
            logger.warning(f"[配置] 数据库配置管理器加载失败，使用默认配置: {str(e)}")
            _db_config_manager = None
        except Exception as e:
            logger.error(f"[配置] 数据库配置管理器加载异常: {str(e)}")
            logger.error(f"[配置] 异常堆栈:\n{traceback.format_exc()}")
            _db_config_manager = None
    return _db_config_manager


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """验证配置的完整性和正确性"""
        errors = []
        
        required_keys = ['SECRET_KEY', 'SERVER_HOST', 'SERVER_PORT', 'DATABASE_DIR']
        for key in required_keys:
            if key not in config or not config[key]:
                errors.append(f"缺少必要配置项: {key}")
        
        port = config.get('SERVER_PORT', 0)
        if not (1 <= port <= 65535):
            errors.append(f"无效的端口号: {port}")
        
        if config.get('CACHE_L2_ENABLED'):
            cache_dir = config.get('CACHE_L2_DIR', '')
            if cache_dir and not os.path.isdir(cache_dir):
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                    logger.info(f"创建缓存目录: {cache_dir}")
                except Exception as e:
                    errors.append(f"无法创建缓存目录: {cache_dir}, 错误: {str(e)}")
        
        db_dir = config.get('DATABASE_DIR', '')
        if db_dir and not os.path.isdir(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"创建数据库目录: {db_dir}")
            except Exception as e:
                errors.append(f"无法创建数据库目录: {db_dir}, 错误: {str(e)}")
        
        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            return False
        
        logger.info("配置验证通过")
        return True
    
    @staticmethod
    def validate_environment() -> bool:
        """验证运行环境"""
        errors = []
        
        import sys
        if sys.version_info < (3, 8):
            errors.append("Python版本需要3.8或更高")
        
        if errors:
            for error in errors:
                logger.error(f"环境验证失败: {error}")
            return False
        
        logger.info("环境验证通过")
        return True


def init_database_config():
    """初始化数据库配置（将默认配置写入数据库）"""
    db_manager = get_db_config_manager()
    if db_manager:
        db_manager.init_defaults(BASE_CONFIG, 'base')
        db_manager.init_defaults(SERVER_CONFIG, 'server')
        db_manager.init_defaults(DATABASE_CONFIG, 'database')
        db_manager.init_defaults(CLUSTER_CONFIG, 'cluster')
        db_manager.init_defaults(LOAD_BALANCER_CONFIG, 'load_balancer')
        db_manager.init_defaults(CACHE_CONFIG, 'cache')
        db_manager.init_defaults(DISTRIBUTED_DB_CONFIG, 'distributed_db')
        db_manager.init_defaults(SECURITY_CONFIG, 'security')
        db_manager.init_defaults(API_CONFIG, 'api')
        db_manager.init_defaults(AI_CONFIG, 'ai')
        db_manager.init_defaults(LOG_CONFIG, 'log')
        db_manager.init_defaults(HA_CONFIG, 'ha')
        
        security_extra_config = {
            'RATE_LIMITS': {
                'login': {'limit': 5, 'window': 60},
                'api': {'limit': 100, 'window': 60},
                'register': {'limit': 3, 'window': 300},
            },
            'PERMISSION_RULES': {
                'admin': {
                    'allowed_routes': ['*'],
                    'allowed_pages': ['dashboard', 'admin*', 'system*', 'exam*', 'user*', 'api*'],
                },
                'teacher': {
                    'allowed_routes': ['/dashboard', '/exam*', '/api/exam*', '/api/question*'],
                    'allowed_pages': ['dashboard', 'exam*', 'question*'],
                },
                'student': {
                    'allowed_routes': ['/dashboard', '/exam/*', '/api/exam/*'],
                    'allowed_pages': ['dashboard', 'exam*'],
                },
                'parent': {
                    'allowed_routes': ['/dashboard', '/api/parent/*'],
                    'allowed_pages': ['dashboard', 'parent*'],
                },
                'user': {
                    'allowed_routes': ['/dashboard', '/api/user/*'],
                    'allowed_pages': ['dashboard'],
                },
            },
            'CSP_POLICY': "default-src 'self' http://localhost:8888 http://127.0.0.1:8888 http://0.0.0.0:8888 http://192.168.0.0/16; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' http://localhost:8888 http://127.0.0.1:8888 http://0.0.0.0:8888 http://192.168.0.0/16; media-src 'self' data:;",
        }
        db_manager.init_defaults(security_extra_config, 'security')
        
        logger.info("[配置] 默认配置已初始化到数据库")


def get_database_path(db_name: str) -> Optional[str]:
    """获取数据库路径"""
    db_config = get_config_value('DATABASE_CONFIG', DATABASE_CONFIG)
    db_dir = db_config.get('DATABASE_DIR')
    db_info = db_config.get('DATABASES', {}).get(db_name)
    if db_dir and db_info:
        return os.path.join(db_dir, db_info.get('file', ''))
    return None


def get_database_role(db_name: str) -> str:
    """获取数据库角色"""
    db_config = get_config_value('DATABASE_CONFIG', DATABASE_CONFIG)
    db_info = db_config.get('DATABASES', {}).get(db_name)
    if db_info:
        return db_info.get('role', 'slave')
    return 'slave'


def load_config(config_type: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置
    优先从数据库读取配置,数据库中不存在的配置使用默认值
    支持从环境变量覆盖配置
    
    Args:
        config_type: 配置类型: 'production', 'development', 'test'
    
    Returns:
        合并后的配置字典
    """
    logger.info(f"加载配置类型: {config_type or '默认'}")
    
    config = DEFAULT_CONFIG.copy()
    
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            db_settings = db_manager.get_all()
            for key, value in db_settings.items():
                if key in config:
                    config[key] = value
                    logger.debug(f"[配置] 从数据库加载配置: {key}")
        except Exception as e:
            logger.warning(f"[配置] 从数据库加载配置失败: {str(e)}")
    
    env_overrides = [
        ('ENV', 'MTSCOS_ENV'),
        ('DEBUG', 'MTSCOS_DEBUG', bool),
        ('SECRET_KEY', 'MTSCOS_SECRET_KEY'),
        ('SERVER_HOST', 'MTSCOS_HOST'),
        ('SERVER_PORT', 'MTSCOS_PORT', int),
        ('LOG_LEVEL', 'MTSCOS_LOG_LEVEL'),
    ]
    
    for config_key, env_key, *converter in env_overrides:
        value = os.environ.get(env_key)
        if value is not None:
            if converter:
                try:
                    value = converter[0](value)
                except ValueError:
                    logger.warning(f"无法转换环境变量 {env_key} 的值: {value}")
                    continue
            config[config_key] = value
            logger.debug(f"[配置] 环境变量 {env_key} 覆盖配置 {config_key}")
    
    if config_type == 'production':
        config['DEBUG'] = False
        config['ENV'] = 'production'
        config['LOG_LEVEL'] = 'WARNING'
        logger.info("已切换到生产环境配置")
    
    elif config_type == 'test':
        config['DEBUG'] = True
        config['ENV'] = 'test'
        config['LOG_LEVEL'] = 'DEBUG'
        logger.info("已切换到测试环境配置")
    
    ConfigValidator.validate_config(config)
    ConfigValidator.validate_environment()
    
    return config


def get_config_value(key: str, default: Any = None) -> Any:
    """
    获取配置值
    优先从数据库读取,数据库中不存在则使用默认值
    """
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            value = db_manager.get(key)
            if value is not None:
                return value
        except Exception as e:
            logger.debug(f"[配置] 从数据库获取 {key} 失败: {str(e)}")
    
    return DEFAULT_CONFIG.get(key, default)


def get_config_category(category: str) -> Dict[str, Any]:
    """获取指定分类的所有配置"""
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            return db_manager.get_category(category)
        except Exception as e:
            logger.error(f"[配置] 获取分类 {category} 配置失败: {str(e)}")
    return {}


def update_config(key: str, value: Any, category: str = 'general', description: str = '') -> bool:
    """
    更新配置值
    同时更新数据库和内存中的配置
    """
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            success = db_manager.set(key, value, category, description)
            if success:
                DEFAULT_CONFIG[key] = value
                logger.info(f"[配置] 更新配置: {key} = {value}")
            return success
        except Exception as e:
            logger.error(f"[配置] 更新配置 {key} 失败: {str(e)}")
            return False
    
    DEFAULT_CONFIG[key] = value
    logger.info(f"[配置] 更新配置(内存): {key} = {value}")
    return True


def delete_config(key: str) -> bool:
    """删除配置"""
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            success = db_manager.delete(key)
            if success and key in DEFAULT_CONFIG:
                del DEFAULT_CONFIG[key]
            return success
        except Exception as e:
            logger.error(f"[配置] 删除配置 {key} 失败: {str(e)}")
            return False
    return False


def get_all_configs() -> Dict[str, Any]:
    """获取所有配置（包含数据库和默认配置）"""
    config = DEFAULT_CONFIG.copy()
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            db_settings = db_manager.get_all()
            config.update(db_settings)
        except Exception as e:
            logger.warning(f"[配置] 获取数据库配置失败: {str(e)}")
    return config


def get_all_configs_with_category() -> Dict[str, Dict[str, Any]]:
    """获取所有配置，按分类分组"""
    db_manager = get_db_config_manager()
    if db_manager:
        try:
            return db_manager.get_all_with_category()
        except Exception as e:
            logger.error(f"[配置] 获取所有配置失败: {str(e)}")
            return {}
    return {}


def refresh_config():
    """刷新配置（重新从数据库加载）"""
    db_manager = get_db_config_manager()
    if db_manager:
        db_manager.refresh_cache()
        logger.info("[配置] 配置已从数据库刷新")