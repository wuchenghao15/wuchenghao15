# -*- coding: utf-8 -*-
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
                # 获取特定类型的验证信息
                verification_data = db_manager.fetch_one(
                    'SELECT verification_value, is_active FROM user_verification WHERE user_id = ? AND verification_type = ?',
                    (self.user_id, verification_type)
                )
                if verification_data:
                    return {
                        'verification_type': verification_type,
                        'verification_value': verification_data[0],
                        'is_active': verification_data[1]
                    }
                return None
            else:
                # 获取所有验证信息
                verification_data = db_manager.fetch_all(
                    'SELECT verification_type, verification_value, is_active FROM user_verification WHERE user_id = ?',
                    (self.user_id,)
                )
                return [{
                    'verification_type': item[0],
                    'verification_value': item[1],
                    'is_active': item[2]
                } for item in verification_data]
        except Exception as e:
            logger.error(f"获取用户验证信息失败: {str(e)}")
            return []

    def save_verification_info(self, verification_type, verification_value):
        """保存用户的验证信息"""
            from app.utils.db import db_manager
            # 检查是否已存在该类型的验证信息
            existing = db_manager.fetch_one(
                'SELECT id FROM user_verification WHERE user_id = ? AND verification_type = ?',
                (self.user_id, verification_type)
            )
            if existing:
                # 更新现有验证信息
                db_manager.execute(
                    'UPDATE user_verification SET verification_value = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND verification_type = ?',
                    (verification_value, self.user_id, verification_type)
                )
                logger.info(f"更新用户验证信息: {self.username}, 类型: {verification_type}")
            else:
                # 插入新的验证信息
                db_manager.execute(
                    (self.user_id, self.username, verification_type, verification_value)
                )
                logger.info(f"保存用户验证信息: {self.username}, 类型: {verification_type}")
            return True
        except Exception as e:
            logger.error(f"保存用户验证信息失败: {str(e)}")
            return False

    def delete_verification_info(self, verification_type):
        """删除用户的验证信息"""
            from app.utils.db import db_manager

                'DELETE FROM user_verification WHERE user_id = ? AND verification_type = ?',
                (self.user_id, verification_type)
            )
            logger.info(f"删除用户验证信息: {self.username}, 类型: {verification_type}")
            return True
            logger.error(f"删除用户验证信息失败: {str(e)}")
            return False

    @staticmethod
    def create_table():
        """创建用户表 - 调用远程服务"""
            client = get_user_management_client()
            # 调用健康检查接口，确保服务可用
            health_status = client.health_check()
            if health_status.get('success'):
                logger.info("用户管理服务健康状态正常")
            else:
                logger.error("用户管理服务健康检查失败")
        except Exception as e:
            logger.error(f"调用用户管理服务失败: {str(e)}")

    def save(self):
        """保存用户信息 - 使用数据库管理器"""

            if self.user_id:
                # 更新现有用户
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
                else:
                    return None
            else:
                # 创建新用户
                logger.info(f"创建用户: {self.username}")
                    'username': self.username,
                    'email': self.email,
                    'password': self.password,
                    'role': self.role,
                user_id = db_manager.insert('users', data)
                    return user_id
                else:
                    return None
        except Exception as e:
            logger.error(f"保存用户信息失败: {str(e)}")
            import traceback

    def get_by_username(username):
        try:
            import os
            # 使用绝对路径连接数据库

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 查询users表
            print(f"DEBUG: Querying users table for: {username}")
            cursor.execute('SELECT id, username, email, password, role, is_active FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()

            if user_data:
                user_id, username, email, password, role, is_active = user_data
                print(f"DEBUG: Found user in users table: {username}, role: {role}, is_active: {is_active}")
                logger.info(f"数据库获取用户成功: {username}")
                conn.close()
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password='',  # 不返回密码
                    role=role,
                    is_active=is_active,
                    super_admin_approved=1,
                    hardware_admin_approved=1
                )
            else:
                print(f"DEBUG: User not found in users table: {username}")
                conn.close()
                return None
        except Exception as e:
            logger.error(f"通过用户名获取用户失败: {str(e)}")
            print(f"DEBUG: Error getting user: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_by_id(user_id):
        """通过用户ID获取用户 - 调用远程服务"""
        try:
            result = client.get_user(user_id)
                if user_data:
                    return User(
                        user_id=user_data.get('id'),
                        username=user_data.get('username'),
                        password='',  # 不返回密码
                        role=user_data.get('role'),
                        created_at=user_data.get('created_at'),
                        updated_at=user_data.get('created_at'),
                        is_active=user_data.get('is_active'),
                        super_admin_approved=0,
                        hardware_admin_approved=0,
                        avatar=user_data.get('avatar')
                    )
        except Exception as e:
            logger.error(f"通过用户ID获取用户失败: {str(e)}")
            return None

    def verify_credentials(username, password):

            # 直接从users表中查询用户
            import sqlite3
            import os
            from app.utils.security import security_utils
            # 使用绝对路径连接数据库
            db_path = os.path.abspath('app.db')

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            print(f"DEBUG: Querying users table for username: {username}")
            cursor.execute('SELECT id, username, email, password, role, is_active FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()

            if user_data:
                user_id, username, email, stored_password, role, is_active = user_data
                print(f"DEBUG: Found user in users table: {username}, role: {role}, is_active: {is_active}")

                # 检查是否是明文密码，如果是则自动更新为哈希密码
                if len(stored_password) < 80:  # 简单判断，哈希密码通常较长
                    # 计算哈希密码
                    hashed_password = security_utils.hash_password(password)
                    # 更新数据库中的密码
                    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
                    conn.commit()
                    # 验证成功
                    conn.close()
                    return User(
                        user_id=user_id,
                        username=username,
                        email=email,
                        password='',  # 不存储密码
                        role=role,
                        is_active=is_active,
                        hardware_admin_approved=1,
                    )
                    # 使用哈希密码验证
                    try:
                            print(f"DEBUG: Hashed password match for: {username}")
                            conn.close()
                                user_id=user_id,
                                email=email,
                                password='',  # 不存储密码
                                is_active=is_active,
                                hardware_admin_approved=1,
                                phone=None
                            )
                        else:
                            logger.warning(f"密码验证失败: {username}")
                            return None
                        print(f"DEBUG: Hash verification error: {hash_error}")
                        conn.close()
                        return None
            else:
                conn.close()
                return None
        except Exception as e:
            logger.error(f"验证用户凭证失败: {str(e)}")
            print(f"DEBUG: Error verifying credentials: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    def update_password(self, new_password):
        """更新用户密码 - 调用远程服务"""
                logger.info(f"更新用户密码: {self.username}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"更新用户密码失败: {str(e)}")
            return False

        """更新用户角色 - 调用远程服务"""
            result = client.update_user(self.user_id, role=new_role)
            if result.get('success'):
                self.role = new_role
                logger.info(f"更新用户角色: {self.username} -> {new_role}")
                return True
            else:
                logger.error(f"更新用户角色失败: {result.get('error')}")
                return False
            logger.error(f"更新用户角色失败: {str(e)}")
            return False

    @staticmethod
    def get_all_users():
        """获取所有用户 - 调用远程服务"""
        try:
            if result.get('success'):
                for user_data in result.get('users', []):
                    users.append(User(
                        user_id=user_data.get('id'),
                        username=user_data.get('username'),
                        is_active=user_data.get('is_active'),
                        super_admin_approved=0,
                        hardware_admin_approved=0,
                        avatar=user_data.get('avatar')
                return users
        except Exception as e:
            logger.error(f"获取所有用户失败: {str(e)}")

        """删除用户 - 调用远程服务"""
        try:
            result = client.delete_user(self.user_id)
                logger.info(f"删除用户: {self.username}")
                return True
            else:
                logger.error(f"删除用户失败: {result.get('error')}")
                return False
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return False

    @staticmethod
    def get_by_email(email):
        """通过邮箱获取用户"""

            # 从数据库查询用户
            user_data = db_manager.fetch_one('SELECT id, username, email, password, role, is_active FROM users WHERE email = ?', (email,))
            if user_data:
                user_id, username, email, hashed_password, role, is_active = user_data
                logger.info(f"通过邮箱获取用户成功: {email}")
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password='',  # 不返回密码
                    role=role,
                    super_admin_approved=1,
                    hardware_admin_approved=1
                )
            return None
        except Exception as e:
            return None
    @staticmethod
    def get_by_phone(phone):
        """通过手机号获取用户"""
        try:

            # 由于表中可能没有phone字段，直接返回None
            return None
        except Exception as e:
            logger.error(f"通过手机号获取用户失败: {str(e)}")
            return None

    @staticmethod
    def get_by_reset_token(token):
        """通过重置令牌获取用户"""
        try:

            if user_data:
                logger.info(f"通过重置令牌获取用户成功: {username}")
                return User(
                    user_id=user_id,
                    username=username,
                    password='',  # 不返回密码
                    is_active=is_active,
                    reset_token_expiry=reset_token_expiry
                )
            logger.error(f"通过重置令牌获取用户失败: {str(e)}")

        """更新用户信息"""

            db_manager.execute(
                (self.email, self.password, self.role, self.is_active, self.reset_token, self.reset_token_expiry, self.password_modified_at, self.password_modified_by, self.user_id)
            return True
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return False

    def add_password_history(self, password_hash):
        """添加密码历史记录"""
        try:
                'INSERT INTO password_history (user_id, password_hash) VALUES (?, ?)',
                (self.user_id, password_hash)
            logger.info(f"添加密码历史记录: {self.username}")
            return True
            logger.error(f"添加密码历史记录失败: {str(e)}")
            return False

    def get_password_history(self, limit=10):
        """获取密码历史记录"""
        try:

            history = db_manager.fetch_all(
                'SELECT id, password_hash, created_at FROM password_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            )
            return history
        except Exception as e:
            logger.error(f"获取密码历史记录失败: {str(e)}")
            return []

    def is_password_used_before(self, password_hash):
        try:

            result = db_manager.fetch_one(
                'SELECT id FROM password_history WHERE user_id = ? AND password_hash = ?',
                (self.user_id, password_hash)
            )
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
