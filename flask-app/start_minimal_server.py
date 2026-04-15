#!/usr/bin/env python3
"""
最小化启动服务器，只运行最基本的Flask应用
"""

import os

# 移除所有环境变量，避免影响
for key in list(os.environ.keys()):
    if key.startswith('MODEL_PATH') or key.startswith('DEFAULT_CONFIG'):
        del os.environ[key]

# 创建一个最小化的Flask应用
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World! Server is running on port 8888", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    print("Starting minimal Flask server on port 8888...")
    app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False)
