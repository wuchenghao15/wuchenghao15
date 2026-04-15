#!/usr/bin/env python3
"""
创建测试用户的简单脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入User模型和security_utils，绕过应用初始化
try:
    from app.models.user import User
    from app.utils.security import security_utils
    print("✓ 成功导入User模型和security_utils")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 创建测试用户
def create_test_user():
    """创建测试用户"""
    username = "testuser"
    email = "test@example.com"
    password = "Test123!@#"
    
    # 检查用户是否已存在
    try:
        existing_user = User.get_by_username(username)
        if existing_user:
            print(f"✗ 用户 {username} 已存在")
            return False
    except Exception as e:
        print(f"✗ 检查用户是否存在失败: {e}")
        print("  继续创建用户...")
    
    # 哈希密码
    hashed_password = security_utils.hash_password(password)
    print(f"✓ 密码哈希成功")
    
    # 创建用户
    try:
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role='user',
            is_active=1,  # 直接设置为激活状态
            super_admin_approved=1,  # 直接设置为已批准
            hardware_admin_approved=1  # 直接设置为已批准
        )
        user_id = user.save()
        if user_id:
            print(f"✓ 测试用户创建成功!")
            print(f"  用户名: {username}")
            print(f"  密码: {password}")
            print(f"  邮箱: {email}")
            print(f"  用户ID: {user_id}")
            return True
        else:
            print(f"✗ 用户创建失败")
            return False
    except Exception as e:
        print(f"✗ 创建用户失败: {e}")
        return False

if __name__ == "__main__":
    print("开始创建测试用户...")
    create_test_user()
