# -*- coding: utf-8 -*-
# User Management Server - 配置文件
import secrets
from datetime import timedelta

class Config:
    # 基本配置
    SECRET_KEY = secrets.token_hex(32)  # 生成随机密钥
    DATABASE_PATH = 'user_management.db'  # 用户管理数据库

    # 安全配置
    DEBUG = False  # 生产环境关闭调试模式

    # JWT配置
    JWT_EXPIRATION = 3600  # JWT过期时间（秒）
    JWT_ALGORITHM = 'HS256'  # JWT算法

    # 密码策略
    PASSWORD_MIN_LENGTH = 8  # 最小密码长度
    PASSWORD_MAX_LENGTH = 64  # 最大密码长度
    PASSWORD_REQUIRE_UPPER = True  # 要求大写字母
    PASSWORD_REQUIRE_LOWER = True  # 要求小写字母
    PASSWORD_REQUIRE_DIGIT = True  # 要求数字
    PASSWORD_REQUIRE_SPECIAL = True  # 要求特殊字符

    # API安全配置
    API_KEY_HEADER = 'X-API-Key'  # API密钥头部
    API_KEY_EXPIRATION_DAYS = 365  # API密钥有效期（天）

    # 速率限制配置
    RATE_LIMIT_ENABLED = True  # 启用速率限制
    RATE_LIMIT_PER_MINUTE = 100  # 每分钟请求数限制
    RATE_LIMIT_PER_HOUR = 1000  # 每小时请求数限制

    # IP白名单配置
    IP_WHITELIST_ENABLED = False  # 启用IP白名单
    IP_WHITELIST = ['127.0.0.1', '::1']  # IP白名单

    # 日志配置
    LOG_LEVEL = 'INFO'  # 日志级别
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # 日志格式

    # 双因素认证配置
    TWO_FACTOR_ENABLED = False  # 启用双因素认证
    TWO_FACTOR_ISSUER = 'MTSCOS User Management'  # 双因素认证发行者

    # HTTPS配置
    HTTPS_ENABLED = False  # 启用HTTPS
    SSL_CERT_PATH = 'cert.pem'  # SSL证书路径
    SSL_KEY_PATH = 'key.pem'  # SSL密钥路径

    # 安全头配置
    SECURE_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-src 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
