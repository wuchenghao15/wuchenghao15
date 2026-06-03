# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
检查应用的路由映射

import logging
logger = logging.getLogger(__name__)
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 禁用dotenv加载
os.environ['FLASK_SKIP_DOTENV'] = '1'

# 导入应用
from app import app

# 打印所有路由
print("应用路由映射:")
for rule in app.url_map.iter_rules():
    print(f"  {rule}")

"""