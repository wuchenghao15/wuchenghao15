#!/usr/bin/env python3
"""
Simple Flask app start script for MTSCOS AI Project

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# 创建Flask应用
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key-for-development'

# 定义简单的健康检查路由
@app.route('/health')
def health():
    return "OK", 200

# 定义版本路由
@app.route('/version')
def version():
    return {"VERSION": "3.0.0", "INTERNAL_VERSION": "3.0.0.5678"}, 200

# 定义根路由
@app.route('/')
def index():
    return "Hello World from MTSCOS AI Project!", 200

if __name__ == '__main__':
    print("[INFO] 启动简单Flask应用...")
    print("[INFO] 监听地址: 0.0.0.0:8888")
    print("[INFO] 访问地址: http://localhost:8888")

    # 启动服务器
    app.run(host='0.0.0.0', port=8888, debug=True, use_reloader=False)

"""