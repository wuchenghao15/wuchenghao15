#!/usr/bin/env python3
"""
检查数据库中的现有用户
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.utils.logging import logger

def check_users():
    """
    检查数据库中的现有用户
    """
    try:
        logger.info("开始检查现有用户...")
        
        # 获取所有用户
        users = User.get_all_users()
        
        logger.info(f"数据库中共有 {len(users)} 个用户")
        
        for user in users:
            logger.info(f"用户ID: {user.user_id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}, 激活状态: {user.is_active}")
        
        return 0
    except Exception as e:
        logger.error(f"检查用户失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(check_users())
