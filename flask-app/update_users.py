#!/usr/bin/env python3
"""
更新用户信息脚本
"""

import psycopg2
import hashlib
import os
import dotenv

# 密码加密函数
def encrypt_password(password):
    """加密密码"""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + hashed.hex()

# 加载环境变量
dotenv.load_dotenv()

# 获取数据库连接
def get_db_connection():
    """获取数据库连接"""
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', 5432),
        database=os.environ.get('DB_NAME', 'mtscos_db'),
        user=os.environ.get('DB_USER', 'mtscos_user'),
        password=os.environ.get('DB_PASSWORD', 'SecurePassword123!')
    )
    return conn

# 初始化数据库
def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 表创建已经在init.sql中完成，这里只做验证
    cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'user'")
    user_table_exists = cursor.fetchone() is not None
    
    cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'user_backup'")
    backup_table_exists = cursor.fetchone() is not None
    
    print(f"[INFO] 数据库初始化检查 - 用户表: {'存在' if user_table_exists else '不存在'}")
    print(f"[INFO] 数据库初始化检查 - 用户备份表: {'存在' if backup_table_exists else '不存在'}")
    
    conn.commit()
    conn.close()

# 更新或创建用户
def update_or_create_user(username, role, password, email=None):
    """更新或创建用户"""
    if not email:
        email = f"{username}@example.com"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查用户是否存在
    cursor.execute('SELECT id FROM "user" WHERE username = %s', (username,))
    user = cursor.fetchone()
    
    # 加密密码
    encrypted_password = encrypt_password(password)
    
    if user:
        user_id = user[0]  # PostgreSQL返回元组，不是字典
        # 更新现有用户
        cursor.execute('''
            UPDATE "user" 
            SET role = %s, password = %s, updated_at = NOW() 
            WHERE username = %s
        ''', (role, encrypted_password, username))
        
        # 更新备份表
        cursor.execute('''
            INSERT INTO user_backup (id, username, email, password, role, is_active, updated_at)
            VALUES (%s, %s, %s, %s, %s, true, NOW())
            ON CONFLICT (id) DO UPDATE SET
                username = EXCLUDED.username,
                email = EXCLUDED.email,
                password = EXCLUDED.password,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
        ''', (user_id, username, email, encrypted_password, role))
        
        print(f"用户 {username} 已更新")
    else:
        # 创建新用户
        cursor.execute('''
            INSERT INTO "user" (username, email, password, role, is_active)
            VALUES (%s, %s, %s, %s, true)
            RETURNING id
        ''', (username, email, encrypted_password, role))
        
        # 获取插入的ID
        user_id = cursor.fetchone()[0]
        
        # 插入到备份表
        cursor.execute('''
            INSERT INTO user_backup (id, username, email, password, role, is_active, updated_at)
            VALUES (%s, %s, %s, %s, %s, true, NOW())
        ''', (user_id, username, email, encrypted_password, role))
        
        print(f"用户 {username} 已创建")
    
    conn.commit()
    conn.close()

# 主函数
if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 更新或创建第一个用户：wuchenghao15，硬件管理员权限，密码 LoginMe.1988
    update_or_create_user('wuchenghao15', 'hardware_admin', 'LoginMe.1988')
    
    # 更新或创建第二个用户：caopw，学生权限，密码 xuxu4pipo
    update_or_create_user('caopw', 'student', 'xuxu4pipo')
    
    print("用户信息更新完成！")