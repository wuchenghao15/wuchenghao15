#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单启动脚本，使用固定端口8888
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入应用
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
