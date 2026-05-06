# -*- coding: utf-8 -*-
import os
import hashlib
import base64
from functools import wraps
from flask import session, redirect, url_for, flash
from app.config import Config
from app.utils.logging import logger

class SecurityUtils:
    """安全工具类，用于处理密码哈希、权限检查等安全相关功能"""

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
            # 将盐和哈希值连接起来，然后进行base64编码
            return base64.b64encode(salt + hashed).decode('utf-8')
        except Exception as e:
            logger.error(f"密码哈希失败: {str(e)}")
            raise

    def verify_password(stored_password, provided_password):
        """验证密码，支持多种哈希格式"""
        try:
            # 支持约88字符长度的base64编码格式
            # 这种格式是: base64(salt + hash)，其中salt是32字节，hash是32字节
            decoded = base64.b64decode(stored_password)
            if len(decoded) == 64:  # 32字节salt + 32字节hash
                salt = decoded[:32]
                stored_hash = decoded[32:]

                # 计算提供密码的哈希值
                hashed = hashlib.pbkdf2_hmac(
                    Config.HASH_ALGORITHM,
                    salt,
                )

                    return True
            logger.error(f"base64格式密码验证失败: {str(e)}")
        # 2. 尝试使用hex格式验证（update_users.py使用的格式）
        # 支持64字符和96字符格式
        if len(stored_password) in [64, 96]:
            try:
                salt_hex = stored_password[:32]  # 前32个字符是salt的十六进制表示（16字节）
                hash_hex = stored_password[32:96]  # 后面是hash的十六进制表示（32字节）

                # 转换为bytes
                salt = bytes.fromhex(salt_hex)
                stored_hash = bytes.fromhex(hash_hex)

                # 计算提供密码的哈希值
                hashed = hashlib.pbkdf2_hmac(
                    'sha256',
                    provided_password.encode('utf-8'),
                    100000
                )

                return hashed == stored_hash

        # 3. 尝试使用werkzeug.security.check_password_hash（支持scrypt哈希）
        try:
            logger.error(f"werkzeug格式密码验证失败: {str(e)}")

        return False

    def check_permission(required_permission):
        """权限检查装饰器，基于细粒度权限控制"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_level' not in session:
                    flash('请先登录', 'danger')
                    return redirect(url_for('main.index'))

                username = session.get('username')
                user_level = session['user_level']

                # 细粒度权限定义，与auth_ai保持一致
                role_permissions = {
                    "hardware_vikey_admin": [
                        "admin", "manage_users", "manage_system", "view_reports", "manage_hardware",
                        "manage_ai_rules", "manage_approvals", "view_logs", "system_cleanup", "system_config",
                        "manage_roles", "manage_permissions", "access_all_data", "manage_api_keys",
                        "manage_backups", "manage_security_settings", "manage_logs", "view_audit_logs",
                        "manage_sandboxes", "manage_ai_models", "manage_question_banks", "manage_tests",
                        "manage_language_tests", "access_language_tests", "manage_admin_approval",
                        "manage_sensitive_data", "manage_underlying_settings", "auto_expand_features"
                    ],
                    "super_admin": [
                        "admin", "manage_users", "manage_system", "view_reports", "manage_ai_rules",
                        "manage_approvals", "view_logs", "system_config", "manage_roles", "manage_permissions",
                        "access_all_data", "manage_api_keys", "manage_backups", "manage_security_settings",
                        "manage_logs", "view_audit_logs", "manage_ai_models", "manage_question_banks", "manage_tests",
                        "manage_language_tests", "access_language_tests", "manage_admin_approval",
                        "manage_admin_users", "update_rules", "manage_ai_employees"
                    ],
                    "admin": [
                        "manage_ai_rules", "manage_approvals", "view_logs", "system_cleanup", "view_reports",
                        "manage_question_banks", "manage_tests", "manage_ai_models", "manage_sandboxes",
                        "access_language_tests", "manage_non_sensitive_data", "admin_approval",
                        "view_language_test_results", "manage_language_test_settings"
                    ],
                    "user": [
                        "take_tests", "view_results", "update_profile", "manage_projects", "manage_tasks",
                        "view_reports", "save_test_progress", "view_test_history", "manage_favorites",
                        "access_language_tests", "take_language_tests", "view_language_test_results"
                    ],
                    "teacher": [
                        "manage_student_groups", "view_class_stats", "create_test_templates",
                        "manage_language_tests", "access_language_tests", "view_language_test_results",
                    ],
                    "guest": [
                        "take_tests", "view_results", "view_test_history",
                        "access_language_tests", "take_language_tests", "view_language_test_results"
                    ]

                # 超级管理员和硬件管理员拥有所有权限
                if user_level in ["super_admin", "hardware_vikey_admin"]:
                    return f(*args, **kwargs)
                # 检查用户角色是否有效
                if user_level not in role_permissions:
                    flash('您的角色无效', 'danger')
                    logger.warning(f"无效角色: 用户 {username} 拥有角色 {user_level}")
                    return redirect(url_for('main.index'))
                # 检查用户是否拥有直接权限或继承权限
                if required_permission in role_permissions[user_level]:
                    return f(*args, **kwargs)

                # 检查权限是否是用户角色权限的子集（例如，admin权限包含所有子权限）
                for permission in role_permissions[user_level]:
                        return f(*args, **kwargs)

                flash('您没有权限访问此页面', 'danger')
                logger.warning(f"权限不足: 用户 {username} 尝试访问需要 {required_permission} 权限的资源")
                return redirect(url_for('main.index'))
            return decorated_function
        return decorator

    def generate_csrf_token():
        """生成CSRF令牌"""
        if '_csrf_token' not in session:
            session['_csrf_token'] = base64.b64encode(os.urandom(32)).decode('utf-8')
        return session['_csrf_token']

    def verify_csrf_token(token):
        """验证CSRF令牌"""
        return token == session.get('_csrf_token')

    def login_required(f):
        """登录验证装饰器，支持会话管理"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否已登录
            if 'logged_in' not in session or not session['logged_in']:
                flash('请先登录', 'danger')
                return redirect(url_for('main.index'))

            # 检查会话ID是否存在
            session_id = session.get('session_id')
            user_id = session.get('user_id')
            username = session.get('username')

            # 如果是游客会话，跳过数据库会话验证
            if session.get('is_guest', False):
                return f(*args, **kwargs)

            # 如果是临时会话（没有用户ID），跳过数据库会话验证
            if not user_id:

                # 验证会话有效性
                from app.utils.session_manager import session_manager
                is_valid, message = session_manager.validate_session(session_id)
                    # 会话无效，清除会话
                    session.clear()
                    flash(f'会话无效: {message}', 'danger')
                    logger.warning(f"会话验证失败: 用户 {username}, 会话ID {session_id[:10]}...: {message}")
                    return redirect(url_for('main.index'))
            except Exception as e:
                # 发生错误时，允许用户继续访问，但记录日志

            return f(*args, **kwargs)
        return decorated_function

# 初始化安全工具
security_utils = SecurityUtils()
