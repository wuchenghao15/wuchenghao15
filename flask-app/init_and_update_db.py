#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始化并更新数据库脚本
1. 创建必要的表
2. 运行数据库更新脚本

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.models.system_config import SystemConfig
from app.models.local_data import LocalData
from app.config import Config

print("初始化并更新数据库...")

# 1. 确保数据库目录存在
if not os.path.exists(os.path.dirname(Config.DATABASE_PATH)):
    os.makedirs(os.path.dirname(Config.DATABASE_PATH))
    print(f"✓ 创建数据库目录: {os.path.dirname(Config.DATABASE_PATH)}")

# 2. 创建用户表
print("\n1. 创建用户表...")
User.create_table()

# 3. 创建系统配置表
print("\n2. 创建系统配置表...")
SystemConfig.create_table()

# 4. 创建本地数据上传表
print("\n3. 创建本地数据上传表...")
LocalData.create_table()

# 4. 运行数据库更新脚本
print("\n3. 运行数据库更新脚本...")
os.system("python3 update_database.py")

print("\n✅ 数据库初始化和更新完成！")

"""