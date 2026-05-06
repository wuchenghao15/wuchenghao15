#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超简单的Flask应用，只返回index.html，使用端口8888

from flask import Flask, render_template
import os

# 创建Flask应用实例
app = Flask(__name__)

# 配置模板目录
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# 配置静态文件目录
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

@app.route('/')
def index():
    """首页路由，返回index.html"""
    return render_template('index.html')

if __name__ == '__main__':
    PORT = 8888
    print(f"Starting simple Flask app on http://0.0.0.0:{PORT}...")
    try:
        app.run(host='0.0.0.0', port=PORT, debug=True)
    except KeyboardInterrupt:
        print("Flask app stopped.")
    except Exception as e:
        print(f"Error starting Flask app: {str(e)}")
        import traceback
        traceback.print_exc()
