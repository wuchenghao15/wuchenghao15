#!/usr/bin/env python3
"""
纯净的启动脚本，直接创建Flask应用并注册必要的蓝图，跳过所有复杂的初始化

import sys
import os
from flask import Flask, request, render_template

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建一个全新的Flask应用，不依赖于app/__init__.py中的复杂初始化
print("创建纯净的Flask应用...")
app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 设置基本配置
app.config['SECRET_KEY'] = 'simple-secret-key-for-development'
app.config['JSON_AS_ASCII'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True

# 创建一个简单的auth蓝图
from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """简单的登录页面"""
    if request.method == 'GET':
        return render_template('login.html')
    return "登录处理"

@auth_bp.route('/register')
def register():
    """简单的注册页面"""
    return render_template('register.html')

@auth_bp.route('/auto_guest_login')
def auto_guest_login():
    """简单的自动游客登录"""
    return "游客登录处理"

# 创建一个简单的main蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    return "欢迎访问MTSCOS AI Project"

@main_bp.route('/get_js_ai_code')
def get_js_ai_code():
    """提供AI相关的JavaScript代码"""
    return "// AI JavaScript代码"

# 注册蓝图
print("注册蓝图...")
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# 打印路由信息
print("\n应用路由:")
for rule in app.url_map.iter_rules():
    print(f"  - {rule}")

# 启动服务器
print("\n启动服务器...")
print("📌 服务器将在 http://localhost:8888 上运行")
print("📌 登录页面地址: http://localhost:8888/auth/login")
app.run(host='127.0.0.1', port=8888, debug=True, use_reloader=False)
