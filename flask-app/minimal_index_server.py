#!/usr/bin/env python3
"""
极简的索引服务器，只提供index.html的访问

from flask import Flask, render_template
import os

# 创建Flask应用
app = Flask(__name__)

# 配置模板目录
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 主路由，渲染index.html模板
@app.route('/')
def index():
    return render_template('index.html')

# 健康检查路由
@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    print("=== 极简索引服务器启动 ===")
    print("访问地址: http://localhost:8888")
    print("健康检查: http://localhost:8888/health")
    print("按 Ctrl+C 停止服务器")
    print("==========================")
    app.run(host='0.0.0.0', port=8888, debug=True)

"""