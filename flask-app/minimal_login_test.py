#!/usr/bin/env python3
"""
最小化的登录测试应用
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'test_secret_key'

# 配置模板目录
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 简单的根路由
@app.route('/')
def index():
    return render_template('index.html')

# 登录路由
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """简单的登录测试路由"""
    if request.method == 'GET':
        return render_template('login.html')
    
    # POST请求处理
    username = request.form.get('username')
    password = request.form.get('password')
    
    print(f"收到登录请求: 用户名={username}, 密码={password}")
    
    # 测试登录逻辑
    try:
        from app.models.user import User
        from app.utils.verification import verification_utils
        
        # 首先测试User.verify_credentials
        print("测试User.verify_credentials...")
        user = User.verify_credentials(username, password)
        print(f"User.verify_credentials结果: {user}")
        
        if user:
            # 测试verification_utils.verify_all_factors
            print("测试verification_utils.verify_all_factors...")
            is_valid, message = verification_utils.verify_all_factors(username, password)
            print(f"verification_utils.verify_all_factors结果: {is_valid}, {message}")
            
            if is_valid:
                # 登录成功
                session['logged_in'] = True
                session['username'] = username
                flash('登录成功', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'登录失败: {message}', 'danger')
        else:
            flash('用户名或密码错误', 'danger')
            
    except Exception as e:
        print(f"登录过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'登录失败: {str(e)}', 'danger')
    
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("[INFO] 启动最小化登录测试应用...")
    print("[INFO] 应用将运行在 http://localhost:5001")
    app.run(host='localhost', port=5001, debug=True)