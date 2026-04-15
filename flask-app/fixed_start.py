#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的启动脚本，移除AI阻塞操作
"""

import os
import sys
import logging

# 设置基本日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 显式设置环境变量，禁用AI自我修复系统
os.environ['AI_SELF_HEALING_ENABLED'] = 'false'

# 导入应用
print("导入应用前设置环境变量完成...")
from app import app

# 显式设置端口为8888
PORT = 8888

if __name__ == '__main__':
    print(f"Starting Flask app on http://0.0.0.0:{PORT}...")
    try:
        app.run(host='0.0.0.0', port=PORT, debug=True)
    except KeyboardInterrupt:
        print("Flask app stopped.")
    except Exception as e:
        print(f"Error starting Flask app: {str(e)}")
        import traceback
        traceback.print_exc()
