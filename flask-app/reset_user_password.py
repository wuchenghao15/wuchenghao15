# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
重置用户密码的脚本

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import os
import sys
from app.utils.security import security_utils
from app.utils.logging import logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reset_user_password(username, new_password):
    重置用户密码
    print(f"=== 重置用户密码: {username} ===")

    # 连接数据库
    db_path = os.path.abspath('app.db')
    print(f"连接数据库: {db_path}")

    try:
        with sqlite3.connect(sqlite3.connect(db_path)) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()
            
            if not user_data:
            print("❌ 用户不存在")
            return
            
            user_id = user_data[0]
            print(f"✅ 用户存在,ID: {user_id}")
            
            # 生成新的哈希密码
            hashed_password = security_utils.hash_password(new_password)
            print(f"生成新的哈希密码,长度: {len(hashed_password)}")
            
            # 更新密码
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
            conn.commit()
            
            print("✅ 密码重置成功")
            print(f"用户 {username} 的密码已重置为: {new_password}")
            

    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python reset_user_password.py <用户名> <新密码>")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]

    reset_user_password(username, new_password)

"""