#!/usr/bin/env python3
"""
最小化Flask应用启动脚本，用于测试基本功能
from flask import Flask, jsonify

# 创建一个简单的Flask应用
app = Flask(__name__)

# 添加一个简单的路由
@app.route('/')
def index():
    return "Hello, World! This is a minimal Flask app."

# 添加一个健康检查路由
@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Flask app is running"}), 200

# 运行应用
if __name__ == "__main__":
    host = '0.0.0.0'
    port = 8888
    print(f"Starting minimal Flask app on {host}:{port}...")
    app.run(host=host, port=port, debug=False)

"""