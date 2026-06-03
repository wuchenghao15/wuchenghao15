# -*- coding: utf-8 -*-
# Configuration Management System - 支持多数据库分离
"""
统一管理系统配置,支持从多种来源加载配置
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ==================== 基础配置 ====================
BASE_CONFIG = {
    'ENV': 'development',
    'DEBUG': True,
    'SECRET_KEY': 'dev-secret-key',
    'VERSION': '3.0.0',
    'BUILD_NUMBER': 5678,
    'BUILD_DATE': '2026-03-03',
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
    
    # L1 内存缓存
    'CACHE_L1_ENABLED': True,
    'CACHE_L1_MAX_SIZE': 1000,
    'CACHE_L1_TTL': 300,
    'CACHE_L1_POLICY': 'lru',
    
    # L2 文件缓存
    'CACHE_L2_ENABLED': True,
    'CACHE_L2_DIR': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cache/l2',
    'CACHE_L2_MAX_SIZE': 100 * 1024 * 1024,
    'CACHE_L2_TTL': 3600,
    
    # L3 数据库缓存
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

class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """验证配置的完整性和正确性"""
        errors = []
        
        # 验证必要配置项
        required_keys = ['SECRET_KEY', 'SERVER_HOST', 'SERVER_PORT', 'DATABASE_DIR']
        for key in required_keys:
            if key not in config or not config[key]:
                errors.append(f"缺少必要配置项: {key}")
        
        # 验证端口范围
        port = config.get('SERVER_PORT', 0)
        if not (1 <= port <= 65535):
            errors.append(f"无效的端口号: {port}")
        
        # 验证缓存目录
        if config.get('CACHE_L2_ENABLED'):
            cache_dir = config.get('CACHE_L2_DIR', '')
            if cache_dir and not os.path.isdir(cache_dir):
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                    logger.info(f"创建缓存目录: {cache_dir}")
                except Exception as e:
                    errors.append(f"无法创建缓存目录: {cache_dir}, 错误: {str(e)}")
        
        # 验证数据库目录
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
        
        # 验证Python版本
        import sys
        if sys.version_info < (3, 8):
            errors.append("Python版本需要3.8或更高")
        
        if errors:
            for error in errors:
                logger.error(f"环境验证失败: {error}")
            return False
        
        logger.info("环境验证通过")
        return True

def get_database_path(db_name: str) -> Optional[str]:
    """获取数据库路径"""
    db_dir = DEFAULT_CONFIG.get('DATABASE_DIR')
    db_info = DEFAULT_CONFIG.get('DATABASES', {}).get(db_name)
    if db_dir and db_info:
        return os.path.join(db_dir, db_info.get('file', ''))
    return None

def get_database_role(db_name: str) -> str:
    """获取数据库角色"""
    db_info = DEFAULT_CONFIG.get('DATABASES', {}).get(db_name)
    if db_info:
        return db_info.get('role', 'slave')
    return 'slave'

def load_config(config_type: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置
    支持从环境变量和配置文件覆盖默认配置
    
    Args:
        config_type: 配置类型: 'production', 'development', 'test'
    
    Returns:
        合并后的配置字典
    """
    logger.info(f"加载配置类型: {config_type or '默认'}")
    
    # 从环境变量加载配置
    config = DEFAULT_CONFIG.copy()
    
    # 环境变量覆盖
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
            logger.debug(f"环境变量 {env_key} 覆盖配置 {config_key}")
    
    # 根据配置类型调整配置
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
    
    # 验证配置
    ConfigValidator.validate_config(config)
    ConfigValidator.validate_environment()
    
    return config

def get_config_value(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return DEFAULT_CONFIG.get(key, default)

def update_config(key: str, value: Any) -> None:
    """更新配置值"""
    DEFAULT_CONFIG[key] = value
    logger.info(f"配置更新: {key} = {value}")