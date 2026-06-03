# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import hashlib
import base64

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def hash_password(password):
    """使用SHA-256 + Base64编码哈希密码"""
    pwd_hash = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(pwd_hash).decode()

def change_user_password(username, new_password):
    """修改用户密码"""
    hashed_password = hash_password(new_password)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ 用户 '{username}' 不存在")
            return False
        
        # 更新密码
        cursor.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
        conn.commit()
        
        print(f"✅ 用户 '{username}' 的密码已成功更新")
        print(f"   用户ID: {user[0]}")
        print(f"   新密码: {new_password}")
        return True

if __name__ == '__main__':
    username = 'caopw'
    new_password = 'xuxu4pipo'
    
    change_user_password(username, new_password)
