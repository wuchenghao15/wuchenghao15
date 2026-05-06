#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查wuchenghao15用户的信息，确认其角色

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User

print("=== 检查用户信息 ===")

# 获取wuchenghao15用户信息
user = User.get_by_username('wuchenghao15')

if user:
    print(f"用户ID: {user.user_id}")
    print(f"用户名: {user.username}")
    print(f"邮箱: {user.email}")
    print(f"角色: {user.role}")
    print(f"激活状态: {'已激活' if user.is_active else '未激活'}")
    print(f"超级管理员批准: {'已批准' if user.super_admin_approved else '未批准'}")
    print(f"硬件管理员批准: {'已批准' if user.hardware_admin_approved else '未批准'}")
else:
    print("未找到用户 wuchenghao15")

print("\n=== 检查完成 ===")

"""