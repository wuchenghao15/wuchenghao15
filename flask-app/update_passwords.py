#!/usr/bin/env python3
"""
更新数据库中的明文密码为哈希密码

import sqlite3
import os
from app.utils.security import security_utils
from app.utils.logging import logger

def update_passwords():
    """更新数据库中的明文密码为哈希密码"""
    try:
        # 连接数据库
        db_path = os.path.abspath('app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询所有用户
        cursor.execute('SELECT id, username, password FROM users')
        users = cursor.fetchall()

        updated_count = 0

        for user_id, username, password in users:
            # 检查是否是明文密码（长度小于80）
            if len(password) < 80:
                print(f"更新用户 {username} 的密码...")
                print(f"当前密码: {password}")

                # 生成哈希密码
                hashed_password = security_utils.hash_password(password)
                print(f"哈希密码: {hashed_password}")

                # 更新数据库
                cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
                updated_count += 1

        # 提交更改
        conn.commit()
        conn.close()

        print(f"\n更新完成！共更新了 {updated_count} 个用户的密码")
        logger.info(f"更新了 {updated_count} 个用户的密码为哈希格式")

    except Exception as e:
        logger.error(f"更新密码失败: {str(e)}")
        print(f"更新密码失败: {str(e)}")

if __name__ == "__main__":
    update_passwords()
