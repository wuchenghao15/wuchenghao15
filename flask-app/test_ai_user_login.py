#!/usr/bin/env python3
"""
测试AI自动生成用户的登录功能

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.guest_user_manager import guest_user_manager
from app.models.user import User

def test_ai_user_login():
    """测试AI自动生成用户的登录功能"""
    print("=== 测试AI自动生成用户登录功能 ===")

    # 1. 生成AI自动用户
    print("1. 生成AI自动用户...")
    guest_user, guest_user_id, random_password = guest_user_manager.generate_guest_user()

    if not guest_user:
        print("❌ 生成AI用户失败")
        return False

    print(f"✅ 生成AI用户成功")
    print(f"   用户名: {guest_user.username}")
    print(f"   邮箱: {guest_user.email}")
    print(f"   用户ID: {guest_user_id}")
    print(f"   密码: {random_password}")

    # 2. 尝试使用生成的用户登录
    print("\n2. 测试登录功能...")

    test_username = guest_user.username

    # 尝试使用错误密码登录
    print(f"   尝试使用错误密码登录用户: {test_username}")
    wrong_user = User.verify_credentials(test_username, "wrong_password")
    if wrong_user:
        print("❌ 错误密码登录成功，这是一个问题")
    else:
        print("✅ 错误密码登录失败，符合预期")

    # 尝试使用正确密码登录
    print(f"   尝试使用正确密码登录用户: {test_username}")
    correct_user = User.verify_credentials(test_username, random_password)
    if correct_user:
        print("✅ 正确密码登录成功")
        print(f"   登录用户角色: {correct_user.role}")
        print(f"   登录用户状态: {'活跃' if correct_user.is_active else '非活跃'}")
    else:

    # 3. 检查数据库连接和用户存储
    print("\n3. 检查数据库中的用户...")
    db_user = User.get_by_username(test_username)
    if db_user:
        print(f"✅ 从数据库中获取用户成功: {db_user.username}")
        print(f"   用户角色: {db_user.role}")
        print(f"   用户状态: {'活跃' if db_user.is_active else '非活跃'}")
    else:

    return True

if __name__ == "__main__":
    success = test_ai_user_login()
    if success:
        print("\n=== 测试完成 ===")
    else:
        sys.exit(1)
