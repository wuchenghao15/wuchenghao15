#!/usr/bin/env python3
"""
测试登录逻辑的简化脚本

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 测试登录逻辑 ===")

# 1. 测试User.verify_credentials方法
print("\n1. 测试User.verify_credentials方法...")
try:
    from app.models.user import User

    # 测试用户名密码验证
    username = "test_user"
    password = "Test123!"

    print(f"测试用户: {username}, 密码: {password}")
    user = User.verify_credentials(username, password)
    if user:
        print(f"✓ 验证成功，用户ID: {user.user_id}")
    else:
        print(f"✗ 验证失败")

    # 测试错误密码
    wrong_password = "WrongPass123!"
    print(f"测试用户: {username}, 错误密码: {wrong_password}")
    user = User.verify_credentials(username, wrong_password)
    if not user:
        print(f"✓ 错误密码验证失败，符合预期")
    else:

    # 测试错误用户名
    wrong_username = "wrong_user"
    print(f"测试错误用户名: {wrong_username}, 密码: {password}")
    user = User.verify_credentials(wrong_username, password)
    if not user:
        print(f"✓ 错误用户名验证失败，符合预期")

except Exception as e:
    print(f"✗ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 2. 测试verification_utils.verify_all_factors方法
print("\n2. 测试verification_utils.verify_all_factors方法...")
try:

    username = "test_user"
    password = "Test123!"
    print(f"测试所有因素验证: {username}, 密码: {password}")
    print(f"结果: {is_valid}, 消息: {message}")

    # 测试错误密码
    print(f"测试所有因素验证(错误密码): {username}, 密码: WrongPass123!")
    is_valid, message = verification_utils.verify_all_factors(username, "WrongPass123!")
    print(f"结果: {is_valid}, 消息: {message}")

except Exception as e:
    import traceback
    traceback.print_exc()

# 3. 测试密码哈希
try:

    password = "Test123!"
    hashed = security_utils.hash_password(password)
    print(f"密码: {password}")
    print(f"哈希值: {hashed}")
    # 测试验证
    is_valid = security_utils.verify_password(password, hashed)
    if is_valid:
        print(f"✓ 密码验证成功")
    else:
        print(f"✗ 密码验证失败")

except Exception as e:
    print(f"✗ 测试失败: {str(e)}")
    import traceback

print("\n=== 测试完成 ===")

"""