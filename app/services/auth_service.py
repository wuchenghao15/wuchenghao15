#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务 - 密码验证、用户查询等功能
"""

import hashlib
import base64
import sqlite3
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = None


def set_database_path(path):
    """设置数据库路径"""
    global DATABASE_PATH
    DATABASE_PATH = path


def verify_password(stored_password, provided_password):
    """验证密码 - 支持多种哈希方式"""
    try:
        if stored_password.startswith('gAAAAA'):
            try:
                from cryptography.fernet import Fernet
                possible_keys = [
                    b'MTSCOS_SECRET_KEY_2026',
                    b'mtscos_ai_secret_key_2026',
                    b'MTSCOS_AI_SYSTEM_KEY_2026'
                ]
                for key_source in possible_keys:
                    try:
                        key = base64.urlsafe_b64encode(hashlib.sha256(key_source).digest()[:32])
                        fernet = Fernet(key)
                        decrypted = fernet.decrypt(stored_password.encode()).decode()
                        if decrypted == provided_password:
                            return True
                    except Exception:
                        continue
                logger.error("Fernet解密失败: 尝试了所有可能的密钥")
            except Exception as e:
                logger.error(f"Fernet解密异常: {e}")

        if stored_password.startswith('pbkdf2:'):
            try:
                from werkzeug.security import check_password_hash
                return check_password_hash(stored_password, provided_password)
            except ImportError:
                parts = stored_password.split('$')
                if len(parts) == 3:
                    algorithm_info = parts[0]
                    salt = parts[1].encode()
                    stored_hash = parts[2].encode()
                    algo_parts = algorithm_info.split(':')
                    if len(algo_parts) >= 3:
                        algo = algo_parts[1]
                        iterations = int(algo_parts[2])
                        provided_hash = hashlib.pbkdf2_hmac(algo, provided_password.encode(), salt, iterations)
                        return stored_hash == provided_hash.hex().encode()
                return False

        if stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith(
        '$2y$'):
            try:
                import bcrypt
                return bcrypt.checkpw(provided_password.encode(), stored_password.encode())
            except ImportError:
                logger.error("bcrypt模块未安装")
                return False

        if len(stored_password) == 64 and all(c in '0123456789abcdef' for c in stored_password.lower()):
            provided_hex = hashlib.sha256(provided_password.encode()).hexdigest()
            return stored_password == provided_hex

        try:
            stored_bytes = base64.b64decode(stored_password)
            if len(stored_bytes) == 32:
                provided_hash = hashlib.sha256(provided_password.encode()).digest()
                return stored_bytes == provided_hash
            if len(stored_bytes) > 32:
                salt = stored_bytes[:16]
                stored_hash = stored_bytes[16:]
                provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
                return stored_hash == provided_hash
        except Exception:
            pass

        if stored_password == provided_password:
            return True

        if len(stored_password) == 64:
            try:
                int(stored_password, 16)
                provided_hash = hashlib.sha256(provided_password.encode()).hexdigest()
                return stored_password == provided_hash
            except ValueError:
                pass

    except Exception as e:
        logger.error(f"密码验证错误: {e}")

    return stored_password == provided_password


def hash_password(password):
    """使用bcrypt哈希密码"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        logger.warning("bcrypt未安装，回退到SHA-256哈希")
        return base64.b64encode(hashlib.sha256(password.encode()).digest()).decode()


def get_user_by_username(username):
    """从数据库获取用户信息"""
    try:
        db_path = DATABASE_PATH or 'app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

        if user:
            columns = ['id', 'user_id', 'username', 'email', 'password', 'password_hash', 'role', 'is_active',
            'enabled', 'super_admin_approved', 'hardware_admin_approved', 'avatar', 'failed_login_attempts',
            'last_login_attempt', 'locked_until', 'status', 'created_at', 'updated_at']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        logger.error(f"查询用户失败: {e}")
        return None


def get_user_by_id(user_id):
    """从数据库根据ID获取用户信息"""
    try:
        db_path = DATABASE_PATH or 'app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()

        if user:
            columns = ['id', 'user_id', 'username', 'email', 'password', 'password_hash', 'role', 'is_active',
            'enabled', 'super_admin_approved', 'hardware_admin_approved', 'avatar', 'failed_login_attempts',
            'last_login_attempt', 'locked_until', 'status', 'created_at', 'updated_at']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        logger.error(f"根据ID查询用户失败: {e}")
        return None