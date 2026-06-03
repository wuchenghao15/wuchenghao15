# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
检查登录失败问题的脚本

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

def check_user_login(username, password):
    检查用户登录问题
    print(f"=== 检查用户登录问题: {username} ===")

    # 1. 检查用户是否存在
    print("\n1. 检查用户是否存在...")
    db_path = os.path.abspath('app.db')
    print(f"连接数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查用户表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("❌ 用户表不存在")
            return

        # 先检查用户表结构
        print("检查用户表结构...")
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"用户表列: {column_names}")

        # 构建查询语句,只查询存在的列
        available_columns = ['id', 'username', 'email', 'password', 'role', 'is_active']
        selected_columns = [col for col in available_columns if col in column_names]
        select_sql = ', '.join(selected_columns)

        # 尝试通过用户名查询用户
        print(f"查询用户: {username}")
        cursor.execute(f'SELECT {select_sql} FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()

        # 如果用户名不存在,尝试通过其他可能的字段查询
        if not user_data:
            # 检查是否有phone列
            if 'phone' in column_names:
                print(f"用户名不存在,尝试通过手机号查询: {username}")
                cursor.execute(f'SELECT {select_sql} FROM users WHERE phone = ?', (username,))
                user_data = cursor.fetchone()
            # 检查是否有email列
            if not user_data and 'email' in column_names:
                cursor.execute(f'SELECT {select_sql} FROM users WHERE email = ?', (username,))
                user_data = cursor.fetchone()

        if user_data:
            user_info = dict(zip(selected_columns, user_data))
            user_id = user_info.get('id')
            username = user_info.get('username')
            email = user_info.get('email')
            stored_password = user_info.get('password')
            role = user_info.get('role')
            is_active = user_info.get('is_active', 1)
            phone = user_info.get('phone', 'N/A')

            print(f"✅ 用户存在: {username}, ID: {user_id}, 角色: {role}, 状态: {'激活' if is_active else '未激活'}")
            print(f"   邮箱: {email}, 手机号: {phone}")

            # 2. 检查用户状态
            print("\n2. 检查用户状态...")
            if not is_active:
                print("❌ 用户未激活")
            else:
                print("✅ 用户已激活")

            # 3. 检查密码
            print("\n3. 检查密码...")
            print(f"   存储的密码长度: {len(stored_password)}")

            # 检查是否是明文密码
            if len(stored_password) < 80:
                print("   密码是明文格式")
                if stored_password == password:
                    print("✅ 明文密码匹配")
                else:
                    print("❌ 明文密码不匹配")
            else:
                print("   密码是哈希格式")
                try:
                        print("✅ 哈希密码验证成功")
                except Exception as e:
                    print(f"❌ 哈希验证出错: {str(e)}")

            # 4. 检查用户是否在黑名单
            cursor.execute('SELECT id FROM user_blacklist WHERE username = ? AND is_active = 1', (username,))
            if cursor.fetchone():
                print("❌ 用户在黑名单中")
            else:
                print("✅ 用户不在黑名单中")

        else:
            print("❌ 用户不存在")


    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python check_login_issue.py <用户名> <密码>")
        sys.exit(1)

    username = sys.argv[1]

    check_user_login(username, password)

"""