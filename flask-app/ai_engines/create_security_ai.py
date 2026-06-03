# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建安全保安AI
负责项目数字安全、数据库安全、本地缓存数据安全和项目后门漏洞安全
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_security_ai():
    """创建安全保安AI"""
    db_path = "app.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        security_ai = {
            "ai_name": "security_ai",
            "instance_id": "security_ai",
            "collection_id": "main_ai_ensemble",
            "ai_type": "security",
            "name": "安全保安AI",
            "description": "专门负责项目数字安全、数据库安全、本地缓存数据安全和项目后门漏洞安全,保护数据、中间件、cookie、session等安全",
            "functions": str([
                "digital_security",
                "database_security",
                "cache_security",
                "vulnerability_scanning",
                "data_protection",
                "middleware_security",
                "session_security",
                "cookie_security",
                "encryption",
                "threat_detection"
            ]),
            "responsibilities": str([
                "数字安全防护",
                "数据库安全保护",
                "本地缓存数据安全",
                "项目后门漏洞检测",
                "数据传输加密",
                "中间件安全监控",
                "Session安全管理",
                "Cookie安全保护",
                "威胁检测与响应",
                "安全漏洞扫描"
            ]),
            "config": str({
                "security_level": "high",
                "encryption_algorithm": "AES-256",
                "scanning_interval": 300,
                "alert_threshold": 0.8,
                "security_rules": {
                    "database": {
                        "query_monitoring": True,
                        "injection_detection": True,
                        "access_control": True
                    },
                    "session": {
                        "timeout": 3600,
                        "regeneration": True,
                        "validation": True
                    },
                    "cookie": {
                        "secure": True,
                        "same_site": "strict"
                    },
                    "middleware": {
                        "output_encoding": True,
                        "rate_limiting": True
                    }
                }
            }),
            "status": "active",
            "bound_user": "admin"
        }

        sql = """
        INSERT OR REPLACE INTO ai_instances
        (ai_name, instance_id, collection_id, ai_type, name, description,
         functions, responsibilities, status, config, bound_user, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

        params = (
            security_ai["ai_name"],
            security_ai["instance_id"],
            security_ai["collection_id"],
            security_ai["ai_type"],
            security_ai["name"],
            security_ai["description"],
            security_ai["functions"],
            security_ai["responsibilities"],
            security_ai["status"],
            security_ai["config"],
            security_ai["bound_user"]
        )

        cursor.execute(sql, params)
        conn.commit()

        print("安全保安AI创建成功!")
        print(f"AI名称: {security_ai['name']}")
        print(f"类型: {security_ai['ai_type']}")
        print(f"状态: {security_ai['status']}")

        config_dict = eval(security_ai['config'])
        print(f"安全级别: {config_dict['security_level']}")
        print(f"加密算法: {config_dict['encryption_algorithm']}")

        create_security_tables(cursor)

        conn.close()
        return True

    except Exception as e:
        print(f"创建安全保安AI失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_security_tables(cursor):
    """创建安全相关的表"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        source TEXT,
        ip_address TEXT,
        user_agent TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        details TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target TEXT NOT NULL,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        status TEXT DEFAULT 'running',
        findings TEXT,
        severity TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key TEXT UNIQUE NOT NULL,
        config_value TEXT NOT NULL,
        description TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    initial_configs = [
        ("encryption_key", "your-secure-encryption-key", "数据加密密钥"),
        ("session_timeout", "3600", "Session超时时间(秒)"),
        ("block_duration", "300", "登录失败后阻塞时间(秒)"),
        ("api_rate_limit", "100", "API速率限制(次/分钟)"),
        ("enable_csrf_protection", "true", "启用CSRF保护"),
        ("enable_xss_protection", "true", "启用XSS保护"),
        ("enable_content_security_policy", "true", "启用内容安全策略")
    ]

    for config_key, config_value, description in initial_configs:
        cursor.execute('''
        INSERT OR REPLACE INTO security_configs (config_key, config_value, description)
        VALUES (?, ?, ?)
        ''', (config_key, config_value, description))

    print("安全相关表创建成功!")


if __name__ == "__main__":
    create_security_ai()
