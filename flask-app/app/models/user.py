#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import contextmanager
from app.utils.logging import logger
from app.services.user_management_client import get_user_management_client


class User:
    """用户数据模型"""

    def __init__(self, user_id=None, username=None, email=None, password=None, role="user", created_at=None, updated_at=None, is_active=1, super_admin_approved=0, hardware_admin_approved=0, avatar=None, reset_token=None, reset_token_expiry=None, password_modified_at=None, password_modified_by=None, phone=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_active = is_active
        self.super_admin_approved = super_admin_approved
        self.hardware_admin_approved = hardware_admin_approved
        self.avatar = avatar
        self.reset_token = reset_token
        self.reset_token_expiry = reset_token_expiry
        self.password_modified_at = password_modified_at
        self.password_modified_by = password_modified_by
        self.phone = phone

    def get_verification_info(self, verification_type=None):
        """获取用户的验证信息"""
        try:
            from app.utils.db import db_manager

            if verification_type:
                verification_data = db_manager.fetch_one(
                    'SELECT verification_value, is_active FROM user_verification WHERE user_id = ? AND verification_type = ?',
                    (self.user_id, verification_type)
                )

                if verification_data:
                    return verification_data
            return {}
        except Exception as e:
            logger.error(f"获取验证信息失败: {str(e)}")
            return {}

    def save_verification_info(self, verification_type, verification_value):
        """保存用户的验证信息"""
        try:
            from app.utils.db import db_manager
            existing = db_manager.fetch_one(
                'SELECT id FROM user_verification WHERE user_id = ? AND verification_type = ?',
                (self.user_id, verification_type)
            )

            if existing:
                db_manager.execute(
                    'UPDATE user_verification SET verification_value = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND verification_type = ?',
                    (verification_value, self.user_id, verification_type)
                )
                logger.info(f"更新用户验证信息: {self.username}, 类型: {verification_type}")
            else:
                db_manager.execute(
                    'INSERT INTO user_verification (user_id, username, verification_type, verification_value) VALUES (?, ?, ?, ?)',
                    (self.user_id, self.username, verification_type, verification_value)
                )
                logger.info(f"保存用户验证信息: {self.username}, 类型: {verification_type}")
            return True
        except Exception as e:
            logger.error(f"保存验证信息失败: {str(e)}")
            return False

    def delete_verification_info(self, verification_type):
        """删除用户的验证信息"""
        try:
            from app.utils.db import db_manager
            db_manager.execute(
                'DELETE FROM user_verification WHERE user_id = ? AND verification_type = ?',
                (self.user_id, verification_type)
            )
            logger.info(f"删除用户验证信息: {self.username}, 类型: {verification_type}")
            return True
        except Exception as e:
            logger.error(f"删除验证信息失败: {str(e)}")
            return False

    @staticmethod
    def create_table():
        """创建用户表 - 调用远程服务"""
        try:
            client = get_user_management_client()
            health_status = client.health_check()
            if health_status.get('success'):
                logger.info("用户管理服务健康状态正常")
            else:
                logger.error("用户管理服务健康检查失败")
        except Exception as e:
            logger.error(f"调用用户管理服务失败: {str(e)}")

    def save(self):
        """保存用户信息 - 使用数据库管理器"""
        try:
            from app.utils.db import db_manager
            if self.user_id:
                data = {
                    'username': self.username,
                    'email': self.email,
                    'password': self.password,
                    'role': self.role,
                    'is_active': self.is_active
                }
                success = db_manager.update('users', data, 'id = ?', [self.user_id])
                if success:
                    return self.user_id
            return None
        except Exception as e:
            logger.error(f"保存用户失败: {str(e)}")
            return None

    @staticmethod
    def get_by_username(username):
        """通过用户名获取用户"""
        try:
            import sqlite3
            import os
            from app.utils.db import db_manager

            user_data = db_manager.fetch_one(
                'SELECT id, username, email, password, role, is_active FROM users WHERE username = ?',
                (username,)
            )

            if user_data:
                user_id = user_data.get('id') if isinstance(user_data, dict) else user_data[0]
                username = user_data.get('username') if isinstance(user_data, dict) else user_data[1]
                email = user_data.get('email') if isinstance(user_data, dict) else user_data[2]
                password = user_data.get('password') if isinstance(user_data, dict) else user_data[3]
                role = user_data.get('role') if isinstance(user_data, dict) else user_data[4]
                is_active = user_data.get('is_active') if isinstance(user_data, dict) else user_data[5]
                logger.info(f"数据库获取用户成功: {username}")
                return User(user_id=user_id, username=username, email=email, password=password, role=role, is_active=is_active)
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    @staticmethod
    def get_by_id(user_id):
        """通过用户ID获取用户 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.get_user(user_id)
            if result.get('success'):
                user_data = result.get('user')
                if user_data:
                    return User(
                        user_id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        role=user_data.get('role'),
                        is_active=user_data.get('is_active')
                    )
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    @staticmethod
    def verify_credentials(username, password):
        """验证用户凭据"""
        try:
            import sqlite3
            import os
            from app.utils.security import security_utils
            from app.utils.db import db_manager

            user_data = db_manager.fetch_one(
                'SELECT id, username, email, password, role, is_active FROM users WHERE username = ?',
                (username,)
            )

            if user_data:
                user_id = user_data.get('id') if isinstance(user_data, dict) else user_data[0]
                username = user_data.get('username') if isinstance(user_data, dict) else user_data[1]
                email = user_data.get('email') if isinstance(user_data, dict) else user_data[2]
                stored_password = user_data.get('password') if isinstance(user_data, dict) else user_data[3]
                role = user_data.get('role') if isinstance(user_data, dict) else user_data[4]
                is_active = user_data.get('is_active') if isinstance(user_data, dict) else user_data[5]

                if len(stored_password) < 80:
                    hashed_password = security_utils.hash_password(password)
                    db_manager.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))

                return User(user_id=user_id, username=username, email=email, password=stored_password, role=role, is_active=is_active)
            return None
        except Exception as e:
            logger.error(f"验证凭据失败: {str(e)}")
            return None

    def update_password(self, new_password):
        """更新用户密码 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.update_password(self.user_id, new_password)
            if result.get('success'):
                logger.info(f"更新用户密码: {self.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新密码失败: {str(e)}")
            return False

    @staticmethod
    def get_all_users():
        """获取所有用户 - 调用远程服务"""
        try:
            client = get_user_management_client()
            result = client.get_all_users()
            users = []
            if result.get('success'):
                for user_data in result.get('users', []):
                    users.append(User(
                        user_id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        role=user_data.get('role'),
                        is_active=user_data.get('is_active'),
                        super_admin_approved=0,
                        hardware_admin_approved=0,
                        avatar=user_data.get('avatar')
                    ))
            return users
        except Exception as e:
            logger.error(f"获取所有用户失败: {str(e)}")
            return []

    @staticmethod
    def get_by_email(email):
        """通过邮箱获取用户"""
        try:
            from app.utils.db import db_manager
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active FROM users WHERE email = ?', (email,))
            if user_data:
                user_id = user_data.get('id') if isinstance(user_data, dict) else user_data[0]
                username = user_data.get('username') if isinstance(user_data, dict) else user_data[1]
                email = user_data.get('email') if isinstance(user_data, dict) else user_data[2]
                hashed_password = user_data.get('password') if isinstance(user_data, dict) else user_data[3]
                role = user_data.get('role') if isinstance(user_data, dict) else user_data[4]
                is_active = user_data.get('is_active') if isinstance(user_data, dict) else user_data[5]
                logger.info(f"通过邮箱获取用户成功: {email}")
                return User(user_id=user_id, username=username, email=email, password=hashed_password, role=role, is_active=is_active)
            return None
        except Exception as e:
            logger.error(f"通过邮箱获取用户失败: {str(e)}")
            return None

    @staticmethod
    def get_by_phone(phone):
        """通过手机号获取用户"""
        try:
            from app.utils.db import db_manager
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active FROM users WHERE phone = ?', (phone,))
            if user_data:
                user_id = user_data.get('id') if isinstance(user_data, dict) else user_data[0]
                username = user_data.get('username') if isinstance(user_data, dict) else user_data[1]
                email = user_data.get('email') if isinstance(user_data, dict) else user_data[2]
                password = user_data.get('password') if isinstance(user_data, dict) else user_data[3]
                role = user_data.get('role') if isinstance(user_data, dict) else user_data[4]
                is_active = user_data.get('is_active') if isinstance(user_data, dict) else user_data[5]
                return User(user_id=user_id, username=username, email=email, password=password, role=role, is_active=is_active)
            return None
        except Exception as e:
            logger.error(f"通过手机号获取用户失败: {str(e)}")
            return None

    @staticmethod
    def get_by_reset_token(token):
        """通过重置令牌获取用户"""
        try:
            from app.utils.db import db_manager
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active FROM users WHERE reset_token = ?', (token,))
            if user_data:
                user_id = user_data.get('id') if isinstance(user_data, dict) else user_data[0]
                username = user_data.get('username') if isinstance(user_data, dict) else user_data[1]
                email = user_data.get('email') if isinstance(user_data, dict) else user_data[2]
                password = user_data.get('password') if isinstance(user_data, dict) else user_data[3]
                role = user_data.get('role') if isinstance(user_data, dict) else user_data[4]
                is_active = user_data.get('is_active') if isinstance(user_data, dict) else user_data[5]
                logger.info(f"通过重置令牌获取用户成功: {username}")
                return User(user_id=user_id, username=username, email=email, password=password, role=role, is_active=is_active)
            return None
        except Exception as e:
            logger.error(f"通过重置令牌获取用户失败: {str(e)}")
            return None

    def add_password_history(self, password_hash):
        """添加密码历史记录"""
        try:
            from app.utils.db import db_manager
            db_manager.execute(
                'INSERT INTO password_history (user_id, password_hash) VALUES (?, ?)',
                (self.user_id, password_hash)
            )
            logger.info(f"添加密码历史记录: {self.username}")
            return True
        except Exception as e:
            logger.error(f"添加密码历史记录失败: {str(e)}")
            return False

    def get_password_history(self, limit=10):
        """获取密码历史记录"""
        try:
            from app.utils.db import db_manager
            history = db_manager.fetch_all(
                'SELECT id, password_hash, created_at FROM password_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                (self.user_id, limit)
            )
            return history
        except Exception as e:
            logger.error(f"获取密码历史记录失败: {str(e)}")
            return []

    def is_password_used_before(self, password_hash):
        """检查密码是否之前使用过"""
        try:
            from app.utils.db import db_manager
            result = db_manager.fetch_one(
                'SELECT id FROM password_history WHERE user_id = ? AND password_hash = ?',
                (self.user_id, password_hash)
            )
            return result is not None
        except Exception as e:
            logger.error(f"检查密码历史失败: {str(e)}")
            return False

    @staticmethod
    def is_common_password(password):
        """检查是否为常用密码"""
        common_passwords = [
            'Password123', 'Qwerty123', '12345678', 'Admin123',
            'Letmein123', 'Welcome123', 'Monkey123', 'Dragon123',
            'Password1!', 'Qwerty1!', '123456789', '12345678a',
            'Password2024', 'Password2025', 'Password2026'
        ]
        return password in common_passwords
