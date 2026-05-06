#!/usr/bin/env python3
"""
登录容器 - 负责管理用户登录流程和认证保护

import time
import threading
from app.models.user import User
from app.ai.login import LoginAI
from app.utils.logging import logger


class LoginContainer:
    登录容器类，负责管理用户登录流程、认证保护和状态监控

    def __init__(self):
        self.container_id = f"login_container_{id(self)}"
        self.name = "登录容器"
        self.description = "负责管理用户登录流程和认证保护"

        # 登录配置
        self.config = {
            "enabled": True,
            "max_login_attempts": 5,
            "lockout_duration": 1800,  # 30分钟
            "allow_guest_login": True,
            "two_factor_enabled": False,
            "login_record_retention": 86400,  # 登录记录保留1天
            "ip_ban_threshold": 10,  # IP地址登录失败阈值
            "session_timeout": 3600  # 会话超时时间
        }

        # 登录统计
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

        # 详细登录尝试记录
        self.login_records = []
        # IP地址登录尝试记录
        self.ip_login_attempts = {}

        # 活跃会话记录
        self.active_sessions = {}

        # 初始化登录AI
        self.login_ai = LoginAI()

        # 启动监控线程
        self._start_monitoring()

        logger.info(f"✓ 登录容器初始化成功: {self.container_id}")

    def _start_monitoring(self):
        """启动监控线程"""
        # 清理过期登录尝试记录线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_thread_func, daemon=True)
        self.cleanup_thread.start()

        # 会话超时检查线程
        self.session_check_thread = threading.Thread(target=self._session_check_thread_func, daemon=True)
        self.session_check_thread.start()

        logger.info(f"✓ 登录容器监控线程已启动")

    def _cleanup_thread_func(self):
        """定期清理过期的登录尝试记录"""
        while True:
            time.sleep(60)  # 每分钟清理一次
            self._cleanup_old_attempts()

    def _session_check_thread_func(self):
        """定期检查会话超时"""
        while True:
            time.sleep(300)  # 每5分钟检查一次
            self._check_session_timeouts()

    def _cleanup_old_attempts(self):
        current_time = time.time()

        # 清理用户登录尝试记录
        expired_users = [username for username, attempts in self.login_attempts.items()
                        if current_time - attempts["timestamp"] > self.config["lockout_duration"]]

        for username in expired_users:
            if username in self.login_attempts:
                del self.login_attempts[username]
                # 如果用户被锁定，解除锁定
                if username in self.stats["locked_out_users"]:
                    self.stats["locked_out_users"].remove(username)

        # 清理IP登录尝试记录
        expired_ips = [ip for ip, attempts in self.ip_login_attempts.items()
                      if current_time - attempts["timestamp"] > self.config["lockout_duration"]]

        for ip in expired_ips:
            if ip in self.ip_login_attempts:
                del self.ip_login_attempts[ip]
                # 如果IP被禁止，解除禁止
                    self.stats["banned_ips"].remove(ip)

        # 清理过期登录记录
        self.login_records = [record for record in self.login_records
                             if current_time - record["timestamp"] < self.config["login_record_retention"]]

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

    def _is_ip_banned(self, ip_address: str) -> bool:
        """检查IP地址是否被禁止"""
        return ip_address in self.stats["banned_ips"]

    def _record_login_attempt(self, login_context: Dict[str, Any]):
        """记录登录尝试"""
        self.login_records.append(login_context)

        # 限制登录记录数量
        if len(self.login_records) > 1000:
            self.login_records = self.login_records[-1000:]

    def _update_daily_stats(self, success: bool, username: str, ip_address: str):
        """更新每日统计信息"""
        current_date = time.strftime("%Y-%m-%d")
        current_hour = time.localtime().tm_hour

        # 更新每日统计
        if current_date not in self.stats["daily_stats"]:
            self.stats["daily_stats"][current_date] = {
                "success": 0,
                "failed": 0,
                "by_role": {}
            }

        if success:
        else:
            self.stats["daily_stats"][current_date]["failed"] += 1

        # 更新按小时统计
        self.stats["login_distribution"]["by_hour"][current_hour] += 1

        # 更新IP分布
        if ip_address not in self.stats["login_distribution"]["by_ip"]:
            self.stats["login_distribution"]["by_ip"][ip_address] = 0
        self.stats["login_distribution"]["by_ip"][ip_address] += 1

    def _update_login_attempts(self, username: str, ip_address: str, success: bool):
        """更新登录尝试记录"""
        current_time = time.time()

        # 更新用户登录尝试
        if username not in self.login_attempts:
            self.login_attempts[username] = {
                "attempts": 0,
                "timestamp": current_time,
            }

        if not success:
            self.login_attempts[username]["ip_addresses"].add(ip_address)
            self.login_attempts[username]["timestamp"] = current_time

            # 检查是否需要锁定用户
            if self.login_attempts[username]["attempts"] >= self.config["max_login_attempts"]:
                if username not in self.stats["locked_out_users"]:
                    self.stats["locked_out_users"].append(username)
                    logger.warning(f"用户被锁定: {username}")
        else:
            # 登录成功，重置尝试次数
            if username in self.login_attempts:
                del self.login_attempts[username]
            if username in self.stats["locked_out_users"]:
                self.stats["locked_out_users"].remove(username)

        # 更新IP登录尝试
        if ip_address not in self.ip_login_attempts:
            self.ip_login_attempts[ip_address] = {
                "attempts": 0,
                "usernames": set()

            self.ip_login_attempts[ip_address]["usernames"].add(username)

            if self.ip_login_attempts[ip_address]["attempts"] >= self.config["ip_ban_threshold"]:
                if ip_address not in self.stats["banned_ips"]:
                    self.stats["banned_ips"].append(ip_address)
                    logger.warning(f"IP被禁止: {ip_address}")
        else:
            # 登录成功，不重置IP尝试次数（防止暴力破解）

        """处理用户登录请求"""
        try:
            login_start_time = time.time()
            logger.info(f"🔑 登录请求: 用户={username}, IP={ip_address}")
            # 检查登录容器是否启用
            if not self.config["enabled"]:
                logger.error("❌ 登录容器已禁用")
                return {
                    "success": False,
                    "message": "登录服务暂时不可用",
                }

            # 检查IP是否被禁止
                logger.warning(f"❌ 登录被拒绝: IP={ip_address} 已被禁止")
                return {
                    "success": False,
                    "message": "您的IP地址已被禁止登录",
                    "reason": "ip_banned"
                }

            # 检查用户是否被锁定
                logger.warning(f"❌ 登录被拒绝: 用户={username} 已被锁定")
                return {
                    "success": False,
                    "message": "您的账号已被锁定，请稍后再试",
                    "reason": "user_locked"
                }

            # 使用登录AI处理登录请求

            # 更新登录统计
            if login_result["success"]:
                self.stats["successful_logins"] += 1
                logger.info(f"✅ 登录成功: 用户={username}")

                # 创建会话
                session_id = f"session_{id(username)}_{int(time.time())}"
                user = User.get_by_username(username)

                self.active_sessions[session_id] = {
                    "session_id": session_id,
                    "username": username,
                    "role": user.role,
                    "ip_address": ip_address,
                    "created_at": time.time(),
                    "last_activity": time.time(),
                    "user_agent": request.headers.get('User-Agent', 'Unknown') if request else 'Unknown'
                }

                login_result["session_id"] = session_id
                login_result["session_expires_at"] = time.time() + self.config["session_timeout"]
            else:
                self.stats["failed_logins"] += 1
                logger.warning(f"❌ 登录失败: 用户={username}, 原因={login_result.get('reason', 'unknown')}")

            # 更新登录尝试记录
            self._update_login_attempts(username, ip_address, login_result["success"])

            # 更新统计信息
            self._update_daily_stats(login_result["success"], username, ip_address)

            # 更新按角色统计
            if login_result["success"]:
                user = User.get_by_username(username)
                role = user.role
                if role not in self.stats["login_distribution"]["by_role"]:
                    self.stats["login_distribution"]["by_role"][role] = 0
                self.stats["login_distribution"]["by_role"][role] += 1

            login_duration = time.time() - login_start_time
            logger.info(f"⏱️  登录处理耗时: {login_duration:.3f}秒")
            return login_result

        except Exception as e:
            logger.error(f"❌ 登录处理出错: {str(e)}")
            return {
                "success": False,
                "message": "登录过程中发生错误",
                "error": str(e)
            }

    def process_logout(self, session_id: str) -> Dict[str, Any]:
        try:
            if session_id in self.active_sessions:
                username = self.active_sessions[session_id]["username"]
                del self.active_sessions[session_id]
                logger.info(f"✅ 登出成功: 用户={username}, 会话={session_id}")
                    "success": True,
                    "session_id": session_id
                }
            else:
                logger.warning(f"❌ 登出失败: 会话不存在={session_id}")
                    "success": False,
                    "message": "会话不存在或已过期"
                }
        except Exception as e:
            logger.error(f"❌ 登出处理出错: {str(e)}")
                "success": False,
                "message": "登出过程中发生错误",
                "error": str(e)
            }

        try:
            if session_id in self.active_sessions:
                # 更新最后活动时间
                session["last_activity"] = time.time()
                self.active_sessions[session_id] = session

                logger.info(f"✅ 会话有效: 用户={session['username']}, 会话={session_id}")
                return {
                    "success": True,
                    "session": session,
                    "message": "会话有效"
                }
            else:
                logger.warning(f"❌ 会话无效: {session_id}")
                    "success": True,
                    "valid": False,
                    "message": "会话不存在或已过期"
                }
        except Exception as e:
            logger.error(f"❌ 会话验证出错: {str(e)}")
                "success": False,
                "message": "会话验证过程中发生错误",
                "error": str(e)

    def get_status(self) -> Dict[str, Any]:
        return {
            "container_id": self.container_id,
            "name": self.name,
            "description": self.description,
            "status": "running" if self.config["enabled"] else "disabled",
            "config": self.config,
            "stats": self.stats,
            "active_sessions": len(self.active_sessions),
            "login_attempts": len(self.login_attempts),
            "ip_login_attempts": len(self.ip_login_attempts),
            "login_records": len(self.login_records),
            "locked_out_users": len(self.stats["locked_out_users"]),
            "banned_ips": len(self.stats["banned_ips"]),
        }

    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.config.update(config_updates)
            logger.info(f"✅ 登录容器配置已更新: {config_updates}")
            return {
                "success": True,
                "message": "配置更新成功",
                "config": self.config
            }
        except Exception as e:
            logger.error(f"❌ 更新配置出错: {str(e)}")
                "success": False,
                "error": str(e)
            }

    def reset_container(self) -> Dict[str, Any]:
        try:
            # 重置所有状态
            self.login_attempts = {}
            self.ip_login_attempts = {}
            self.login_records = []
            self.stats["locked_out_users"] = []
            self.stats["banned_ips"] = []

            # 不重置统计数据和配置

            logger.info(f"✅ 登录容器已重置: {self.container_id}")
            return {
                "success": True,
                "message": "登录容器已重置"
            }
        except Exception as e:
            logger.error(f"❌ 重置容器出错: {str(e)}")
                "success": False,
                "message": "重置失败",
                "error": str(e)
            }


login_container = LoginContainer()
