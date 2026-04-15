#!/usr/bin/env python3
"""
生成密码哈希的简单脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入安全工具
from app.utils.security import security_utils

# 生成密码哈希
password = "Test123!@#"
hashed_password = security_utils.hash_password(password)

print(f"密码: {password}")
print(f"哈希值: {hashed_password}")
