#!/usr/bin/env python3
"""
登录检查中间件，确保用户必须登录才能访问系统

from flask import session, redirect, url_for, request
from app.utils.logging import logger


def login_required_middleware(app):
    登录检查中间件，确保用户（包括游客）必须登录才能使用系统

    Args:
        app: Flask应用实例

    # 不需要登录的路由列表
    EXCLUDED_ROUTES = [
        'auth.auto_guest_login',  # 游客登录路由
        'auth.login',  # 用户登录路由
        'auth.register',  # 用户注册路由
        'auth.logout',  # 登出路由
        'auth.login_vikey',  # Vikey登录路由
        'main.index',  # 首页路由
        'main.vikey_driver_status',  # Vikey驱动状态路由
        'main.vikey_install_driver',  # Vikey驱动安装路由
        'monitoring.health',  # 健康检查路由
        'static',  # 静态文件路由
    ]

    @app.before_request
    def check_login():
        检查用户是否已登录
        # 获取当前请求的端点
        endpoint = request.endpoint

        # 获取当前请求的URL路径
        path = request.path

        # 检查是否为静态文件请求
        if endpoint == 'static':
            return None

        # 检查是否为API请求
        if path.startswith('/api/'):
            # API请求不需要登录检查
            return None

        # 检查是否在排除列表中
        if endpoint in EXCLUDED_ROUTES:
            return None
        # 检查会话中是否有登录状态
        if not session.get('logged_in'):
            # 未登录，重定向到首页
            return redirect(url_for('main.index'))

        # 已登录，继续处理请求
        return None

    return app


login_required_priority = 5

"""