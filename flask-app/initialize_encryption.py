#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库加密初始化脚本
用于加密现有数据库中的敏感数据并设置加密表结构
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.encrypted_db_manager import encrypted_db_manager
from app.utils.encryption import encryption_manager

def initialize_encryption():
    """初始化数据库加密"""
    print("=== 数据库加密初始化 ===")
    print(f"加密密钥已配置: {encryption_manager.fernet_key[:10]}...")
    
    print("\n1. 加密现有数据...")
    try:
        encrypted_db_manager.encrypt_existing_data()
        print("   ✓ 现有数据加密完成")
    except Exception as e:
        print(f"   ✗ 加密失败: {e}")
    
    print("\n2. 查看加密配置...")
    print("   加密表列表:", encrypted_db_manager.encrypted_tables)
    print("   加密列配置:", encrypted_db_manager.encrypted_columns)
    
    print("\n3. 测试加密功能...")
    test_data = {"test": "敏感数据", "password": "secret123", "email": "test@example.com"}
    encrypted = encryption_manager.encrypt(test_data)
    decrypted = encryption_manager.decrypt(encrypted)
    print(f"   原始数据: {test_data}")
    print(f"   加密后: {encrypted[:50]}...")
    print(f"   解密后: {decrypted}")
    print(f"   ✓ 加密/解密测试通过: {test_data == decrypted}")
    
    print("\n=== 数据库加密初始化完成 ===")

if __name__ == '__main__':
    initialize_encryption()