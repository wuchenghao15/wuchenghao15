#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试密码验证函数

import hashlib
import os

# 从app.py复制的密码验证函数
def verify_password(stored_password, provided_password):
    """验证密码，支持scrypt和pbkdf2_hmac两种格式"""
    try:
        # 检查是否为scrypt格式
        if stored_password.startswith('scrypt:'):
            # 使用werkzeug的security模块验证scrypt密码
            from werkzeug.security import check_password_hash
            return check_password_hash(stored_password, provided_password)
        else:
            # pbkdf2_hmac格式
            salt = bytes.fromhex(stored_password[:32])
            stored_hash = stored_password[32:]
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return stored_hash == provided_hash.hex()
    except Exception as e:
        print(f"[ERROR] 密码验证失败: {str(e)}")
        return False

# 测试scrypt格式密码
scrypt_password = "scrypt:32768:8:1$myGq6ShdhGBMJOXV$b0380302f18fad55c829e095d60e25e80e4120b829c33af8412573d082cda1ce15694bcc14a1ca3f38bac1645bd7f333fc0acd1c344c684f8576d1a8d7e6d106"
test_passwords = ["password", "admin", "test", "123456"]

print("测试scrypt格式密码验证:")
print(f"存储的密码: {scrypt_password}")
print("=" * 60)

for pwd in test_passwords:
    result = verify_password(scrypt_password, pwd)
    print(f"密码 '{pwd}' 验证结果: {result}")

# 测试pbkdf2_hmac格式密码
pbkdf2_password = "0198ffaa5d35ecdbd7306ddb67f8433999cc07e3b383fb9c57eab7f51dca5ccff597394b93bd09ebbd5336d98bc25f50"
print("\n测试pbkdf2_hmac格式密码验证:")
print(f"存储的密码: {pbkdf2_password}")
print("=" * 60)
for pwd in test_passwords:
    result = verify_password(pbkdf2_password, pwd)

# 测试直接使用werkzeug生成和验证密码
from werkzeug.security import generate_password_hash, check_password_hash
new_scrypt = generate_password_hash("admin")
print(f"生成的scrypt密码: {new_scrypt}")
print(f"验证 'admin': {check_password_hash(new_scrypt, 'admin')}")
print(f"验证 'password': {check_password_hash(new_scrypt, 'password')}")
