# -*- coding: utf-8 -*-
import time
import threading
import hashlib
from app.utils.logging import logger
from app.models.user import User
from app.ai.validator import validator_ai
from app.config import Config
from app.utils.security import security_utils
import logging

class LoginAI:
    """登录专用AI: 负责处理用户登录流程"""

    def __init__(self):
        self.instance_id = f"login_ai_{id(self)}"
        self.name = "登录AI"
        self.description = "负责处理用户登录流程, 包括验证,监控和统计"
        self.logger = logger
        self.logger.info(f"初始化登录AI: {self.instance_id}")

        self.login_config = {
            "enabled": True,
            "max_login_attempts": 5,
            "lockout_duration": 1800,
            "allow_guest_login": True,
            "two_factor_enabled": False,
            "login_record_retention": 86400,
            "ip_ban_threshold": 10
        }

        self.login_stats = {
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

        self.login_attempts = {}
        self.login_records = []
        self.ip_login_attempts = {}

    def login_user(self, username, password, ip_address="127.0.0.1", request=None):
        """处理用户登录请求: 优化登录逻辑分析"""
        try:
            login_start_time = time.time()
            self.logger.info(f"{self.instance_id} 收到登录请求,用户: {username}, IP: {ip_address}")

            self._cleanup_old_attempts()
            self.login_stats["total_login_attempts"] += 1

            login_context = {
                "username": username,
                "ip_address": ip_address,
                "timestamp": time.time(),
                "user_agent": request.headers.get('User-Agent', 'Unknown') if request else 'Unknown',
                "status": "attempted"
            }

            if self._is_user_locked(username):
                self.login_stats["failed_logins"] += 1
                self._update_daily_stats(success=False, username=username, ip_address=ip_address)
                login_context["status"] = "failed"
                login_context["reason"] = "user_locked"
                self._record_login_attempt(login_context)
                self.logger.warning(f"{self.instance_id} 用户已被锁定: {username}, IP: {ip_address}")
                return {"success": False, "message": "用户已被锁定"}
        except Exception as e:
            self.logger.error(f"登录处理出错: {str(e)}")
            return {"success": False, "message": str(e)}

    def _check_login_attempts(self, username, ip_address):
        """检查登录尝试次数: 返回剩余尝试次数"""
        if ip_address in self.login_stats["banned_ips"]:
            return 0
        return self.login_config["max_login_attempts"] - self.login_attempts.get(username, {}).get("count", 0)

    def _record_failed_attempt(self, username, ip_address):
        """记录失败的登录尝试"""
        if username not in self.login_attempts:
            self.login_attempts[username] = {
                "count": 0,
                "ip": ip_address,
                "last_attempt": time.time()
            }

        self.login_attempts[username]["count"] += 1
        self.login_attempts[username]["last_attempt"] = time.time()
        self.login_attempts[username]["ip"] = ip_address

        if ip_address not in self.ip_login_attempts:
            self.ip_login_attempts[ip_address] = {
                "count": 0,
                "last_attempt": time.time()
            }

        self.ip_login_attempts[ip_address]["count"] += 1
        self.ip_login_attempts[ip_address]["last_attempt"] = time.time()

    def _reset_login_attempts(self, username, ip_address):
        """重置登录尝试次数"""
        if username in self.login_attempts:
            del self.login_attempts[username]

        if ip_address in self.ip_login_attempts:
            self.ip_login_attempts[ip_address]["count"] = max(0, self.ip_login_attempts[ip_address]["count"] - 1)

    def _cleanup_old_attempts(self):
        """清理过期的登录尝试记录"""
        current_time = time.time()
        expired_usernames = []
        expired_ips = []
        expired_records = []

        for username, attempt in self.login_attempts.items():
            if current_time - attempt['last_attempt'] > 3600:
                expired_usernames.append(username)

        for username in expired_usernames:
            del self.login_attempts[username]

        for ip, attempt in self.ip_login_attempts.items():
            if current_time - attempt['last_attempt'] > 7200:
                expired_ips.append(ip)

        for ip in expired_ips:
            del self.ip_login_attempts[ip]

        retention_time = self.login_config.get("login_record_retention", 86400)
        for i, record in enumerate(self.login_records):
            if current_time - record['timestamp'] > retention_time:
                expired_records.append(i)

        for i in reversed(expired_records):
            del self.login_records[i]

        if expired_usernames or expired_ips or expired_records:
            self.logger.info(f"{self.instance_id} 清理了 {len(expired_usernames)} 条用户登录尝试记录, {len(expired_ips)} 条IP登录尝试记录, {len(expired_records)} 条登录记录")

    def _is_user_locked(self, username):
        """检查用户是否被锁定"""
        return username in self.login_stats["locked_out_users"]

    def _lock_user(self, username):
        """锁定用户"""
        if username not in self.login_stats["locked_out_users"]:
            self.login_stats["locked_out_users"].append(username)
            self.logger.warning(f"{self.instance_id} 用户已被锁定: {username}")

    def _unlock_user(self, username):
        """解锁用户"""
        if username in self.login_stats["locked_out_users"]:
            self.login_stats["locked_out_users"].remove(username)
            if username in self.login_attempts:
                del self.login_attempts[username]
            self.logger.info(f"{self.instance_id} 用户已解锁: {username}")

    def _update_daily_stats(self, success=True, username=None, ip_address=None, user_role=None):
        """更新每日统计信息"""
        today = time.strftime("%Y-%m-%d")
        current_hour = int(time.strftime("%H"))

        if today not in self.login_stats["daily_stats"]:
            self.login_stats["daily_stats"][today] = {
                "login_attempts": 0,
                "successful": 0,
                "failed": 0,
                "by_role": {},
                "by_ip": {}
            }

        self.login_stats["daily_stats"][today]["login_attempts"] += 1
        if success:
            self.login_stats["daily_stats"][today]["successful"] += 1
        else:
            self.login_stats["daily_stats"][today]["failed"] += 1

        if user_role:
            if user_role not in self.login_stats["daily_stats"][today]["by_role"]:
                self.login_stats["daily_stats"][today]["by_role"][user_role] = 0
            self.login_stats["daily_stats"][today]["by_role"][user_role] += 1

        if ip_address:
            if ip_address not in self.login_stats["daily_stats"][today]["by_ip"]:
                self.login_stats["daily_stats"][today]["by_ip"][ip_address] = 0
            self.login_stats["daily_stats"][today]["by_ip"][ip_address] += 1

        hour_key = f"{today}_{current_hour}"
        if hour_key not in self.login_stats["hourly_stats"]:
            self.login_stats["hourly_stats"][hour_key] = {
                "login_attempts": 0,
                "successful": 0,
                "failed": 0
            }

        self.login_stats["hourly_stats"][hour_key]["login_attempts"] += 1
        if success:
            self.login_stats["hourly_stats"][hour_key]["successful"] += 1
        else:
            self.login_stats["hourly_stats"][hour_key]["failed"] += 1

        if success and user_role:
            if user_role not in self.login_stats["login_distribution"]["by_role"]:
                self.login_stats["login_distribution"]["by_role"][user_role] = 0
            self.login_stats["login_distribution"]["by_role"][user_role] += 1

        if ip_address:
            if ip_address not in self.login_stats["login_distribution"]["by_ip"]:
                self.login_stats["login_distribution"]["by_ip"][ip_address] = 0
            self.login_stats["login_distribution"]["by_ip"][ip_address] += 1

        self.login_stats["login_distribution"]["by_hour"][current_hour] += 1

    def _record_login_attempt(self, login_context):
        """记录详细的登录尝试"""
        self.login_records.append(login_context)
        max_records = 1000
        if len(self.login_records) > max_records:
            self.login_records = self.login_records[-max_records:]

    def _ban_ip(self, ip_address):
        """禁止IP地址"""
        if ip_address not in self.login_stats["banned_ips"]:
            self.login_stats["banned_ips"].append(ip_address)
            self.logger.warning(f"{self.instance_id} IP地址已被禁止: {ip_address}")
            threading.Timer(self.login_config["lockout_duration"] * 2, self._unban_ip, args=[ip_address]).start()

    def _unban_ip(self, ip_address):
        """解除IP地址禁止"""
        if ip_address in self.login_stats["banned_ips"]:
            self.login_stats["banned_ips"].remove(ip_address)
            if ip_address in self.ip_login_attempts:
                del self.ip_login_attempts[ip_address]
            self.logger.info(f"{self.instance_id} IP地址已解除禁止: {ip_address}")

    def get_login_stats(self):
        """获取登录统计信息: 包含详细的登录分析"""
        success_rate = 0
        if self.login_stats["total_login_attempts"] > 0:
            success_rate = (self.login_stats["successful_logins"] / self.login_stats["total_login_attempts"]) * 100

        average_duration = 0
        if self.login_records:
            success_records = [r for r in self.login_records if r["status"] == "success" and "duration" in r]
            if success_records:
                total_duration = sum(r["duration"] for r in success_records)
                average_duration = total_duration / len(success_records)

        recent_records = sorted(self.login_records, key=lambda x: x["timestamp"], reverse=True)[:20]

        return {
            "total_attempts": self.login_stats["total_login_attempts"],
            "successful_logins": self.login_stats["successful_logins"],
            "failed_logins": self.login_stats["failed_logins"],
            "success_rate": success_rate,
            "average_duration": average_duration,
            "recent_records": recent_records
        }

    def get_user_login_history(self, username):
        """获取用户登录历史"""
        user_history = [
            record for record in self.login_records
            if record["username"] == username
        ]
        user_history.sort(key=lambda x: x["timestamp"], reverse=True)
        return user_history

    def get_login_analysis_report(self):
        """生成详细的登录分析报告"""
        today = time.strftime("%Y-%m-%d")
        yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))

        today_stats = self.login_stats["daily_stats"].get(today, {
            "login_attempts": 0,
            "successful": 0,
            "failed": 0
        })

        yesterday_stats = self.login_stats["daily_stats"].get(yesterday, {
            "login_attempts": 0,
            "successful": 0,
            "failed": 0
        })

        def calculate_change(current, previous):
            if previous == 0:
                return 0 if current == 0 else 100
            return ((current - previous) / previous) * 100

        return {
            "today": today_stats,
            "yesterday": yesterday_stats,
            "change_percentage": {
                "attempts": calculate_change(today_stats["login_attempts"], yesterday_stats["login_attempts"]),
                "successful": calculate_change(today_stats["successful"], yesterday_stats["successful"]),
                "failed": calculate_change(today_stats["failed"], yesterday_stats["failed"])
            }
        }

    def _hash_password(self, password, salt):
        """使用PBKDF2算法对密码进行哈希"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)

    def __str__(self):
        return f"LoginAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()
