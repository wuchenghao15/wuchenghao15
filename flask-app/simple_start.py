#!/usr/bin/env python3
"""
简化的启动脚本，直接启动Flask应用

# 只导入必要的模块
from flask import Flask

# 创建一个简单的Flask应用
app = Flask(__name__)

# 定义一个简单的路由
@app.route('/')
def index():
    return "MTSCOS AI Project is running!"

@app.route('/api/health')
def health_check():
    return {
        "status": "healthy",
        "message": "MTSCOS AI Project API is running",
        "timestamp": "2026-03-23"
    }

if __name__ == '__main__':
    print("=== 简化启动脚本 ===")
    print("启动Flask服务器...")
    print("访问地址: http://localhost:8888")
    print("健康检查: http://localhost:8888/api/health")

    # 直接启动服务器，不进行任何额外初始化
    app.run(host='0.0.0.0', port=8888, debug=True)

"""