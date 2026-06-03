# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
完全独立的Flask服务器,不依赖app包中的复杂组件

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用,不导入任何app包中的模块
try:
    from flask import Flask, render_template, redirect, url_for, session, flash, request
    app = Flask(__name__)

    # 配置模板目录和静态目录
    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    # 设置密钥,用于会话管理
    app.secret_key = 'dev-secret-key'

    # 健康检查路由
    @app.route('/health')
    def health():
        return "OK", 200

    # 根路由,渲染index.html
    @app.route('/')
    def index():
        logger.info("[独立服务器] 渲染index.html")
        # 简单的版本号
        versions = {'system_version': '1.1.0'}
        return render_template('index.html', versions=versions)

    # 登录页路由
    @app.route('/auth/login', methods=['GET', 'POST'])
    def login():
        logger.info("[独立服务器] 访问登录页")
        if request.method == 'GET':
            return render_template('login.html')
        else:
            # 简单的登录处理,不连接数据库
            username = request.form.get('username')
            password = request.form.get('password')
            if username and password:
                # 简单验证,实际应用中需要连接数据库
                session['logged_in'] = True
                session['username'] = username
                session['user_level'] = 'user'
                flash('登录成功', 'success')
                return redirect(url_for('index'))
            else:
                return render_template('login.html')
    # 注册页路由
    @app.route('/auth/register', methods=['GET'])
    def register():
        logger.info("[独立服务器] 访问注册页")
        return render_template('register.html')

    # 登出路由
    @app.route('/auth/logout')
    def logout():
        logger.info("[独立服务器] 登出")
        session.clear()
        flash('登出成功', 'success')
        return redirect(url_for('index'))

    # 游客登录路由(缺失的路由)
    def auto_guest_login():
        logger.info("[独立服务器] 游客登录")
        # 简单的游客登录处理
        session['logged_in'] = True
        session['username'] = 'guest'
        session['user_level'] = 'guest'
        flash('游客登录成功', 'success')
        return redirect(url_for('index'))

    # JS AI 代码路由(缺失的路由)
    @app.route('/get_js_ai_code')
        logger.info("[独立服务器] 获取JS AI代码")
        # 简单的JS代码返回
        js_code = "// AI功能不可用,这是一个占位脚本\nconsole.log('AI功能不可用');"
        return js_code, 200, {'Content-Type': 'application/javascript'}

    logger.info("[独立服务器] Flask应用创建成功!")
except Exception as e:
    logger.error(f"[独立服务器] 创建Flask应用失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 启动服务器
if __name__ == '__main__':
    try:
        import argparse
        parser = argparse.ArgumentParser(description='完全独立的Flask服务器')
        parser.add_argument('--port', type=int, default=8888, help='服务器端口')
        parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机')
        args = parser.parse_args()

        host = args.host
        port = args.port
        debug = False

        # 打印所有注册的路由
        logger.info("[独立服务器] 已注册的路由:")
        for rule in app.url_map.iter_rules():
            logger.info(f"  - {rule}")

        logger.info(f"[独立服务器] 启动服务器...")
        logger.info(f"[独立服务器] 服务器地址: http://{host}:{port}")
        logger.info(f"[独立服务器] 调试模式: {debug}")

        # 运行Flask服务器
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except Exception as e:
        logger.error(f"[独立服务器] 启动服务器失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""