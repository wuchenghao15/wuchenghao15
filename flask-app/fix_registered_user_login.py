#!/usr/bin/env python3
"""修复已注册用户登录问题"""

from app.models.user import User
from app.utils.security import security_utils
from app.ai.user_ai_manager import user_ai_manager

print("=== 修复已注册用户登录问题 ===")

# 检查所有用户并修复密码（如果需要）
users = User.get_all_users()
print(f"\n1. 系统中共有 {len(users)} 个用户")

# 定义默认密码映射
password_map = {
    "wuchenghao15": "LoginMe.1988",
    "caopw": "xuxu2pipo",
    "admin": "LoginMe.1988"
}

for user in users:
    print(f"\n2. 处理用户: {user.username} ({user.role})")
    print(f"   激活状态: {user.is_active}")

    # 检查密码是否正确
    default_password = password_map.get(user.username, "LoginMe.1988")
    is_valid = security_utils.verify_password(user.password, default_password)
    print(f"   当前密码 '{default_password}' 验证: {'✅' if is_valid else '❌'}")

    if not is_valid:
        # 修复密码
        print(f"   修复密码为: {default_password}")
        hashed_password = security_utils.hash_password(default_password)
        user.password = hashed_password
        user.save()
        print(f"   ✅ 密码已修复")

        # 验证修复后的密码
        updated_user = User.get_by_username(user.username)
        is_valid = security_utils.verify_password(updated_user.password, default_password)
        print(f"   修复后密码验证: {'✅' if is_valid else '❌'}")

    # 测试登录
    print(f"   测试登录...")
    login_result = user_ai_manager.process_login_request(user.username, default_password)
    if login_result['success']:
        print(f"   ✅ 登录成功")
    else:
        print(f"   ❌ 登录失败: {login_result['message']}")

print("\n=== 修复完成 ===")
print("\n用户登录信息:")
print("- 管理员: admin / LoginMe.1988")
print("- 硬件管理员: wuchenghao15 / LoginMe.1988")
print("- 普通用户: caopw / xuxu2pipo")
