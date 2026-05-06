#!/usr/bin/env python3
"""
完整测试游客用户登录功能，包括使用正确的密码登录

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.guest_user_manager import guest_user_manager
from app.models.user import User


def test_guest_login_full():
    """完整测试游客用户登录"""
    print("=== 完整测试游客用户登录 ===")

    # 生成游客用户
    print("1. 生成游客用户...")

    # 注意：我们需要修改guest_user_manager.generate_guest_user方法，让它返回原始密码
    # 或者我们可以直接修改测试脚本，使用已知的密码生成逻辑

    # 生成随机游客用户名
    import uuid
    guest_username = f"guest_{uuid.uuid4().hex[:8]}"
    guest_email = f"{guest_username}@guest.example.com"
    random_password = uuid.uuid4().hex[:16]

    # 手动创建游客用户，这样我们可以知道密码
    from app.utils.security import security_utils
    hashed_password = security_utils.hash_password(random_password)

    from app.models.user import User
        username=guest_username,
        email=guest_email,
        password=hashed_password,
        role='guest',
        is_active=1,
        super_admin_approved=1,
        hardware_admin_approved=1
    )

    # 保存游客用户
    guest_user_id = guest_user.save()

    if not guest_user_id:
        print("❌ 生成游客用户失败")
        return False

    print(f"✅ 生成游客用户成功")
    print(f"   用户名: {guest_username}")
    print(f"   邮箱: {guest_email}")
    print(f"   密码: {random_password}")
    print(f"   哈希密码: {hashed_password}")

    # 测试1：使用错误的密码
    print("\n2. 测试用户验证...")
    print("   测试1: 使用错误的密码")
    user = User.verify_credentials(guest_username, "wrong_password")
    if not user:
        print("   ✅ 错误密码验证失败，符合预期")
    else:
        print("   ❌ 错误密码验证成功，不符合预期")
        return False

    print("   测试2: 使用正确的密码")
    user = User.verify_credentials(guest_username, random_password)
    if user:
        print(f"   ✅ 正确密码验证成功，用户ID: {user.user_id}")
        print(f"   用户角色: {user.role}")
    else:
        print("   ❌ 正确密码验证失败，不符合预期")
        return False
    print("   测试3: 验证用户信息")
    if user.username == guest_username and user.role == 'guest' and user.is_active == 1:
        print("   ✅ 用户信息验证成功")
    else:
        print("   ❌ 用户信息验证失败")
        return False

    return True


if __name__ == "__main__":
    test_guest_login_full()
