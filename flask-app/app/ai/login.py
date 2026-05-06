# -*- coding: utf-8 -*-
import time
import threading
import hashlib
from app.utils.logging import logger
from app.models.user import User
from app.ai.validator import validator_ai
from app.config import Config
from app.utils.security import security_utils

class LoginAI:
    """登录专用AI，负责处理用户登录流程"""

    def __init__(self):
        self.instance_id = f"login_ai_{id(self)}"
        self.name = "登录AI"
        self.description = "负责处理用户登录流程，包括验证、监控和统计"
        self.logger = logger
        self.logger.info(f"初始化登录AI: {self.instance_id}")

        # 登录配置
        self.login_config = {
            "enabled": True,
            "max_login_attempts": 5,
            "lockout_duration": 1800,  # 30分钟
            "allow_guest_login": True,
            "two_factor_enabled": False,
            "login_record_retention": 86400,  # 登录记录保留1天
            "ip_ban_threshold": 10  # IP地址登录失败阈值
        }

        # 登录统计
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

        # 登录尝试记录
        self.login_attempts = {}
        # 详细登录尝试记录
        self.login_records = []
        # IP地址登录尝试记录
        self.ip_login_attempts = {}

    def login_user(self, username, password, ip_address="127.0.0.1", request=None):
        """处理用户登录请求，优化登录逻辑分析"""
        try:
            login_start_time = time.time()
            self.logger.info(f"{self.instance_id} 收到登录请求，用户: {username}, IP: {ip_address}")

            # 清理过期的登录尝试记录
            self._cleanup_old_attempts()

            # 增加总登录尝试次数
            self.login_stats["total_login_attempts"] += 1

            # 记录登录尝试上下文
            login_context = {
                "username": username,
                "ip_address": ip_address,
                "timestamp": time.time(),
                "user_agent": request.headers.get('User-Agent', 'Unknown') if request else 'Unknown',
                "status": "attempted"

            # 检查用户是否被锁定
            if self._is_user_locked(username):
                self.login_stats["failed_logins"] += 1
                # 更新每日失败统计
                self._update_daily_stats(success=False, username=username, ip_address=ip_address)
                # 更新详细的登录记录
                login_context["status"] = "failed"
                login_context["reason"] = "user_locked"
                self._record_login_attempt(login_context)

                self.logger.warning(f"{self.instance_id} 用户已被锁定: {username}, IP: {ip_address}")
                return {
                    "success": False,
                    "message": "用户已被锁定，请稍后再试",
                    "user": None,
                    "attempts_left": 0

            # 检查登录尝试次数
            attempts_left = self._check_login_attempts(username, ip_address)
            if attempts_left <= 0:
                self.login_stats["failed_logins"] += 1
                # 更新每日失败统计
                self._update_daily_stats(success=False, username=username, ip_address=ip_address)
                # 更新详细的登录记录
                login_context["reason"] = "too_many_attempts"

                return {
                    "message": f"登录尝试次数过多，请稍后再试",
                    "attempts_left": 0

            validation_result = self._validate_login_data(username, password)
            if not validation_result["success"]:
                self._record_failed_attempt(username, ip_address)
                self.login_stats["failed_logins"] += 1
                self._update_daily_stats(success=False, username=username, ip_address=ip_address)
                # 更新详细的登录记录
                login_context["errors"] = validation_result["errors"]
                return {
                    "success": False,
                    "errors": validation_result["errors"],
                    "attempts_left": attempts_left - 1
            # 检查用户是否存在
            user = User.get_by_username(username)
                self._record_failed_attempt(username, ip_address)
                self.login_stats["failed_logins"] += 1
                # 更新每日失败统计
                self._update_daily_stats(success=False, username=username, ip_address=ip_address)
                login_context["status"] = "failed"
                login_context["reason"] = "user_not_found"

                self.logger.warning(f"{self.instance_id} 用户不存在: {username}, IP: {ip_address}")
                    "message": "用户名或密码错误",
                    "user": None,
                    "attempts_left": attempts_left - 1
            # 验证密码
            if not security_utils.verify_password(user.password, password):
                self._record_failed_attempt(username, ip_address)
                # 更新每日失败统计
                self._update_daily_stats(success=False, username=username, ip_address=ip_address)
                # 更新详细的登录记录
                login_context["reason"] = "incorrect_password"
                self._record_login_attempt(login_context)
                self.logger.warning(f"{self.instance_id} 密码验证失败: 用户 {username}, IP: {ip_address}")
                    "message": "用户名或密码错误",
                    "attempts_left": attempts_left - 1

            # 登录成功，重置登录尝试记录
            self._reset_login_attempts(username, ip_address)
            # 增加成功登录次数

            # 更新每日成功统计

            # 更新详细的登录记录
            login_context["user_id"] = user.user_id if hasattr(user, 'user_id') else None
            login_context["duration"] = time.time() - login_start_time
            self._record_login_attempt(login_context)


                "success": True,
                "message": "登录成功",
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at
                "login_info": {
                    "ip_address": ip_address,
                    "duration": login_context["duration"]
        except Exception as e:
            self.login_stats["failed_logins"] += 1
            login_context["status"] = "error"
            login_context["reason"] = "system_error"
            self._record_login_attempt(login_context)

            self.logger.error(f"{self.instance_id} 登录失败: {str(e)}")
                "message": "登录过程中发生错误，请稍后再试",

        """验证登录数据"""
        # 定义登录数据的验证模式，只做最基本的验证
        schema = {
            "username": {
                "required": True,
                "type": "string"
            },
            "password": {
                "required": True,
                "type": "string"

            "username": username,
            "password": password

        return validator_ai.validate_data(data, schema)

    def _check_login_attempts(self, username, ip_address):
        """检查登录尝试次数，返回剩余尝试次数"""
        # 检查IP地址是否被禁止
        if ip_address in self.login_stats["banned_ips"]:
            return 0

        # 检查用户名登录尝试次数
        user_attempts = self.login_attempts.get(username, {}).get("count", 0)
        ip_attempts = self.ip_login_attempts.get(ip_address, {}).get("count", 0)

        # 如果IP地址尝试次数过多，禁止该IP
        if ip_attempts >= self.login_config["ip_ban_threshold"]:
            self._ban_ip(ip_address)
            return 0

        # 如果用户尝试次数过多，锁定用户
        if user_attempts >= self.login_config["max_login_attempts"]:
            return 0

        # 返回剩余尝试次数
        return self.login_config["max_login_attempts"] - user_attempts

    def _record_failed_attempt(self, username, ip_address):
        """记录失败的登录尝试"""
        # 更新用户名登录尝试记录
        if username not in self.login_attempts:
            self.login_attempts[username] = {
                "count": 0,
                "ip": ip_address,
                "last_attempt": time.time()

        self.login_attempts[username]["count"] += 1
        self.login_attempts[username]["last_attempt"] = time.time()
        self.login_attempts[username]["ip"] = ip_address

        # 更新IP地址登录尝试记录
        if ip_address not in self.ip_login_attempts:
            self.ip_login_attempts[ip_address] = {
                "count": 0,
                "last_attempt": time.time()

        self.ip_login_attempts[ip_address]["count"] += 1
        self.ip_login_attempts[ip_address]["last_attempt"] = time.time()

        """重置登录尝试次数"""
        if username in self.login_attempts:
            del self.login_attempts[username]

        # 重置IP地址登录尝试记录（如果是成功登录）
        if ip_address in self.ip_login_attempts:
            self.ip_login_attempts[ip_address]["count"] = max(0, self.ip_login_attempts[ip_address]["count"] - 1)

    def _cleanup_old_attempts(self):
        """清理过期的登录尝试记录"""
        current_time = time.time()
        expired_usernames = []
        expired_ips = []
        expired_records = []

        # 清理用户名登录尝试记录（超过1小时）
        for username, attempt in self.login_attempts.items():
            if current_time - attempt['last_attempt'] > 3600:  # 1小时过期
                expired_usernames.append(username)

        for username in expired_usernames:
            del self.login_attempts[username]

        # 清理IP登录尝试记录（超过2小时）
        for ip, attempt in self.ip_login_attempts.items():
            if current_time - attempt['last_attempt'] > 7200:  # 2小时过期
                expired_ips.append(ip)
        for ip in expired_ips:
            del self.ip_login_attempts[ip]

        # 清理旧的登录记录（超过配置的保留时间）
        for i, record in enumerate(self.login_records):
            if current_time - record['timestamp'] > retention_time:
                expired_records.append(i)

        # 从后往前删除，避免索引问题
        for i in reversed(expired_records):
            del self.login_records[i]

        if expired_usernames or expired_ips or expired_records:
            self.logger.info(f"{self.instance_id} 清理了 {len(expired_usernames)} 条用户登录尝试记录, {len(expired_ips)} 条IP登录尝试记录, {len(expired_records)} 条登录记录")

    def _is_user_locked(self, username):
        """检查用户是否被锁定"""
        # 简单的用户锁定逻辑，实际项目中可以使用更复杂的算法
        return username in self.login_stats["locked_out_users"]

    def _lock_user(self, username):
        """锁定用户"""
        if username not in self.login_stats["locked_out_users"]:
            self.login_stats["locked_out_users"].append(username)
            self.logger.warning(f"{self.instance_id} 用户已被锁定: {username}")

            # 设置解锁定时器

        """解锁用户"""
        if username in self.login_stats["locked_out_users"]:
            self.login_stats["locked_out_users"].remove(username)
            # 重置登录尝试次数
            if username in self.login_attempts:
                del self.login_attempts[username]
            self.logger.info(f"{self.instance_id} 用户已解锁: {username}")

    def _update_daily_stats(self, success=True, username=None, ip_address=None, user_role=None):
        """更新每日统计信息"""
        today = time.strftime("%Y-%m-%d")
        current_hour = int(time.strftime("%H"))

        # 更新每日统计
        if today not in self.login_stats["daily_stats"]:
            self.login_stats["daily_stats"][today] = {
                "login_attempts": 0,
                "successful": 0,
                "failed": 0,
                "by_role": {},
                "by_ip": {}

        self.login_stats["daily_stats"][today]["login_attempts"] += 1
        if success:
            self.login_stats["daily_stats"][today]["successful"] += 1
        else:
            self.login_stats["daily_stats"][today]["failed"] += 1

        # 更新按角色统计
            if user_role not in self.login_stats["daily_stats"][today]["by_role"]:
                self.login_stats["daily_stats"][today]["by_role"][user_role] = 0
            self.login_stats["daily_stats"][today]["by_role"][user_role] += 1

        # 更新按IP统计
            if ip_address not in self.login_stats["daily_stats"][today]["by_ip"]:
                self.login_stats["daily_stats"][today]["by_ip"][ip_address] = 0
            self.login_stats["daily_stats"][today]["by_ip"][ip_address] += 1

        # 更新每小时统计
        hour_key = f"{today}_{current_hour}"
        if hour_key not in self.login_stats["hourly_stats"]:
            self.login_stats["hourly_stats"][hour_key] = {
                "login_attempts": 0,
                "successful": 0,
                "failed": 0

        self.login_stats["hourly_stats"][hour_key]["login_attempts"] += 1
        if success:
            self.login_stats["hourly_stats"][hour_key]["successful"] += 1
        else:
            self.login_stats["hourly_stats"][hour_key]["failed"] += 1

        # 更新登录分布统计
        if success and user_role:
            if user_role not in self.login_stats["login_distribution"]["by_role"]:
                self.login_stats["login_distribution"]["by_role"][user_role] = 0
            self.login_stats["login_distribution"]["by_role"][user_role] += 1

        if ip_address:
            if ip_address not in self.login_stats["login_distribution"]["by_ip"]:
                self.login_stats["login_distribution"]["by_ip"][ip_address] = 0
            self.login_stats["login_distribution"]["by_ip"][ip_address] += 1

        # 更新按小时分布
        self.login_stats["login_distribution"]["by_hour"][current_hour] += 1

    def _record_login_attempt(self, login_context):
        """记录详细的登录尝试"""
        # 添加登录记录
        self.login_records.append(login_context)
        # 限制登录记录数量
        if len(self.login_records) > max_records:
            self.login_records = self.login_records[-max_records:]

    def _ban_ip(self, ip_address):
        """禁止IP地址"""
        if ip_address not in self.login_stats["banned_ips"]:
            self.login_stats["banned_ips"].append(ip_address)
            self.logger.warning(f"{self.instance_id} IP地址已被禁止: {ip_address}")

            # 设置IP解禁令定时器
            threading.Timer(self.login_config["lockout_duration"] * 2, self._unban_ip, args=[ip_address]).start()

    def _unban_ip(self, ip_address):
        """解除IP地址禁止"""
        if ip_address in self.login_stats["banned_ips"]:
            self.login_stats["banned_ips"].remove(ip_address)
            # 清理该IP的登录尝试记录
            if ip_address in self.ip_login_attempts:
                del self.ip_login_attempts[ip_address]
            self.logger.info(f"{self.instance_id} IP地址已解除禁止: {ip_address}")

    def get_login_stats(self):
        """获取登录统计信息，包含详细的登录分析"""
        # 计算成功率
        success_rate = 0
        if self.login_stats["total_login_attempts"] > 0:
            success_rate = (self.login_stats["successful_logins"] / self.login_stats["total_login_attempts"]) * 100

        # 计算平均登录时间
        average_duration = 0
        if self.login_records:
            success_records = [r for r in self.login_records if r["status"] == "success" and "duration" in r]
            if success_records:
                total_duration = sum(r["duration"] for r in success_records)
                average_duration = total_duration / len(success_records)

        # 获取最近的登录记录
        recent_records = sorted(self.login_records, key=lambda x: x["timestamp"], reverse=True)[:20]

        return {
            **self.login_stats,
            "success_rate": round(success_rate, 2),
            "average_login_duration": round(average_duration, 3),
            "recent_login_attempts": recent_records,
            "current_attempts": {
                "by_username": {k: v["count"] for k, v in self.login_attempts.items()},
                "by_ip": {k: v["count"] for k, v in self.ip_login_attempts.items()}
    def get_user_login_history(self, username):
        """获取用户登录历史"""
        user_history = [
            record for record in self.login_records
            if record["username"] == username
        ]
        # 按时间倒序排列
        user_history.sort(key=lambda x: x["timestamp"], reverse=True)
        return user_history

    def get_login_analysis_report(self):
        """生成详细的登录分析报告"""
        today = time.strftime("%Y-%m-%d")
        yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))

        # 今天的统计
        today_stats = self.login_stats["daily_stats"].get(today, {
            "login_attempts": 0,
            "successful": 0,
            "failed": 0
        })

        # 昨天的统计
        yesterday_stats = self.login_stats["daily_stats"].get(yesterday, {
            "login_attempts": 0,
            "successful": 0,
            "failed": 0
        })

        # 计算今日与昨日的变化
            if previous == 0:
                return 0 if current == 0 else 100
            return round(((current - previous) / previous) * 100, 2)

        change = {
            "login_attempts": calculate_change(today_stats["login_attempts"], yesterday_stats["login_attempts"]),
            "successful": calculate_change(today_stats["successful"], yesterday_stats["successful"]),
            "failed": calculate_change(today_stats["failed"], yesterday_stats["failed"])

        # 分析失败原因
        for record in self.login_records:
            if record["status"] == "failed" and "reason" in record:
                reason = record["reason"]
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        # 分析登录高峰
        peak_hour = self.login_stats["login_distribution"]["by_hour"].index(max(self.login_stats["login_distribution"]["by_hour"]))

        return {
            "today": today_stats,
            "yesterday": yesterday_stats,
            "change": change,
            "failure_reasons": failure_reasons,
            "peak_login_hour": peak_hour,
            "ban_status": {
                "banned_ips_count": len(self.login_stats["banned_ips"]),
                "locked_users_count": len(self.login_stats["locked_out_users"])
            },
            "success_rate": self.get_login_stats()["success_rate"],
            "average_login_duration": self.get_login_stats()["average_login_duration"]

    def _hash_password(self, password, salt):
        """使用PBKDF2算法对密码进行哈希"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            Config.PASSWORD_HASH_ITERATIONS
        ).hex()

    def __str__(self):
        return f"LoginAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()

# 创建全局登录AI实例
login_ai = LoginAI()
