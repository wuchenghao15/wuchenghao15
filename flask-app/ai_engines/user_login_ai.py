# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户登录AI模块,用于处理用户登录请求,智能归档和安全检查

from app.ai.instances import ai_instance_manager
from app.utils.logging import logger
from app.models.user import User
from app.services.user_manager_service import get_user_manager_service
from app.utils.db import db_manager
from datetime import datetime

class UserLoginAI:
    用户登录AI,负责处理用户登录请求,智能归档和安全检查

    def __init__(self):
        self.instance_id = "user_login_ai"
        self.collection_id = "user_dedicated_ai_collection"
        self._initialize()
        self.user_manager = get_user_manager_service()

    def _initialize(self):
        初始化登录AI实例
        # 检查登录AI实例是否已存在
        login_ai = ai_instance_manager.get_ai_instance(self.instance_id)
        if not login_ai:
            logger.info(f"创建用户登录AI实例: {self.instance_id}")
            ai_instance_manager.create_ai_instance(
                instance_id=self.instance_id,
                ai_type="login_ai",
                name="用户登录AI",
                description="专门处理用户登录请求,智能归档和安全检查的AI实例",
                functions=["login_verification", "ip_analysis", "blacklist_check", "whitelist_check", "user_group_analysis"],
                responsibilities=["处理用户登录请求", "分析登录IP", "检查黑名单", "检查白名单", "分析用户组别"],
                config={"login_rate_limit": 5, "session_timeout": 1800, "ip_analysis_enabled": True},
                collection_id=self.collection_id
            )

    def process_login(self, username, password, ip_address, user_agent):
        处理用户登录请求,包括智能归档和安全检查

        Args:
            username: 用户名
            password: 密码
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            dict: 登录结果
        logger.info(f"用户登录AI处理登录请求: {username}, IP: {ip_address}")

        # 1. 检查用户是否存在
        user_exists = self.check_user_exists(username)
        if not user_exists:
            logger.warning(f"用户不存在: {username}")
            return {
                "success": False,
                "message": "用户名或密码错误",
                reason = "user_not_exists"
            }

        # 2. 检查IP是否在黑名单
        if self.check_ip_blacklist(ip_address):
            logger.warning(f"IP在黑名单中: {ip_address}")
            return {
                "success": False,
                "message": "您的IP地址已被限制访问",
                reason = "ip_blacklisted"
            }

        # 3. 检查用户是否在黑名单
        if self.check_user_blacklist(username):
            logger.warning(f"用户在黑名单中: {username}")
            return {
                "success": False,
                "message": "您的账号已被限制登录",
                reason = "user_blacklisted"
            }

        # 4. 验证用户凭证
        user = User.verify_credentials(username, password)
        if not user:
            logger.warning(f"密码验证失败: {username}")
            # 记录失败登录尝试
            self.record_login_attempt(username, ip_address, user_agent, False, "password_error")
            return {
                "success": False,
                "message": "用户名或密码错误",
                reason = "invalid_credentials"
            }

        # 5. 获取用户组别
        user_group = self.get_user_group(user.user_id)

        self.archive_login_info(user.user_id, username, ip_address, user_agent, user_group)

        # 7. 检查是否是异地登录
        # 异地登录检测
        is_remote_login = self.detect_remote_login(user.user_id, ip_address)
        if is_remote_login:
            logger.info(f"检测到异地登录: {username}, IP: {ip_address}")
            # 可以在这里添加额外的安全措施,如发送通知等

        logger.info(f"登录成功: {username}, IP: {ip_address}, 组别: {user_group}")
        return {
            "success": True,
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "group": user_group,
            message = "登录成功"
        }

    def check_user_exists(self, username):
        检查用户是否存在

        Args:
            username: 用户名或手机号

        Returns:
            bool: 用户是否存在
        try:
            # 先尝试通过用户名获取用户
            user = User.get_by_username(username)
                return True
            # 如果用户名不存在,尝试通过手机号获取用户
            user = User.get_by_phone(username)
            return user is not None
        except Exception as e:
            logger.error(f"检查用户存在性失败: {str(e)}")
            return False

    def check_ip_blacklist(self, ip_address):
        检查IP是否在黑名单中

        Args:
            ip_address: IP地址

        Returns:
            bool: IP是否在黑名单中
        try:
            # 从数据库查询黑名单
            result = db_manager.fetch_one(
                'SELECT id FROM ip_blacklist WHERE ip_address = ? AND is_active = 1',
                (ip_address,)
            return result is not None
        except Exception as e:
            # 当表不存在或其他错误时,默认返回False(不在黑名单中)
            return False

    def check_user_blacklist(self, username):
        检查用户是否在黑名单中

        Args:
    pass

        Returns:
            bool: 用户是否在黑名单中
        try:
            # 从数据库查询用户黑名单
            result = db_manager.fetch_one(
                'SELECT id FROM user_blacklist WHERE username = ? AND is_active = 1',
                (username,)
            )
            return result is not None
        except Exception as e:
            # 当表不存在或其他错误时,默认返回False(不在黑名单中)
            return False

        获取用户所在组别

        Args:
            user_id: 用户ID

            str: 用户组别
        try:
            # 从数据库查询用户组别
            result = db_manager.fetch_one(
                (user_id,)
            )

            logger.info(f"获取用户组别结果: {result}, user_id: {user_id}")
            if result:
                if isinstance(result, dict):
    pass
                elif isinstance(result, (list, tuple)):
    pass
                elif hasattr(result, 'group_name'):
                    return result.group_name
                elif hasattr(result, '__getitem__'):
                    try:
                        return result[0]
                    except (IndexError, TypeError):
    pass
                return str(result)
            return "default"
        except Exception as e:
            logger.error(f"获取用户组别失败: {str(e)}")
            return "default"

        归档登录信息

        Args:
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            user_group: 用户组别
        try:
            # 插入登录记录
            db_manager.execute(
                '''
                INSERT INTO user_login_history (user_id, username, ip_address, user_agent, login_time, user_group)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''',
                (user_id, username, ip_address, user_agent, user_group)
            )

            # 记录用户行为
            self.user_manager.record_user_behavior(
                user_id=user_id,
                action_data={"ip_address": ip_address, "user_agent": user_agent, "group": user_group},
                ip_address=ip_address,
                user_agent=user_agent
            )

            logger.error(f"归档登录信息失败: {str(e)}")

        记录登录尝试
        Args:
            ip_address: IP地址
            user_agent: 用户代理
            reason: 原因
        try:
            db_manager.execute(
                INSERT INTO login_attempts (username, ip_address, user_agent, success, reason, attempt_time)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (username, ip_address, user_agent, 1 if success else 0, reason)
            )
        except Exception as e:
            logger.error(f"记录登录尝试失败: {str(e)}")

    def detect_remote_login(self, user_id, current_ip):
        检测是否是异地登录

        Args:
            user_id: 用户ID
            current_ip: 当前IP地址
        Returns:
            bool: 是否是异地登录
        try:
            # 获取用户最近的登录记录
            recent_logins = db_manager.fetch_all(
                '''
                FROM user_login_history
                ORDER BY login_time DESC
                LIMIT 5
                (user_id,)
            )

                return False

            # 检查最近的IP是否与当前IP不同
            for login in recent_logins:
                if login[0] != current_ip:
                    # 计算时间差
                    current_time = datetime.now()
                    time_diff = (current_time - login_time).total_seconds()

                    # 如果时间差小于24小时且IP不同,视为异地登录
                    if time_diff < 24 * 3600:
                        return True

            return False
            logger.error(f"检测异地登录失败: {str(e)}")
            return False
    def get_login_history(self, user_id, limit=10):
    pass

        Args:
            user_id: 用户ID
            limit: 限制数量

        Returns:
            list: 登录历史记录
            history = db_manager.fetch_all(
                '''
                SELECT ip_address, user_agent, login_time, user_group
                FROM user_login_history
                WHERE user_id = ?
                ORDER BY login_time DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )

            for record in history:
                result.append({
                    "ip_address": record[0],
                    "user_agent": record[1],
                    "login_time": record[2],
                })

        except Exception as e:
            return []

    def add_to_blacklist(self, target_type, target_value, reason):
        添加到黑名单

        Args:
            target_type: 目标类型 ("ip" 或 "user")
            target_value: 目标值 (IP地址或用户名)
            reason: 原因
        Returns:
            bool: 是否添加成功
        try:
            if target_type == "ip":
                # 检查是否已存在
                existing = db_manager.fetch_one(
                    'SELECT id FROM ip_blacklist WHERE ip_address = ?',
                    (target_value,)
                )

                if existing:
                    # 更新现有记录
                        'UPDATE ip_blacklist SET is_active = 1, reason = ?, updated_at = CURRENT_TIMESTAMP WHERE ip_address = ?',
                        (reason, target_value)
                    )
                else:
                    # 插入新记录
                    db_manager.execute(
                        'INSERT INTO ip_blacklist (ip_address, reason, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                        (target_value, reason)
                    )
            elif target_type == "user":
                # 检查是否已存在
                existing = db_manager.fetch_one(
                    (target_value,)

                if existing:
                    # 更新现有记录
                    db_manager.execute(
                        'UPDATE user_blacklist SET is_active = 1, reason = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?',
                else:
                        'INSERT INTO user_blacklist (username, reason, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
            else:
                logger.error(f"无效的目标类型: {target_type}")
                return False

            logger.info(f"添加到黑名单成功: {target_type} = {target_value}")
        except Exception as e:
            logger.error(f"添加到黑名单失败: {str(e)}")
            return False

    def remove_from_blacklist(self, target_type, target_value):
    pass

        Args:
            target_type: 目标类型 ("ip" 或 "user")
            target_value: 目标值 (IP地址或用户名)

        Returns:
    pass
        try:
            if target_type == "ip":
                db_manager.execute(
                    'UPDATE ip_blacklist SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE ip_address = ?',
                    (target_value,)
            elif target_type == "user":
                db_manager.execute(
                    'UPDATE user_blacklist SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE username = ?',
                )
            else:
                logger.error(f"无效的目标类型: {target_type}")
                return False

            logger.info(f"从黑名单中移除成功: {target_type} = {target_value}")
            return True
        except Exception as e:
            logger.error(f"从黑名单中移除失败: {str(e)}")
            return False

# 使用延迟初始化,避免导入时执行数据库操作
_user_login_ai = None

def get_user_login_ai():
    获取用户登录AI单例实例

    Returns:
        UserLoginAI: 用户登录AI实例
    global _user_login_ai
    if _user_login_ai is None:
        try:
    pass
        except Exception as e:
            logger.error(f"用户登录AI初始化失败: {str(e)}")
            class SimpleUserLoginAI:
                    from app.models.user import User
import logging
                    user = User.verify_credentials(username, password)
                    if user:
                        return {
                            "user_id": user.user_id,
                            "role": user.role,
                            group = "default"
                        }
                    else:
                        return {
                            message = "用户名或密码错误"
            _user_login_ai = SimpleUserLoginAI()
    return _user_login_ai

def __getattr__(name):
    if name == 'user_login_ai':
        return get_user_login_ai()

"""