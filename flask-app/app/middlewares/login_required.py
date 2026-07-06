# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
登录检查中间件,确保用户必须登录才能访问系统
"""

from flask import session, redirect, url_for, request
from app.utils.logging import logger
import logging


def login_required_middleware(app):
    """登录检查中间件,确保用户(包括游客)必须登录才能使用系统"""

    EXCLUDED_ROUTES = [
        'auth.auto_guest_login',
        'auth.login',
        'auth.register',
        'auth.logout',
        'auth.login_vikey',
        'main.index',
        'index',
        'main.vikey_driver_status',
        'main.vikey_install_driver',
        'monitoring.health',
        'static',
    ]

    STATIC_PATHS = ['/static/', '/assets/', '/webfonts/', '/audio/']
    
    AUTH_PATHS = ['/auth/login', '/auth/register', '/auth/logout']

    @app.before_request
    def check_login():
        """检查用户是否已登录"""
        endpoint = request.endpoint
        path = request.path

        if endpoint == 'static':
            return None

        if path.startswith('/api/'):
            return None

        for static_path in STATIC_PATHS:
            if path.startswith(static_path):
                return None
        
        for auth_path in AUTH_PATHS:
            if path == auth_path:
                return None

        if endpoint in EXCLUDED_ROUTES:
            return None

        if not session.get('logged_in'):
            return redirect(url_for('main.index'))

        return None

    return app


login_required_priority = 5