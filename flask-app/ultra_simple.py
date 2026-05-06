#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超简单Flask应用，只测试基本路由

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Ultra Simple Flask App!'

@app.route('/api/health')
def health_check():
    return {'status': 'ok', 'message': 'Ultra Simple Flask App is healthy'}

@app.route('/test')
def test():
    return 'Test route works!'

if __name__ == '__main__':
    print("启动超简单Flask应用...")
    print("访问地址:")
    print("  http://localhost:8000/")
    print("  http://localhost:8000/api/health")
    print("  http://localhost:8000/test")
    app.run(host='0.0.0.0', port=8000, debug=True)

"""