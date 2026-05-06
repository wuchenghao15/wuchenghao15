#!/usr/bin/env python3
"""
最小化的MTSCOS AI服务器

import os
import sys
from flask import Flask, render_template, session, redirect, url_for, flash, request

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'mtscos_secret_key'

# 配置模板目录
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# 创建主蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页路由"""
    return render_template('index.html',
                       user={'username': session.get('username', 'guest'), 'role': session.get('user_level', 'guest')})

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录路由"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            # 简单的模拟登录
            session['logged_in'] = True
            session['username'] = username
            session['user_level'] = 'user'
            flash('登录成功', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('请输入用户名和密码', 'danger')
    return render_template('index.html',

def logout():
    """登出路由"""
    session.clear()
    flash('登出成功', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/register')
    """注册路由"""
    flash('注册功能开发中', 'info')
    return redirect(url_for('auth.login'))

# 注册蓝图
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# 添加健康检查路由
@app.route('/health')
def health():
    """健康检查路由"""
    return "OK", 200

# 添加测试路由
@app.route('/test')
def test():
    """测试路由"""
    return "Test OK", 200

# 启动服务器
if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8888
    print(f"Starting minimal MTSCOS server on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)
