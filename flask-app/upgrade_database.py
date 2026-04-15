#!/usr/bin/env python3
"""
数据库升级脚本
用于初始化和升级数据库表结构
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.config import Config
from app.utils.logging import logger


def upgrade_database():
    """
    升级数据库
    - 初始化users表
    - 检查其他表结构
    """
    try:
        logger.info("开始升级数据库...")
        logger.info(f"使用数据库文件: {Config.DATABASE_PATH}")
        
        # 1. 创建用户表
        logger.info("正在创建/检查users表...")
        User.create_table()
        
        # 2. 这里可以添加其他表的创建逻辑
        # 例如：
        # from app.models.other import OtherModel
        # OtherModel.create_table()
        
        logger.info("数据库升级成功！")
        return True
        
    except Exception as e:
        logger.error(f"数据库升级失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = upgrade_database()
    sys.exit(0 if success else 1)
