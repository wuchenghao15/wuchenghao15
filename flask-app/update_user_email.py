#!/usr/bin/env python3
"""
更新用户邮箱
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.utils.logging import logger

def update_user_email(username, new_email):
    """
    更新用户邮箱
    
    Args:
        username: 用户名
        new_email: 新邮箱
    
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    try:
        logger.info(f"开始更新用户 {username} 的邮箱为 {new_email}...")
        
        # 获取用户
        user = User.get_by_username(username)
        if not user:
            logger.error(f"用户 {username} 不存在")
            return False
        
        # 更新邮箱
        user.email = new_email
        user.save()
        
        logger.info(f"用户 {username} 的邮箱已更新为 {new_email}")
        return True
    except Exception as e:
        logger.error(f"更新用户 {username} 的邮箱失败: {str(e)}")
        return False

def check_user(username):
    """
    检查用户信息
    
    Args:
        username: 用户名
    
    Returns:
        bool: 检查成功返回True，失败返回False
    """
    try:
        user = User.get_by_username(username)
        if user:
            logger.info(f"用户 {username} 信息: 用户ID: {user.user_id}, 邮箱: {user.email}, 角色: {user.role}, 激活状态: {user.is_active}")
            return True
        else:
            logger.error(f"用户 {username} 不存在")
            return False
    except Exception as e:
        logger.error(f"检查用户 {username} 信息失败: {str(e)}")
        return False

def main():
    """
    主函数，更新普通用户的邮箱
    """
    # 更新普通用户的邮箱
    update_result = update_user_email(
        username="caopw",
        new_email="2@2.com"
    )
    
    if update_result:
        # 检查更新后的用户信息
        check_user("caopw")
        # 检查硬件管理员的信息
        check_user("wuchenghao15")
        logger.info("用户邮箱更新成功")
        return 0
    else:
        logger.error("用户邮箱更新失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
