#!/usr/bin/env python3
"""
测试Flask应用是否能正常启动
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/auth/login')
def login():
    return "Login Page"

if __name__ == '__main__':
    print("启动测试Flask应用...")
    print("服务器将运行在 http://localhost:8888")
    app.run(host='localhost', port=8888, debug=True)