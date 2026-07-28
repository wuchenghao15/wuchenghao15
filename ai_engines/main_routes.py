# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""路由配置模块"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.version import VERSION, VERSION_INFO, get_version_info, get_latest_version
import json
import sys

logger = logging.getLogger(__name__)

class RouteManager:
    def __init__(self, app=None):
        self.app = app
        self.blueprints = {}
        self.routes = []
        logger.info("路由管理器初始化完成")

    def init_app(self, app):
        self.app = app
        self._register_core_routes()
        logger.info("路由应用初始化完成")

    def _register_core_routes(self):
        main_bp = Blueprint('main', __name__)
        auth_bp = Blueprint('auth', __name__)
        api_bp = Blueprint('api', __name__, url_prefix='/api')

        @main_bp.route('/')
        def index():
            version_info = get_version_info()
            latest_version = get_latest_version()
            return render_template('index.html', 
                                version=VERSION,
                                version_info=version_info,
                                latest_version=latest_version)

        @main_bp.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html')

        @main_bp.route('/test')
        def test():
            return jsonify({'status': 'success', 'message': '系统运行正常'})

        @auth_bp.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                data = request.get_json()
                if data and 'username' in data and 'password' in data:
                    username = data.get('username')
                    password = data.get('password')
                    if username == 'admin' and password == 'admin123':
                        return jsonify({'success': True, 'message': '登录成功', 'session_id': 'test_session_123'})
                    else:
                        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
                return jsonify({'success': False, 'message': '参数错误'}), 400
            return render_template('login.html')

        @auth_bp.route('/register', methods=['GET', 'POST'])
        def register():
            if request.method == 'POST':
                data = request.get_json()
                if data and 'username' in data and 'password' in data:
                    return jsonify({'success': True, 'message': '注册成功'})
                return jsonify({'success': False, 'message': '参数错误'}), 400
            return render_template('register.html')

        @auth_bp.route('/logout', methods=['POST'])
        def logout():
            return jsonify({'success': True, 'message': '登出成功'})

        @api_bp.route('/health')
        def health():
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

        @api_bp.route('/user', methods=['GET'])
        def get_user():
            session_id = request.headers.get('X-Session-ID')
            if session_id:
                return jsonify({'success': True, 'user': {'id': 1, 'username': 'admin', 'role': 'admin'}})
            return jsonify({'success': False, 'message': '未授权'}), 401

        @api_bp.route('/system/status')
        def system_status():
            return jsonify({'status': 'running', 'version': '4.5.5', 'timestamp': datetime.now().isoformat()})

        self.app.register_blueprint(main_bp)
        self.app.register_blueprint(auth_bp, url_prefix='/auth')
        self.app.register_blueprint(api_bp)
        logger.info("核心路由注册完成")

    def add_route(self, rule, view_func, methods=None):
        if methods is None:
            methods = ['GET']
        self.app.add_url_rule(rule, view_func.__name__, view_func, methods=methods)
        self.routes.append({'rule': rule, 'methods': methods})

    def register_all_routes(self, app):
        self.app = app
        self._register_core_routes()

route_manager = RouteManager()

def init_routes():
    logger.info("初始化路由...")
    logger.info("路由初始化完成")

if __name__ == "__main__":
    pass