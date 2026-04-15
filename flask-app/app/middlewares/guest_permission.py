#!/usr/bin/env python3
"""
游客用户权限中间件
限制游客用户只能访问考试和语言测试相关的功能
"""

from flask import session, redirect, url_for, flash
from functools import wraps
from app.utils.logging import logger

class GuestPermissionMiddleware:
    """游客用户权限中间件"""
    
    @staticmethod
    def require_guest_permission():
        """检查游客用户权限的装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 检查用户是否为游客
                if session.get('is_guest'):
                    # 检查访问的路由是否允许游客访问
                    allowed_routes = [
                        'language_tests.test_system',
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
                    
                    # 获取当前路由
                    from flask import request
                    current_route = request.endpoint
                    
                    if current_route not in allowed_routes:
                        logger.warning(f"游客用户 {session.get('username')} 尝试访问受限路由: {current_route}")
                        flash('游客用户只能参加考试和语言等级测试', 'warning')
                        return redirect(url_for('language_tests.test_system'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# 创建中间件实例
guest_permission_middleware = GuestPermissionMiddleware()
