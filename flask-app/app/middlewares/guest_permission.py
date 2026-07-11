# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
游客用户权限中间件
限制游客用户只能访问考试和语言测试相关的功能
"""

from flask import session, redirect, url_for, flash, request
from functools import wraps
from app.utils.logging import logger
import logging
import sys

class GuestPermissionMiddleware:
    """游客用户权限中间件"""

    @staticmethod
    def require_guest_permission():
        """检查游客用户权限的装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    if session.get('is_guest'):
                        allowed_routes = [
                            'language_tests.test_system',
                            'language_tests.test_system_japanese',
                            'language_tests.test_system_english',
                            'language_tests.test_system_japanese_test',
                            'language_tests.test_system_english_test',
                            'language_tests.start_test',
                            'language_tests.submit_test',
                            'language_tests.test_result',
                            'auth.logout',
                            'auth.confirm_guest_logout',
                            'main.test_center',
                            'main.japanese_test',
                            'main.japanese_level_test',
                            'main.english_test',
                            'main.combined_test'
                        ]

                        current_route = request.endpoint
                        logger.info(f"当前路由: {current_route}")

                        if current_route not in allowed_routes:
                            logger.warning(f"游客用户 {session.get('username')} 尝试访问受限路由: {current_route}")
                            flash('游客用户只能参加考试和语言等级测试', 'warning')
                            return redirect(url_for('language_tests.test_system'))
                except Exception as e:
                    logger.error(f"游客权限检查失败: {str(e)}")

                return f(*args, **kwargs)
            return decorated_function
        return decorator


def guest_permission_middleware(app):
    """初始化游客权限中间件"""
    logger.info("游客权限中间件已注册")
    return app
