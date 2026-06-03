# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
简化版服务器启动脚本 - 包含认证和语言测试功能
"""

from flask import Flask, render_template
import logging
import os
import traceback

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app.secret_key = 'mtscos_ai_project_secret_key'


@app.route('/')
def index():
    """根路由"""
    return render_template('index.html')


@app.route('/health')
def health():
    """健康检查路由"""
    return "OK", 200


try:
    from app.views.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print("[INFO] 认证蓝图注册成功")
except Exception as e:
    print(f"[ERROR] 认证蓝图注册失败: {str(e)}")
    traceback.print_exc()

try:
    from app.views.language_tests import language_tests_bp
    app.register_blueprint(language_tests_bp, url_prefix='')
    print("[INFO] 语言测试蓝图注册成功")
except Exception as e:
    print(f"[ERROR] 语言测试蓝图注册失败: {str(e)}")
    traceback.print_exc()

try:
    from app.views.main import main_bp
    app.register_blueprint(main_bp, url_prefix='')
    print("[INFO] 主蓝图注册成功")
except Exception as e:
    print(f"[ERROR] 主蓝图注册失败: {str(e)}")
    traceback.print_exc()

if __name__ == '__main__':
    print("[INFO] 正在启动简化版Flask服务器...")
    app.run(host='0.0.0.0', port=8888, debug=True)
