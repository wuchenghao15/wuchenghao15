#!/usr/bin/env python3
"""
用户容器标签检查中间件
"""

from flask import Flask, request, redirect, url_for, render_template, jsonify
from app.utils.logging import logger
from app.models.user import User

# 中间件优先级
user_container_middleware_priority = 25

def user_container_middleware(app: Flask):
    """
    用户容器标签检查中间件
    
    检查每个请求是否包含用户容器标签，如果没有则返回504错误
    """
    @app.before_request
    def check_user_container():
        # 排除静态文件和登录页面
        if request.path.startswith('/static/') or request.path == '/auth/login' or request.path == '/':
            return None
        
        # 检查会话中是否有用户容器标签
        user_container = request.cookies.get('user_container') or request.headers.get('X-User-Container')
        
        # 检查用户会话
        from flask import session
        user_id = session.get('user_id')
        
        # 如果没有用户容器标签且用户已登录，返回504错误
        if user_id and not user_container:
            logger.warning(f"用户 {user_id} 缺少容器标签")
            # 返回504错误页面
            return render_template('errors/504.html'), 504
        
        return None
    
    @app.errorhandler(504)
    def handle_504_error(error):
        """
        处理504错误
        """
        return render_template('errors/504.html'), 504
