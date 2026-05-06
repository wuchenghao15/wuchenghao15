#!/usr/bin/env python3
"""
更新用户组别脚本

from app.utils.db import db_manager
from app.utils.logging import logger

def update_user_group(username, group_name):
    更新用户组别

    Args:
        username: 用户名
        group_name: 组别名称
    try:
        # 获取用户ID
        user = db_manager.fetch_one(
            'SELECT id FROM users WHERE username = ?',
            (username,)
        )

        if not user:
            logger.error(f"用户 {username} 不存在")
            return False

        user_id = user[0]
        logger.info(f"用户 {username} 的ID: {user_id}")

        # 检查用户组别表是否存在
        try:
            db_manager.execute('SELECT 1 FROM user_groups LIMIT 1')
        except Exception:
            logger.info("创建user_groups表")
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS user_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    group_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

        # 检查用户是否已在组别中
            'SELECT id FROM user_groups WHERE user_id = ?',
            (user_id,)
        )

        if existing:
            # 更新现有记录
                'UPDATE user_groups SET group_name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (group_name, user_id)
            )
            logger.info(f"更新用户 {username} 的组别为 {group_name}")
        else:
            # 插入新记录
                'INSERT INTO user_groups (user_id, group_name) VALUES (?, ?)',
                (user_id, group_name)
            )
            logger.info(f"添加用户 {username} 到组别 {group_name}")

        return True
        return False

if __name__ == "__main__":
    # 更新designer1用户的组别为designer
    update_user_group('designer1', 'designer')

"""