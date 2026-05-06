#!/usr/bin/env python3
"""
简单脚本，用于检查数据库中用户表的内容

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.utils.db import db_manager

    # 查询用户表的所有记录
    print("查询用户表内容...")
    users = db_manager.fetch_all('SELECT id, username, email, password, role, is_active FROM user')

    print("\n用户表内容:")
    print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'密码哈希(前30字符)':<35} {'角色':<15} {'激活状态':<10}")
    print("-" * 120)

    for user in users:
        user_id, username, email, password, role, is_active = user
        password_preview = password[:30] if password else "空"
        print(f"{user_id:<5} {username:<20} {email:<30} {password_preview:<35} {role:<15} {is_active:<10}")

        # 检查密码长度和格式
        if password:
            print(f"  密码长度: {len(password)}, 格式: {'hex' if all(c in '0123456789abcdefABCDEF' for c in password) else '其他'}")

    # 测试特定用户的密码验证
    print("\n测试密码验证...")
    from app.utils.security import security_utils

    # 假设我们有一个用户名为'admin'的用户
    test_username = 'admin'
    test_password = 'admin123'  # 替换为实际的测试密码

    # 获取该用户的密码哈希
    admin_user = db_manager.fetch_one('SELECT password FROM user WHERE username = ?', (test_username,))
    if admin_user:
        admin_password = admin_user[0]
        print(f"测试用户 '{test_username}' 的密码验证:")
        print(f"  存储的密码哈希: {admin_password}")
        print(f"  测试密码: {test_password}")

        # 尝试验证
        result = security_utils.verify_password(admin_password, test_password)
        print(f"  验证结果: {'成功' if result else '失败'}")

        # 手动测试不同的验证方法
        print("  手动测试不同验证方法:")

        # 1. 测试hex格式
        try:
                salt_hex = admin_password[:32]
                hash_hex = admin_password[32:]
                salt = bytes.fromhex(salt_hex)
                stored_hash = bytes.fromhex(hash_hex)

                import hashlib
                hashed = hashlib.pbkdf2_hmac('sha256', test_password.encode('utf-8'), salt, 100000)
                hex_result = hashed == stored_hash
                print(f"    hex格式验证: {'成功' if hex_result else '失败'}")
            else:
                print(f"    hex格式验证: 跳过 (长度 {len(admin_password)} 不符合64或96字符)")
        except Exception as e:
            print(f"    hex格式验证: 异常 - {str(e)}")

        # 2. 测试werkzeug格式
        try:
            werkzeug_result = check_password_hash(admin_password, test_password)
            print(f"    werkzeug格式验证: {'成功' if werkzeug_result else '失败'}")
        except Exception as e:
            print(f"    werkzeug格式验证: 异常 - {str(e)}")

        # 3. 测试base64格式
        try:
            decoded = base64.b64decode(admin_password)
            salt = decoded[:32]
            stored_hash = decoded[32:]

            from app.config import Config
            import hashlib
            hashed = hashlib.pbkdf2_hmac(Config.HASH_ALGORITHM, test_password.encode('utf-8'), salt, Config.HASH_ITERATIONS)
            base64_result = hashed == stored_hash
            print(f"    base64格式验证: {'成功' if base64_result else '失败'}")
            print(f"    base64格式验证: 异常 - {str(e)}")
    else:
        print(f"未找到测试用户 '{test_username}'")

except Exception as e:
    print(f"错误: {str(e)}")
    traceback.print_exc()

"""