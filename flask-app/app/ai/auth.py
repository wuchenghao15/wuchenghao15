# -*- coding: utf-8 -*-
import time
import hashlib
from app.config import Config
from app.utils.logging import logger
from app.models.user import User
from app.utils.security import security_utils

class AuthAI:
    """用户认证AI，负责处理用户登录、注册和权限管理"""

    def __init__(self):
        self.instance_id = f"auth_ai_{id(self)}"
        self.name = "用户认证AI"
        self.description = "负责处理用户登录、注册和权限管理"
        self.logger = logger
        self.logger.info(f"初始化用户认证AI: {self.instance_id}")

    def authenticate_user(self, username, password):
        """验证用户身份"""
        try:
            self.logger.info(f"{self.instance_id} 正在验证用户: {username}")

            # 检查用户是否存在 - 使用正确的User模型方法
            user = User.get_by_username(username)
            if not user:
                self.logger.warning(f"{self.instance_id} 用户不存在: {username}")
                return {
                    "success": False,
                    "message": "用户名或密码错误",
                    "user": None
                }

            # 验证密码 - 使用security_utils验证
            if not security_utils.verify_password(user.password, password):
                self.logger.warning(f"{self.instance_id} 用户密码错误: {username}")
                    "success": False,
                    "user": None

                "success": True,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at
                }
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 用户认证失败: {str(e)}")
                "success": False,

    def register_user(self, username, password, email, role="user"):
        """注册新用户"""
            self.logger.info(f"{self.instance_id} 正在注册新用户: {username}")
            # 检查用户名是否已存在 - 使用正确的查询方式
            existing_user = User.get_by_username(username)
                self.logger.warning(f"{self.instance_id} 用户名已存在: {username}")
                return {
                    "message": "用户名已存在"
                }

            # 检查邮箱是否已存在 - 使用原生SQL查询
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email=?', (email,))
            existing_email = cursor.fetchone()
            conn.close()

            if existing_email:
                self.logger.warning(f"{self.instance_id} 邮箱已存在: {email}")
                    "message": "邮箱已存在"
                }

            # 创建新用户 - 使用security_utils进行密码哈希
            hashed_password = security_utils.hash_password(password)
            new_user = User(
                username=username,
                password=hashed_password,
                email=email,
                role=role
            )
            new_user.save()

            return {
                "message": "注册成功"
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 用户注册失败: {str(e)}")
            return {
                "message": f"注册过程中发生错误: {str(e)}"
            }

    def verify_permission(self, username, required_permission):
        """验证用户权限"""
            self.logger.info(f"{self.instance_id} 正在验证用户权限: {username} -> {required_permission}")

            user = User.get_by_username(username)
            if not user:
                return False
                self.logger.warning(f"{self.instance_id} 用户已被禁用: {username}")
                return False

            # 检查用户角色权限，完善所有角色定义
            role_permissions = {
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
                    "view_reports", "save_test_progress", "view_test_history", "manage_favorites",
                    "access_language_tests", "take_language_tests", "view_language_test_results"
                ],
                "teacher": [
                    "manage_tests", "view_students", "generate_reports", "grade_tests",
                    "manage_student_groups", "view_class_stats", "create_test_templates",
                    "manage_language_tests", "access_language_tests", "view_language_test_results",
                    "grade_language_tests", "manage_language_test_settings"
                ],
                "guest": [
                    "take_tests", "view_results", "view_test_history",
                    "access_language_tests", "take_language_tests", "view_language_test_results"
                ]
            }

            user_role = user.role
            if user_role not in role_permissions:
                self.logger.warning(f"{self.instance_id} 未知用户角色: {user_role}")

            # 超级管理员和硬件管理员拥有所有权限
                self.logger.info(f"{self.instance_id} 用户权限验证通过: {username} -> {required_permission} (管理员特权)")
                return True

            # 检查用户是否拥有直接权限或继承权限
            if required_permission in role_permissions[user_role]:
                return True

            # 检查权限是否是用户角色权限的子集（例如，admin权限包含所有子权限）
            for permission in role_permissions[user_role]:
                    return True

            self.logger.warning(f"{self.instance_id} 用户权限验证失败: {username} -> {required_permission}")
            return False
        except Exception as e:
            return False

    def manage_session(self, username, session_data):
        """管理用户会话"""
            self.logger.info(f"{self.instance_id} 正在管理用户会话: {username}")

            session_expiry = time.time() + Config.SESSION_TIMEOUT

            session_info = {
                "session_id": session_id,
                "username": username,
                "created_at": time.time(),
                "expires_at": session_expiry,
                "data": session_data
            }

            self.logger.info(f"{self.instance_id} 用户会话管理成功: {username}")
            return {
                "success": True,
                "session_info": session_info
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 会话管理失败: {str(e)}")
            }

        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            Config.PASSWORD_HASH_ITERATIONS
        ).hex()

        """生成随机盐值"""

    def _generate_session_id(self, username):
        """生成会话ID"""
        return hashlib.sha256((username + str(time.time())).encode()).hexdigest()
    def __str__(self):
        return f"AuthAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()
# 创建全局用户认证AI实例
auth_ai = AuthAI()
