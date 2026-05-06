#!/usr/bin/env python3
import sqlite3
from cryptography.fernet import Fernet
# JSON import removed - using database
# 读取加密密钥
with open('encryption.key', 'rb') as f:
    ENCRYPTION_KEY = f.read()

fernet = Fernet(ENCRYPTION_KEY)

# 加密函数
def encrypt_data(data):
    """加密敏感数据"""
    if not data:
        return data
    if isinstance(data, str):
        data_bytes = data.encode()
    else:
        data_bytes = str(data).encode()
    encrypted_bytes = fernet.encrypt(data_bytes)
    return encrypted_bytes.decode()

# 连接到数据库
conn = sqlite3.connect('primary.db')
cursor = conn.cursor()

# 用户ID和新密码
user_id = 19
new_password = 'xuxu2pipo'

# 加密新密码
encrypted_password = encrypt_data(new_password)

# 更新用户密码
cursor.execute('UPDATE users SET password = ? WHERE id = ?', (encrypted_password, user_id))
conn.commit()

# 验证更新结果
cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
user = cursor.fetchone()

if user:
    print(f"用户 {user[1]} 的密码更新成功！")
    print("用户未找到！")

conn.close()
