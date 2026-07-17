# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
登录容器 - 负责管理用户登录流程和认证保护
"""

import time
import threading
from typing import Dict, Any
from app.models.user import User
from app.ai.login import LoginAI
from app.utils.logging import logger
import logging


class LoginContainer:
    """登录容器类 - 负责管理用户登录流程,认证保护和状态监控"""

    def __init__(self):
        self.container_id = f"login_container_{id(self)}"
        self.name = "登录容器"
        self.description = "负责管理用户登录流程和认证保护"

        self.config = {
            "enabled": True,
            "max_login_attempts": 5,
            "lockout_duration": 1800,
            "allow_guest_login": True,
            "two_factor_enabled": False,
            "login_record_retention": 86400,
            "ip_ban_threshold": 10,
            "session_timeout": 3600
        }

        self.stats = {
            "total_login_attempts": 0,
            "successful_logins": 0,
            "failed_logins": 0,
            "locked_out_users": [],
            "banned_ips": [],
            "daily_stats": {},
            "hourly_stats": {},
            "login_distribution": {
                "by_role": {},
                "by_ip": {},
                "by_hour": [0] * 24
            }
        }

        self.login_records = []
        self.ip_login_attempts = {}
        self.login_attempts = {}
        self.active_sessions = {}

        self.login_ai = LoginAI()

        self._start_monitoring()

        logger.info(f"✓ 登录容器初始化成功: {self.container_id}")

    def _start_monitoring(self):
        """启动监控线程"""
        self.cleanup_thread = threading.Thread(target=self._cleanup_thread_func, daemon=True)
        self.cleanup_thread.start()

        self.session_check_thread = threading.Thread(target=self._session_check_thread_func, daemon=True)
        self.session_check_thread.start()

        logger.info(f"✓ 登录容器监控线程已启动")

    def _cleanup_thread_func(self):
        """定期清理过期的登录尝试记录"""
        while True:
            time.sleep(60)
            self._cleanup_old_attempts()

    def _session_check_thread_func(self):
        """定期检查会话超时"""
        while True:
            time.sleep(300)
            self._check_session_timeouts()

    def _cleanup_old_attempts(self):
        """清理过期登录尝试"""
        current_time = time.time()

        expired_users = [
            username for username, attempts in self.login_attempts.items()
            if current_time - attempts["timestamp"] > self.config["lockout_duration"]
        ]

        for username in expired_users:
            if username in self.login_attempts:
                del self.login_attempts[username]
                if username in self.stats["locked_out_users"]:
                    self.stats["locked_out_users"].remove(username)

        expired_ips = [
            ip for ip, attempts in self.ip_login_attempts.items()
            if current_time - attempts["timestamp"] > self.config["lockout_duration"]
        ]

        for ip in expired_ips:
            if ip in self.ip_login_attempts:
                del self.ip_login_attempts[ip]
                if ip in self.stats["banned_ips"]:
                    self.stats["banned_ips"].remove(ip)

        self.login_records = [
            record for record in self.login_records
            if current_time - record["timestamp"] < self.config["login_record_retention"]
        ]

    def _check_session_timeouts(self):
        """检查会话超时"""
        current_time = time.time()
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            if current_time - session_data["last_activity"] > self.config["session_timeout"]:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            if session_id in self.active_sessions:
                logger.info(f"会话超时: {session_id}, 用户: {self.active_sessions[session_id]['username']}")
                del self.active_sessions[session_id]

    def _is_user_locked(self, username: str) -> bool:
        """检查用户是否被锁定"""
        return username in self.stats["locked_out_users"]

    def _record_login_attempt(self, login_context: Dict[str, Any]):
        """记录登录尝试"""
        self.login_records.append(login_context)

        if len(self.login_records) > 1000:
            self.login_records = self.login_records[-1000:]

    def _update_daily_stats(self, success: bool, username: str, ip_address: str):
        """更新每日统计信息"""
        current_date = time.strftime("%Y-%m-%d")
        current_hour = time.localtime().tm_hour

        if current_date not in self.stats["daily_stats"]:
            self.stats["daily_stats"][current_date] = {
                "success": 0,
                "failed": 0,
                "by_role": {}
            }

        if success:
            self.stats["daily_stats"][current_date]["success"] += 1
        else:
            self.stats["daily_stats"][current_date]["failed"] += 1

        self.stats["login_distribution"]["by_hour"][current_hour] += 1

        if ip_address not in self.stats["login_distribution"]["by_ip"]:
            self.stats["login_distribution"]["by_ip"][ip_address] = 0
        self.stats["login_distribution"]["by_ip"][ip_address] += 1

    def _update_login_attempts(self, username: str, ip_address: str, success: bool):
        """更新登录尝试记录"""
        current_time = time.time()

        if username not in self.login_attempts:
            self.login_attempts[username] = {
                "attempts": 0,
                "timestamp": current_time,
                "ip_addresses": set()
            }

        if not success:
            self.login_attempts[username]["ip_addresses"].add(ip_address)
            self.login_attempts[username]["timestamp"] = current_time

            if self.login_attempts[username]["attempts"] >= self.config["max_login_attempts"]:
                if username not in self.stats["locked_out_users"]:
                    self.stats["locked_out_users"].append(username)
                    logger.warning(f"用户被锁定: {username}")
        else:
            if username in self.login_attempts:
                del self.login_attempts[username]
            if username in self.stats["locked_out_users"]:
                self.stats["locked_out_users"].remove(username)

        if ip_address not in self.ip_login_attempts:
            self.ip_login_attempts[ip_address] = {
                "attempts": 0,
                "usernames": set()
            }

        self.ip_login_attempts[ip_address]["usernames"].add(username)

        if self.ip_login_attempts[ip_address]["attempts"] >= self.config["ip_ban_threshold"]:
            if ip_address not in self.stats["banned_ips"]:
                self.stats["banned_ips"].append(ip_address)
                logger.warning(f"IP被禁止: {ip_address}")

    def handle_login(self, username: str, password: str, ip_address: str) -> Dict[str, Any]:
        """处理用户登录请求"""
        try:
            login_start_time = time.time()
            logger.info(f"🔑 登录请求: 用户={username}, IP={ip_address}")

            if not self.config["enabled"]:
                logger.error("❌ 登录容器已禁用")
                return {"success": False, "error": "登录功能已禁用"}

            if self._is_user_locked(username):
                logger.warning(f"⚠️ 用户被锁定: {username}")
                return {"success": False, "error": "用户已被锁定"}

            if ip_address in self.stats["banned_ips"]:
                logger.warning(f"⚠️ IP被禁止: {ip_address}")
                return {"success": False, "error": "IP已被禁止"}

            user = User.authenticate(username, password)

            if user:
                self.stats["successful_logins"] += 1
                self._update_login_attempts(username, ip_address, True)
                self._update_daily_stats(True, username, ip_address)

                session_id = f"session_{int(time.time())}_{username}"
                self.active_sessions[session_id] = {
                    "username": username,
                    "user_id": user.user_id,
                    "login_time": time.time(),
                    "last_activity": time.time(),
                    "ip_address": ip_address
                }

                logger.info(f"✅ 登录成功: {username}")
                return {
                    "success": True,
                    "session_id": session_id,
                    "user": {
                        "username": user.username,
                        "role": user.role,
                        "user_id": user.user_id
                    }
                }
            else:
                self.stats["failed_logins"] += 1
                self._update_login_attempts(username, ip_address, False)
                self._update_daily_stats(False, username, ip_address)

                logger.warning(f"❌ 登录失败: {username}")
                return {"success": False, "error": "用户名或密码错误"}

        except Exception as e:
            logger.error(f"❌ 登录处理出错: {str(e)}")
            return {"success": False, "error": f"登录处理出错: {str(e)}"}

    def get_status(self) -> Dict[str, Any]:
        """获取容器状态"""
        return {
            "status": "running",
            "container_id": self.container_id,
            "name": self.name,
            "stats": self.stats,
            "active_sessions": len(self.active_sessions)
        }


login_container = LoginContainer()
