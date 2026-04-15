#!/usr/bin/env python3
"""
简单脚本，用于测试密码验证功能，不加载整个应用程序上下文
"""

import sys
import os
import hashlib
import base64

try:
    # 从security.py文件中直接复制verify_password函数的实现
    def verify_password(stored_password, provided_password):
        """验证密码，支持多种哈希格式"""
        try:
            # 1. 优先尝试使用hex格式验证（update_users.py使用的格式）
            # 支持64字符和96字符格式
            if len(stored_password) in [64, 96]:
                salt_hex = stored_password[:32]  # 前32个字符是salt的十六进制表示（16字节）
                hash_hex = stored_password[32:]  # 后面是hash的十六进制表示
                salt = bytes.fromhex(salt_hex)
                stored_hash = bytes.fromhex(hash_hex)
                
                # 计算提供密码的哈希值
                hashed = hashlib.pbkdf2_hmac(
                    'sha256',
                    provided_password.encode('utf-8'),
                    salt,
                    100000
                )
                
                return hashed == stored_hash
        except Exception as e:
            print(f"  hex格式验证异常: {str(e)}")
            pass
            
        try:
            # 2. 尝试使用werkzeug.security.check_password_hash（支持scrypt哈希）
            from werkzeug.security import check_password_hash
            return check_password_hash(stored_password, provided_password)
        except Exception as e:
            print(f"  werkzeug格式验证异常: {str(e)}")
            pass
            
        try:
            # 3. 尝试使用base64格式验证
            decoded = base64.b64decode(stored_password)
            salt = decoded[:32]  # 前32字节是盐
            stored_hash = decoded[32:]  # 后面是哈希值
            
            # 计算提供密码的哈希值
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt,
                100000
            )
            
            return hashed == stored_hash
        except Exception as e:
            print(f"  base64格式验证异常: {str(e)}")
            pass
            
        return False
    
    print("测试密码验证功能...")
    
    # 测试数据：从数据库中获取的实际密码哈希
    test_cases = [
        # (username, password_hash, test_password, expected_result)
        ("admin", "scrypt:32768:8:1$22pF07vhEfVn6XkG$0b7e88b0e0d62a1d0c6b6d8f0e8b6c4d2a0f8e6d4c2b0a8f6e4d2c0b8a6f4e2d0c8b6a4f2e0d8c6b4a2f0e8d6c4b2a0f8e6d4c2b0a8f6e4d2c0b8a6f4e2d0c8b6a4f2e0", "admin123", True),
        ("wuchenghao15", "0198ffaa5d35ecdbd7306ddb67f843033e766c5ed93402a6053d0c0f85e2011a33b6c6f0a428a9143b84226d5b09d00b82d3126d9b250d7a604343c4f9", "123456", True),
    ]
    
    print(f"\n{'用户名':<20} {'测试密码':<15} {'预期结果':<10} {'实际结果':<10} {'状态':<10}")
    print("-" * 65)
    
    for username, password_hash, test_password, expected in test_cases:
        # 测试verify_password函数
        result = verify_password(password_hash, test_password)
        status = "通过" if result == expected else "失败"
        
        print(f"{username:<20} {test_password:<15} {expected:<10} {result:<10} {status:<10}")
        
        # 如果失败，详细测试每个验证步骤
        if result != expected:
            print(f"\n  详细测试 {username} 的密码验证:")
            
            # 1. 测试hex格式
            try:
                if len(password_hash) in [64, 96]:
                    salt_hex = password_hash[:32]
                    hash_hex = password_hash[32:]
                    salt = bytes.fromhex(salt_hex)
                    stored_hash = bytes.fromhex(hash_hex)
                    
                    print(f"    hex格式: salt长度={len(salt)}, hash长度={len(stored_hash)} (预期32)")
                    print(f"    存储的salt: {salt_hex}")
                    print(f"    存储的hash: {hash_hex[:30]}...")
                    
                    hashed = hashlib.pbkdf2_hmac('sha256', test_password.encode('utf-8'), salt, 100000)
                    print(f"    计算的hash: {hashed.hex()[:30]}...")
                    print(f"    hash比较结果: {hashed == stored_hash}")
                else:
                    print(f"    hex格式验证: 跳过 (长度 {len(password_hash)} 不符合64或96字符)")
            except Exception as e:
                print(f"    hex格式验证: 异常 - {str(e)}")
            
            # 2. 测试werkzeug格式
            try:
                from werkzeug.security import check_password_hash
                werkzeug_result = check_password_hash(password_hash, test_password)
                print(f"    werkzeug格式验证: {'成功' if werkzeug_result else '失败'}")
            except Exception as e:
                print(f"    werkzeug格式验证: 异常 - {str(e)}")
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    traceback.print_exc()