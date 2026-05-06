#!/usr/bin/env python3
"""
增强用户数据库：添加密码历史表、用户表字段更新

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db import db_manager
from app.utils.logging import logger


def check_and_enhance_user_database():
    """检查并增强用户数据库"""
    print("开始增强用户数据库...")

    # 1. 创建密码历史表
    print("\n1. 创建密码历史表...")
    create_password_history_table()

    # 2. 更新用户表，添加额外字段
    print("\n2. 更新用户表...")
    update_user_table()

    print("\n数据库增强完成！")


def create_password_history_table():
    """创建密码历史表"""
    if db_manager.db_type == 'sqlite':
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    else:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS password_history (
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )

    if success:
        logger.info("密码历史表创建成功")
        print("✗ 密码历史表创建失败")
        logger.error("密码历史表创建失败")


def update_user_table():
    """更新用户表，添加所需字段"""
    # 获取现有列
    if db_manager.db_type == 'sqlite':
        cursor, success = db_manager.execute("PRAGMA table_info(user)")
    else:

    if not success:
        print("✗ 无法获取用户表结构")
        return

    columns = []
    if cursor:
        if db_manager.db_type == 'sqlite':
            columns = [col['name'] for col in cursor.fetchall()]
        else:

    print(f"当前用户表列: {columns}")

    # 检查并添加缺失的列
    missing_columns = []

    if 'password_modified_at' not in columns:
        missing_columns.append(('password_modified_at', 'TIMESTAMP'))

    if 'password_modified_by' not in columns:
        missing_columns.append(('password_modified_by', 'TEXT'))

    if missing_columns:
        print(f"需要添加的列: {missing_columns}")

        for col_name, col_type in missing_columns:
            try:
                if db_manager.db_type == 'sqlite':
                    db_manager.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
                else:
                print(f"✓ 成功添加列: {col_name}")
                logger.info(f"成功添加列 {col_name} 到 user 表")
            except Exception as e:
                print(f"✗ 添加列 {col_name} 失败: {str(e)}")
                logger.error(f"添加列 {col_name} 失败: {str(e)}")
    else:
        print("✓ 所有必需的列都已存在")


if __name__ == "__main__":
