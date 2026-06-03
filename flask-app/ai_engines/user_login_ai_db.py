# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户登录AI数据库初始化模块

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.db import db_manager
from app.utils.logging import logger
import logging

def init_login_ai_tables():
    初始化用户登录AI所需的数据库表
    try:
        # 创建用户登录历史表
        db_manager.execute('''
        CREATE TABLE IF NOT EXISTS user_login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_group TEXT DEFAULT 'default'
        )
        ''')

        # 创建登录尝试表
        db_manager.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            reason TEXT,
        )

        db_manager.execute('''
        CREATE TABLE IF NOT EXISTS ip_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reason TEXT,
            is_active INTEGER DEFAULT 1,
        )
        ''')

        # 创建用户黑名单表
        db_manager.execute('''
        CREATE TABLE IF NOT EXISTS user_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        # 创建用户组别表
        db_manager.execute('''
        CREATE TABLE IF NOT EXISTS user_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT DEFAULT 'default',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')
        logger.info("用户登录AI数据库表初始化成功")
        logger.error(f"用户登录AI数据库表初始化失败: {str(e)}")

    添加用户到组别

    Args:
        user_id: 用户ID
        group_name: 组别名称
    Returns:
        bool: 是否添加成功
    try:
        existing = db_manager.fetch_one(
            'SELECT id FROM user_groups WHERE user_id = ?',

        if existing:
            # 更新现有记录
            db_manager.execute(
                'UPDATE user_groups SET group_name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (group_name, user_id)
            )
        else:
            # 插入新记录
            db_manager.execute(
                'INSERT INTO user_groups (user_id, group_name) VALUES (?, ?)',
                (user_id, group_name)
            )

        logger.info(f"用户 {user_id} 已添加到组别 {group_name}")
        return True
    except Exception as e:
        logger.error(f"添加用户到组别失败: {str(e)}")
        return False

def get_group_users(group_name):
    获取组别中的所有用户

    Args:
        group_name: 组别名称

    Returns:
        list: 用户ID列表
    try:
        users = db_manager.fetch_all(
            'SELECT user_id FROM user_groups WHERE group_name = ?',
            (group_name,)
        )
        return [user[0] for user in users]
    except Exception as e:
        return []

    获取用户组别统计信息

    Returns:
        dict: 组别统计信息
    try:
            'SELECT group_name, COUNT(*) as user_count FROM user_groups GROUP BY group_name'
        )
        result = {}
            result[group] = count
        return result
    except Exception as e:
        return {}

if __name__ == "__main__":
    init_login_ai_tables()
    # 测试添加用户到组别
    add_user_to_group(1, "admin")
    add_user_to_group(2, "user")
    add_user_to_group(3, "user")

    # 测试获取组别统计
    stats = get_user_group_stats()
    print("用户组别统计:", stats)

"""