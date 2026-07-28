#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置服务 - 读取系统设置、安全设置、语言设置等
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = None


def set_database_path(path):
    """设置数据库路径"""
    global DATABASE_PATH
    DATABASE_PATH = path


def get_system_settings():
    """获取系统设置"""
    settings = {
        'system_name': 'MTSCOS AI 智能学习评估系统',
        'version': "14.0.0",
        'description': 'AI员工编排与集成版本，创建AI员工编排层连接专业角色→技能进化→独立思考→网络学习的自动化成长周期，实现14个子系统统一集成与仪表盘监控.',
        'admin_email': 'admin@example.com',
        'maintenance_mode': False,
        'auto_backup': True
    }
    try:
        db_path = DATABASE_PATH or 'app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, setting_value FROM system_settings WHERE category = "general"')
            rows = cursor.fetchall()
            for row in rows:
                key, value = row
                if key in settings:
                    if isinstance(settings[key], bool):
                        settings[key] = value.lower() == 'true'
                    elif isinstance(settings[key], int):
                        try:
                            settings[key] = int(value)
                        except Exception:
                            pass
                    else:
                        settings[key] = value
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
    return settings


def get_security_settings():
    """获取安全设置"""
    settings = {
        'max_login_attempts': 5,
        'lockout_duration': 5,
        'session_timeout': 30,
        'password_expiry_days': 90,
        'hardware_auth_enabled': True,
        'two_factor_auth': False,
        'login_logging': True,
        'ip_whitelist': False,
        'sql_protection': True,
        'xss_protection': True
    }
    try:
        db_path = DATABASE_PATH or 'app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, setting_value FROM system_settings WHERE category = "security"')
            rows = cursor.fetchall()
            for row in rows:
                key, value = row
                if key in settings:
                    if isinstance(settings[key], bool):
                        settings[key] = value.lower() == 'true'
                    elif isinstance(settings[key], int):
                        try:
                            settings[key] = int(value)
                        except Exception:
                            pass
                    else:
                        settings[key] = value
    except Exception as e:
        logger.error(f"获取安全设置失败: {e}")
    return settings


def get_language_settings():
    """获取语言设置"""
    settings = {
        'language': 'zh-CN',
        'test_language': 'japanese',
        'voice_type': 'standard'
    }
    try:
        db_path = DATABASE_PATH or 'app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, setting_value FROM system_settings WHERE category = "language"')
            rows = cursor.fetchall()
            for row in rows:
                key, value = row
                if key in settings:
                    settings[key] = value
    except Exception as e:
        logger.error(f"获取语言设置失败: {e}")
    return settings