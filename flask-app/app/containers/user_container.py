#!/usr/bin/env python3
"""
用户容器 - 负责管理用户数据、保护用户隐私和保证系统状态
"""

import time
import threading
from typing import Dict, Any, Optional, List
from app.models.user import User
from app.utils.security import security_utils
from app.utils.logging import logger
from app.ai.user_ai_manager import user_ai_manager


class UserContainer:
    """
    用户容器类，负责管理用户数据、保护用户隐私和保证系统状态
    """
    
    def __init__(self):
        self.container_id = f"user_container_{id(self)}"
        self.name = "用户容器"
        self.description = "负责管理用户数据、保护用户隐私和保证系统状态"
        
        # 用户配置
        self.config = {
            "enabled": True,
            "data_retention_period": 365 * 24 * 3600,  # 用户数据保留1年
            "auto_cleanup_enabled": True,
            "ai_monitoring_enabled": True,
            "user_activity_logging": True,
            "privacy_protection_level": "high",  # 隐私保护级别: low, medium, high
            "max_users": 1000  # 最大用户数量
        }
        
        # 用户统计
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
        
        # 用户活动日志
        self.user_activity_logs = []
        
        # 用户数据缓存
        self.user_cache = {}
        self.cache_expiry = 300  # 缓存过期时间（秒）
        self.cache_hits = 0
        self.cache_misses = 0
        
        # AI员工监控配置
        self.ai_monitoring = {
            "enabled": True,
            "check_interval": 300,  # 每5分钟检查一次
            "alert_threshold": {
                "unusual_activity": 5,  # 异常活动阈值
                "failed_logins": 3,  # 登录失败阈值
                "privacy_violations": 1  # 隐私违规阈值
            }
        }
        
        # 初始化AI监控
        self.ai_monitoring_thread = None
        self._start_ai_monitoring()
        
        # 初始化用户统计
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
            # 获取最近的用户活动日志
            recent_logs = self._get_recent_activity_logs(300)  # 最近5分钟的日志
            
            # 分析用户活动
            unusual_activities = self._detect_unusual_activities(recent_logs)
            
            if unusual_activities:
                # 通知AI员工
                logger.warning(f"🔍 检测到异常用户活动: {len(unusual_activities)} 项")
                # 这里可以添加AI员工通知逻辑
                
                # 记录异常活动
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
        
        # 统计每个用户的活动
        user_activities = {}
        for log in logs:
            username = log.get("username", "unknown")
            if username not in user_activities:
                user_activities[username] = []
            user_activities[username].append(log)
        
        # 检测异常活动模式
        for username, activities in user_activities.items():
            # 检查短时间内的活动频率
            if len(activities) > 10:  # 5分钟内超过10次活动
                unusual_activities.append({
                    "username": username,
                    "type": "high_activity_rate",
                    "timestamp": time.time(),
                    "details": {
                        "activity_count": len(activities),
                        "time_window": 300
                    }
                })
            
            # 检查异常的活动类型组合
            activity_types = [a["type"] for a in activities]
            if "failed_login" in activity_types and "password_change" in activity_types:
                unusual_activities.append({
                    "username": username,
                    "type": "suspicious_activity_sequence",
                    "timestamp": time.time(),
                    "details": {
                        "activity_types": activity_types
                    }
                })
        
        return unusual_activities
    
    def _update_user_stats(self):
        """更新用户统计信息"""
        try:
            # 获取所有用户
            users = User.get_all_users()
            total_users = len(users)
            
            # 按角色统计
            users_by_role = {}
            for user in users:
                role = user.role
                users_by_role[role] = users_by_role.get(role, 0) + 1
            
            # 按状态统计
            users_by_status = {
                "active": 0,
                "inactive": 0
            }
            for user in users:
                status = "active" if user.is_active else "inactive"
                users_by_status[status] += 1
            
            # 更新统计数据
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
        
        # 限制日志数量
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
            
            # 清理过期的用户活动日志
            self.user_activity_logs = [log for log in self.user_activity_logs 
                                     if current_time - log["timestamp"] <= self.config["data_retention_period"]]
            
            # 清理过期的缓存
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
            else:
                # 缓存过期，移除
                del self.user_cache[username]
                self.cache_misses += 1
                return None
        else:
            self.cache_misses += 1
            return None
    
    def _add_user_to_cache(self, user: User):
        """将用户添加到缓存"""
        self.user_cache[user.username] = {
            "user": user,
            "timestamp": time.time()
        }
    
    def get_user(self, username: str) -> Optional[User]:
        """获取用户信息"""
        try:
            # 从缓存获取用户
            user = self._get_user_from_cache(username)
            if user:
                logger.info(f"✅ 从缓存获取用户: {username}")
                return user
            
            # 从数据库获取用户
            user = User.get_by_username(username)
            if user:
                logger.info(f"✅ 从数据库获取用户: {username}")
                # 添加到缓存
                self._add_user_to_cache(user)
                return user
            else:
                logger.warning(f"❌ 用户不存在: {username}")
                return None
        except Exception as e:
            logger.error(f"❌ 获取用户出错: {str(e)}")
            return None
    
    def get_all_users(self) -> List[User]:
        """获取所有用户"""
        try:
            users = User.get_all_users()
            logger.info(f"✅ 获取所有用户: 共 {len(users)} 个")
            
            # 更新用户缓存
            for user in users:
                self._add_user_to_cache(user)
            
            return users
        except Exception as e:
            logger.error(f"❌ 获取所有用户出错: {str(e)}")
            return []
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新用户"""
        try:
            logger.info(f"🔧 创建用户: {user_data.get('username')}")
            
            # 检查用户容器是否启用
            if not self.config["enabled"]:
                return {
                    "success": False,
                    "message": "用户容器已禁用",
                    "container_status": "disabled"
                }
            
            # 检查最大用户数量限制
            if self.stats["total_users"] >= self.config["max_users"]:
                return {
                    "success": False,
                    "message": f"已达到最大用户数量限制: {self.config['max_users']}",
                    "reason": "max_users_reached"
                }
            
            # 检查用户名是否已存在
            existing_user = User.get_by_username(user_data["username"])
            if existing_user:
                return {
                    "success": False,
                    "message": "用户名已存在",
                    "reason": "username_exists"
                }
            
            # 创建用户对象
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password=security_utils.hash_password(user_data["password"]),
                role=user_data.get("role", "user"),
                is_active=user_data.get("is_active", True)
            )
            
            # 保存用户
            user.save()
            
            # 更新用户统计
            self._update_user_stats()
            
            # 添加到缓存
            self._add_user_to_cache(user)
            
            # 记录活动
            self._log_activity("user_created", {
                "username": user.username,
                "email": user.email,
                "role": user.role
            })
            
            logger.info(f"✅ 用户创建成功: {user.username}")
            
            return {
                "success": True,
                "message": "用户创建成功",
                "user_id": user.user_id,
                "username": user.username,
                "container_id": self.container_id
            }
        except Exception as e:
            logger.error(f"❌ 创建用户出错: {str(e)}")
            return {
                "success": False,
                "message": f"创建用户失败: {str(e)}",
                "error": str(e)
            }
    
    def update_user(self, username: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息"""
        try:
            logger.info(f"🔧 更新用户: {username}")
            
            # 获取用户
            user = self.get_user(username)
            if not user:
                return {
                    "success": False,
                    "message": "用户不存在",
                    "reason": "user_not_found"
                }
            
            # 更新用户信息
            if "email" in user_data:
                user.email = user_data["email"]
            if "password" in user_data:
                user.password = security_utils.hash_password(user_data["password"])
            if "role" in user_data:
                user.role = user_data["role"]
            if "is_active" in user_data:
                user.is_active = user_data["is_active"]
            
            # 保存用户
            user.save()
            
            # 更新用户缓存
            self._add_user_to_cache(user)
            
            # 更新用户统计
            self._update_user_stats()
            
            # 记录活动
            self._log_activity("user_updated", {
                "username": user.username,
                "updated_fields": list(user_data.keys())
            })
            
            logger.info(f"✅ 用户更新成功: {username}")
            
            return {
                "success": True,
                "message": "用户更新成功",
                "user_id": user.user_id,
                "username": user.username,
                "container_id": self.container_id
            }
        except Exception as e:
            logger.error(f"❌ 更新用户出错: {str(e)}")
            return {
                "success": False,
                "message": f"更新用户失败: {str(e)}",
                "error": str(e)
            }
    
    def delete_user(self, username: str) -> Dict[str, Any]:
        """删除用户"""
        try:
            logger.info(f"🔧 删除用户: {username}")
            
            # 获取用户
            user = self.get_user(username)
            if not user:
                return {
                    "success": False,
                    "message": "用户不存在",
                    "reason": "user_not_found"
                }
            
            # 删除用户
            user.delete()
            
            # 从缓存中移除
            if username in self.user_cache:
                del self.user_cache[username]
            
            # 更新用户统计
            self._update_user_stats()
            
            # 记录活动
            self._log_activity("user_deleted", {
                "username": username,
                "user_id": user.user_id
            })
            
            logger.info(f"✅ 用户删除成功: {username}")
            
            return {
                "success": True,
                "message": "用户删除成功",
                "username": username,
                "container_id": self.container_id
            }
        except Exception as e:
            logger.error(f"❌ 删除用户出错: {str(e)}")
            return {
                "success": False,
                "message": f"删除用户失败: {str(e)}",
                "error": str(e)
            }
    
    def update_user_activity(self, username: str, activity_type: str, details: Dict[str, Any]):
        """更新用户活动"""
        try:
            # 记录用户活动
            self._log_activity(activity_type, {
                "username": username,
                "timestamp": time.time(),
                "details": details
            })
            
            # 通知AI管理器
            if self.config["ai_monitoring_enabled"]:
                user_ai_manager.update_user_activity(username, activity_type, details)
        except Exception as e:
            logger.error(f"❌ 更新用户活动出错: {str(e)}")
    
    def get_user_activity_logs(self, username: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户活动日志"""
        try:
            logs = self.user_activity_logs
            
            # 按用户名过滤
            if username:
                logs = [log for log in logs if log["details"].get("username") == username]
            
            # 按时间倒序排序
            logs.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # 限制返回数量
            return logs[:limit]
        except Exception as e:
            logger.error(f"❌ 获取用户活动日志出错: {str(e)}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取用户容器状态"""
        return {
            "container_id": self.container_id,
            "name": self.name,
            "description": self.description,
            "status": "running" if self.config["enabled"] else "disabled",
            "config": self.config,
            "stats": self.stats,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": round(self.cache_hits / (self.cache_hits + self.cache_misses + 1) * 100, 2)  # 避免除以0
            },
            "ai_monitoring": self.ai_monitoring,
            "active_logs": len(self.user_activity_logs),
            "last_updated": time.time()
        }
    
    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户容器配置"""
        try:
            self.config.update(config_updates)
            logger.info(f"✅ 用户容器配置已更新: {config_updates}")
            
            # 如果AI监控配置改变，重启监控线程
            if "enabled" in config_updates and config_updates["enabled"] != self.ai_monitoring["enabled"]:
                self.ai_monitoring["enabled"] = config_updates["enabled"]
                if self.ai_monitoring_thread:
                    self.ai_monitoring_thread = None
                self._start_ai_monitoring()
            
            return {
                "success": True,
                "message": "配置更新成功",
                "config": self.config
            }
        except Exception as e:
            logger.error(f"❌ 更新配置出错: {str(e)}")
            return {
                "success": False,
                "message": "配置更新失败",
                "error": str(e)
            }
    
    def reset_container(self) -> Dict[str, Any]:
        """重置用户容器状态"""
        try:
            # 重置缓存
            self.user_cache = {}
            self.cache_hits = 0
            self.cache_misses = 0
            
            # 清理活动日志
            self.user_activity_logs = []
            
            # 重置统计数据
            self._update_user_stats()
            
            logger.info(f"✅ 用户容器已重置: {self.container_id}")
            return {
                "success": True,
                "message": "用户容器已重置"
            }
        except Exception as e:
            logger.error(f"❌ 重置容器出错: {str(e)}")
            return {
                "success": False,
                "message": "重置失败",
                "error": str(e)
            }
    
    def backup_user_data(self) -> Dict[str, Any]:
        """备份用户数据"""
        try:
            # 这里可以添加用户数据备份逻辑
            # 例如：将用户数据导出为JSON或SQL文件
            
            users = User.get_all_users()
            backup_data = {
                "backup_id": f"backup_{int(time.time())}",
                "timestamp": time.time(),
                "container_id": self.container_id,
                "total_users": len(users),
                "users": [{
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                } for user in users]
            }
            
            logger.info(f"✅ 用户数据备份成功: 共 {len(users)} 个用户")
            
            return {
                "success": True,
                "message": "用户数据备份成功",
                "backup_id": backup_data["backup_id"],
                "backup_size": len(str(backup_data)),
                "total_users": len(users),
                "container_id": self.container_id
            }
        except Exception as e:
            logger.error(f"❌ 备份用户数据出错: {str(e)}")
            return {
                "success": False,
                "message": f"备份用户数据失败: {str(e)}",
                "error": str(e)
            }


# 导出默认用户容器实例
user_container = UserContainer()
