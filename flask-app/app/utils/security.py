# -*- coding: utf-8 -*-
import os
import hashlib
import base64
from functools import wraps
from flask import session, redirect, url_for, flash
from app.config import Config
from app.utils.logging import logger
import logging

class SecurityUtils:
    """安全工具类: 用于处理密码哈希,权限检查等安全相关功能"""

    @staticmethod
    def hash_password(password):
        """密码哈希处理"""
        try:
            # 使用PBKDF2算法进行密码哈希
            # 生成32字节的随机盐
            salt = os.urandom(32)
            hashed = hashlib.pbkdf2_hmac(
                Config.HASH_ALGORITHM,
                password.encode('utf-8'),
                salt,
                Config.HASH_ITERATIONS
            )
            # 将盐和哈希值连接起来,然后进行base64编码
            return base64.b64encode(salt + hashed).decode('utf-8')
        except Exception as e:
            logger.error(f"密码哈希失败: {str(e)}")
            raise

    @staticmethod
    def verify_password(stored_password, provided_password):
        """验证密码: 支持多种哈希格式"""
        try:
            # 支持约88字符长度的base64编码格式
            # 这种格式是: base64(salt + hash),其中salt是32字节,hash是32字节
            decoded = base64.b64decode(stored_password)
            if len(decoded) == 64:  # 32字节salt + 32字节hash
                salt = decoded[:32]
                stored_hash = decoded[32:]

                # 计算提供密码的哈希值
                hashed = hashlib.pbkdf2_hmac(
                    Config.HASH_ALGORITHM,
                    provided_password.encode('utf-8'),
                    salt,
                    Config.HASH_ITERATIONS
                )
                return hashed == stored_hash
            return False
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    @staticmethod
    def check_permission(required_permission):
        """权限检查装饰器: 基于细粒度权限控制"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_level' not in session:
                    flash('请先登录', 'danger')
                    return redirect(url_for('main.index'))
                
                user_level = session.get('user_level', 'user')
                if user_level == 'admin':
                    return f(*args, **kwargs)
                
                # 检查具体权限
                user_permissions = session.get('permissions', [])
                if required_permission not in user_permissions:
                    flash('权限不足', 'danger')
                    return redirect(url_for('main.index'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def generate_csrf_token():
        """生成CSRF令牌"""
        if '_csrf_token' not in session:
            session['_csrf_token'] = base64.b64encode(os.urandom(32)).decode('utf-8')
        return session['_csrf_token']

    @staticmethod
    def verify_csrf_token(token):
        """验证CSRF令牌"""
        return token == session.get('_csrf_token')

    @staticmethod
    def login_required(f):
        """登录验证装饰器: 支持会话管理"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session or not session['logged_in']:
                flash('请先登录', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def admin_required(f):
        """管理员权限装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_level' not in session or session['user_level'] != 'admin':
                flash('需要管理员权限', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function

security_utils = SecurityUtils()
