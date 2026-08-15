# -*- coding: utf-8 -*-
import time
import hashlib
from app.config import Config
from app.utils.logging import logger
from app.models.user import User
from app.utils.security import security_utils
import logging

logger = logging.getLogger(__name__)

class AuthAI:
    r"""用户认证AI: 负责处理用户登录, 注册和权限管理r"""

    def __init__(self):
        self.instance_id = fr"auth_ai_{id(self)}"
        self.name = r"用户认证AI"
        self.description = r"负责处理用户登录, 注册和权限管理"
        self.logger = logger
        self.logger.info(fr"初始化用户认证AI: {self.instance_id}")

    def authenticate_user(self, username, password):
        r"""验证用户身份r"""
        try:
            self.logger.info(fr"{self.instance_id} 正在验证用户: {username}")

            user = User.get_by_username(username)
            if not user:
                self.logger.warning(fr"{self.instance_id} 用户不存在: {username}")
                return {r"success": False, r"message": r"用户不存在"}

            if security_utils.verify_password(password, user.password_hash):
                self.logger.info(fr"{self.instance_id} 用户验证成功: {username}")
                return {r"success": True, r"user": user.to_dict()}

            self.logger.warning(fr"{self.instance_id} 密码错误: {username}")
            return {r"success": False, r"message": r"密码错误"}
        except Exception as e:
            self.logger.error(fr"{self.instance_id} 用户验证失败: {str(e)}")
            return {r"success": False, r"message": str(e)}

    def register_user(self, username, password, email, role=r"user"):
        r"""注册新用户r"""
        try:
            self.logger.info(fr"{self.instance_id} 正在注册新用户: {username}")

            existing_user = User.get_by_username(username)
            if existing_user:
                self.logger.warning(fr"{self.instance_id} 用户名已存在: {username}")
                return {r"success": False, r"message": r"用户名已存在"}

            existing_email = User.get_by_email(email)
            if existing_email:
                self.logger.warning(fr"{self.instance_id} 邮箱已存在: {email}")
                return {r"success": False, r"message": r"邮箱已存在"}

            password_hash = security_utils.hash_password(password)

            user = User.create(
                username=username,
                password_hash=password_hash,
                email=email,
                role=role
            )

            self.logger.info(fr"{self.instance_id} 用户注册成功: {username}")
            return {r"success": True, r"user": user.to_dict()}
        except Exception as e:
            self.logger.error(fr"{self.instance_id} 用户注册失败: {str(e)}")
            return {r"success": False, r"message": str(e)}

    def verify_permission(self, username, required_permission):
        r"""验证用户权限r"""
        try:
            self.logger.info(fr"{self.instance_id} 正在验证用户权限: {username} -> {required_permission}")

            user = User.get_by_username(username)
            if not user:
                self.logger.warning(fr"{self.instance_id} 用户不存在: {username}")
                return False

            if user.role == r"admin":
                return True

            user_permissions = user.get_permissions()
            if required_permission in user_permissions:
                return True

            self.logger.warning(fr"{self.instance_id} 用户 {username} 没有权限: {required_permission}")
            return False
        except Exception as e:
            self.logger.error(fr"{self.instance_id} 权限验证失败: {str(e)}")
            return False

    def manage_session(self, username, session_data):
        r"""管理用户会话r"""
        try:
            self.logger.info(fr"{self.instance_id} 正在管理用户会话: {username}")

            session_id = self._generate_session_id(username)
            session_expiry = time.time() + Config.SESSION_TIMEOUT

            session_info = {
                r"session_id": session_id,
                r"username": username,
                r"created_at": time.time(),
                r"expires_at": session_expiry,
                r"data": session_data
            }

            self.logger.info(fr"{self.instance_id} 用户会话管理成功: {username}")
            return {r"success": True, r"session": session_info}
        except Exception as e:
            self.logger.error(fr"{self.instance_id} 会话管理失败: {str(e)}")
            return {r"success": False, r"message": str(e)}

    def _generate_session_id(self, username):
        r"""生成会话IDr"""
        return hashlib.sha256((username + str(time.time())).encode()).hexdigest()

    def __str__(self):
        return fr"AuthAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()
