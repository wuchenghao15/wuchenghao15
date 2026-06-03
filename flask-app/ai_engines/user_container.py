# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户容器 - 负责管理用户数据,保护用户隐私和保证系统状态
"""

import time
import threading
from typing import Dict, Any, Optional, List
from app.models.user import User
from app.utils.security import security_utils
from app.utils.logging import logger
from app.ai.user_ai_manager import user_ai_manager
import logging


class UserContainer:
    """用户容器类 - 负责管理用户数据,保护用户隐私和保证系统状态"""

    def __init__(self):
        self.container_id = f"user_container_{id(self)}"
        self.name = "用户容器"
        self.description = "负责管理用户数据,保护用户隐私和保证系统状态"

        self.config = {
            "enabled": True,
            "data_retention_period": 365 * 24 * 3600,
            "auto_cleanup_enabled": True,
            "ai_monitoring_enabled": True,
            "user_activity_logging": True,
            "privacy_protection_level": "high",
            "max_users": 1000
        }

        self.stats = {
            "total_users": 0,
            "active_users": 0,
            "users_by_role": {},
            "users_by_status": {},
            "user_growth": {
                "daily": {},
                "weekly": {},
                "monthly": {}
            },
            "last_updated": time.time()
        }

        self.user_activity_logs = []
        self.user_cache = {}
        self.cache_expiry = 300
        self.cache_hits = 0
        self.cache_misses = 0

        self.ai_monitoring = {
            "enabled": True,
            "check_interval": 300,
            "alert_threshold": {
                "failed_logins": 3,
                "privacy_violations": 1
            }
        }

        self.ai_monitoring_thread = None

        self._update_user_stats()

        logger.info(f"✓ 用户容器初始化成功: {self.container_id}")

    def _start_ai_monitoring(self):
        """启动AI监控线程"""
        if self.ai_monitoring["enabled"]:
            self.ai_monitoring_thread = threading.Thread(target=self._ai_monitoring_thread_func, daemon=True)
            self.ai_monitoring_thread.start()
            logger.info(f"✓ AI监控线程已启动")

    def _ai_monitoring_thread_func(self):
        """AI监控线程函数"""
        while True:
            time.sleep(self.ai_monitoring["check_interval"])
            self._monitor_user_activities()

    def _monitor_user_activities(self):
        """监控用户活动"""
        try:
            recent_logs = self._get_recent_activity_logs(300)

            unusual_activities = self._detect_unusual_activities(recent_logs)

            if unusual_activities:
                logger.warning(f"🔍 检测到异常用户活动: {len(unusual_activities)} 项")

                for activity in unusual_activities:
                    self._log_activity("unusual_activity", {
                        "username": activity["username"],
                        "activity_type": activity["type"],
                        "timestamp": activity["timestamp"],
                        "details": activity
                    })
        except Exception as e:
            logger.error(f"❌ AI监控出错: {str(e)}")

    def _detect_unusual_activities(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测异常用户活动"""
        unusual_activities = []

        user_activities = {}
        for log in logs:
            username = log.get("username", "unknown")
            if username not in user_activities:
                user_activities[username] = []
            user_activities[username].append(log)

        for username, activities in user_activities.items():
            if len(activities) > 10:
                unusual_activities.append({
                    "username": username,
                    "type": "high_activity_rate",
                    "timestamp": time.time(),
                    "details": {
                        "activity_count": len(activities),
                        "time_window": 300
                    }
                })

            activity_types = set(log.get("type", "") for log in activities)
            if "failed_login" in activity_types and "password_change" in activity_types:
                unusual_activities.append({
                    "username": username,
                    "type": "suspicious_activity_sequence",
                    "timestamp": time.time(),
                    "details": {
                        "activity_types": list(activity_types)
                    }
                })

        return unusual_activities

    def _update_user_stats(self):
        """更新用户统计"""
        try:
            users = User.get_all_users()
            total_users = len(users)

            users_by_role = {}
            for user in users:
                role = user.role
                users_by_role[role] = users_by_role.get(role, 0) + 1

            users_by_status = {
                "active": 0,
                "inactive": 0
            }

            for user in users:
                status = "active" if user.is_active else "inactive"
                users_by_status[status] += 1

            self.stats = {
                "total_users": total_users,
                "active_users": users_by_status["active"],
                "users_by_role": users_by_role,
                "users_by_status": users_by_status,
                "last_updated": time.time()
            }

            logger.info(f"✓ 用户统计已更新: 总用户数={total_users}, 活跃用户数={users_by_status['active']}")
        except Exception as e:
            logger.error(f"❌ 更新用户统计出错: {str(e)}")

    def _log_activity(self, activity_type: str, details: Dict[str, Any]):
        """记录用户活动"""
        if not self.config["user_activity_logging"]:
            return

        activity = {
            "activity_id": f"activity_{id(details)}_{int(time.time())}",
            "type": activity_type,
            "timestamp": time.time(),
            "container_id": self.container_id,
            "details": details
        }

        self.user_activity_logs.append(activity)

        if len(self.user_activity_logs) > 10000:
            self.user_activity_logs = self.user_activity_logs[-10000:]

    def _get_recent_activity_logs(self, time_window: int) -> List[Dict[str, Any]]:
        """获取最近一段时间内的活动日志"""
        current_time = time.time()
        return [log for log in self.user_activity_logs
                if current_time - log["timestamp"] <= time_window]

    def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            current_time = time.time()

            self.user_activity_logs = [log for log in self.user_activity_logs
                                       if current_time - log["timestamp"] <= self.config["data_retention_period"]]

            expired_users = []
            for username, cache_data in self.user_cache.items():
                if current_time - cache_data["timestamp"] > self.cache_expiry:
                    expired_users.append(username)

            for username in expired_users:
                if username in self.user_cache:
                    del self.user_cache[username]

            logger.info(f"✓ 数据清理完成: 清理了 {len(expired_users)} 个过期缓存项")
        except Exception as e:
            logger.error(f"❌ 清理过期数据出错: {str(e)}")

    def _get_user_from_cache(self, username: str) -> Optional[User]:
        """从缓存获取用户"""
        current_time = time.time()
        if username in self.user_cache:
            cache_data = self.user_cache[username]
            if current_time - cache_data["timestamp"] <= self.cache_expiry:
                self.cache_hits += 1
                return cache_data["user"]
        self.cache_misses += 1
        return None

    def _add_user_to_cache(self, user: User):
        """将用户添加到缓存"""
        self.user_cache[user.username] = {
            "user": user,
            "timestamp": time.time()
        }

    def get_user(self, username: str) -> Optional[User]:
        """获取用户"""
        try:
            user = self._get_user_from_cache(username)
            if user:
                logger.info(f"✅ 从缓存获取用户: {username}")
                return user

            user = User.get_by_username(username)
            if user:
                self._add_user_to_cache(user)
                return user

            return None
        except Exception as e:
            logger.error(f"❌ 获取用户出错: {str(e)}")
            return None

    def update_user_activity(self, username: str, activity_type: str, details: Dict[str, Any]):
        """更新用户活动"""
        try:
            self._log_activity(activity_type, {
                "username": username,
                "timestamp": time.time(),
                "details": details
            })

            user_ai_manager.update_user_activity(username, activity_type, details)
        except Exception as e:
            logger.error(f"❌ 更新用户活动出错: {str(e)}")

    def get_user_activity_logs(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户活动日志"""
        try:
            logs = self.user_activity_logs

            if username:
                logs = [log for log in logs if log.get("details", {}).get("username") == username]

            logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)

            return logs[:limit]
        except Exception as e:
            logger.error(f"❌ 获取用户活动日志出错: {str(e)}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """获取容器状态"""
        return {
            "status": "running",
            "container_id": self.container_id,
            "name": self.name,
            "stats": self.stats
        }


user_container = UserContainer()
