# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建用户脚本
"""
import logging
logger = logging.getLogger(__name__)
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.utils.security import security_utils

def main():
    try:
        print("正在创建用户...")

        print("\n1. 创建硬件管理员用户...")
        hardware_admin_username = "wuchenghao15"
        hardware_admin_email = "1@1.com"
        hardware_admin_password = "LoginMe.1988"

        existing_user = User.get_by_username(hardware_admin_username)
        if existing_user:
            print(f"用户 {hardware_admin_username} 已存在,跳过创建")
        else:
            hashed_password = security_utils.hash_password(hardware_admin_password)

            hardware_admin = User(
                username=hardware_admin_username,
                email=hardware_admin_email,
                password=hashed_password,
                role="hardware_vikey_admin",
                is_active=1,
                super_admin_approved=1,
                hardware_admin_approved=1
            )

            user_id = hardware_admin.save()
            if user_id:
                print(f"硬件管理员用户创建成功,用户ID: {user_id}")
            else:
                print("硬件管理员用户创建失败")

        print("\n2. 创建普通用户...")
        normal_username = "caopw"
        normal_email = "1@1.com"
        normal_password = "xuxu2pipo"

        existing_user = User.get_by_username(normal_username)
        if existing_user:
            print(f"用户 {normal_username} 已存在,跳过创建")
        else:
            hashed_password = security_utils.hash_password(normal_password)
            normal_user = User(
                username=normal_username,
                email=normal_email,
                password=hashed_password,
                role="user",
                super_admin_approved=1,
                hardware_admin_approved=1
            )

            user_id = normal_user.save()
            if user_id:
                print(f"普通用户创建成功,用户ID: {user_id}")
            else:
                print("普通用户创建失败")

        all_users = User.get_all_users()
        for user in all_users:
            print(f"- 用户ID: {user.user_id}, 用户名: {user.username}, 角色: {user.role}, 邮箱: {user.email}, 激活状态: {user.is_active}")
        print("\n用户创建完成!")

    except Exception as e:
        print(f"创建用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
