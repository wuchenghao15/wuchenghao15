#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常保护管理器 - 防止用户意外退出或非法用户异常破坏导致系统数据异常
包含：会话锁、异常检测、数据保护、自动恢复机制
"""

import threading
import time
import uuid
import signal
import traceback
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from functools import wraps

from app.utils.logging import logger


class ProtectionLevel(Enum):
    """保护级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    TERMINATED = "terminated"


@dataclass
class SessionLock:
    """会话锁信息"""
    lock_id: str
    session_id: str
    user_id: Optional[str]
    resource: str
    acquired_at: float
    expires_at: float
    protection_level: ProtectionLevel
    operations: List[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.operations is None:
            self.operations = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnomalyEvent:
    """异常事件"""
    event_id: str
    type: str
    severity: str
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    timestamp: float
    details: Dict
    action_taken: str = "none"


class ExceptionProtectionManager:
    """异常保护管理器"""
    
    def __init__(self):
        self._session_locks: Dict[str, SessionLock] = {}
        self._active_sessions: Dict[str, Dict] = {}
        self._anomaly_events: List[AnomalyEvent] = []
        self._lock = threading.RLock()
        self._monitor_thread = None
        self._running = False
        
        self._config = {
            "session_timeout": 3600,  # 会话超时时间(秒)
            "lock_timeout": 300,      # 锁超时时间(秒)
            "max_locks_per_session": 10,
            "anomaly_history_size": 1000,
            "suspicious_activity_threshold": 5,
            "rapid_request_threshold": 100,
            "rapid_request_window": 60,
        }
        
        self._user_activity: Dict[str, List[float]] = {}
        self._ip_activity: Dict[str, List[float]] = {}
        
        logger.info("异常保护管理器初始化完成")
    
    def _cleanup_expired_locks(self):
        """清理过期锁"""
        now = time.time()
        expired_locks = []
        
        with self._lock:
            for lock_id, lock_data in self._session_locks.items():
                if lock_data.expires_at < now:
                    expired_locks.append(lock_id)
            
            for lock_id in expired_locks:
                lock_data = self._session_locks.pop(lock_id)
                logger.warning(f"会话锁已过期并自动释放: {lock_id}, 资源: {lock_data.resource}")
    
    def _cleanup_inactive_sessions(self):
        """清理非活动会话"""
        now = time.time()
        inactive_sessions = []
        
        with self._lock:
            for session_id, session_data in self._active_sessions.items():
                last_activity = session_data.get('last_activity', 0)
                if now - last_activity > self._config["session_timeout"]:
                    inactive_sessions.append(session_id)
                    self._terminate_session(session_id, "timeout")
            
            for session_id in inactive_sessions:
                self._active_sessions.pop(session_id, None)
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                self._cleanup_expired_locks()
                self._cleanup_inactive_sessions()
                self._detect_anomalies()
                time.sleep(5)
            except Exception as e:
                logger.error(f"监控循环异常: {str(e)}")
    
    def start_monitor(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            daemon=True,
            name="ExceptionProtectionMonitor"
        )
        self._monitor_thread.start()
        logger.info("异常保护监控已启动")
    
    def stop_monitor(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("异常保护监控已停止")
    
    def _record_activity(self, user_id: Optional[str], ip_address: str):
        """记录用户活动"""
        now = time.time()
        
        if user_id:
            if user_id not in self._user_activity:
                self._user_activity[user_id] = []
            self._user_activity[user_id].append(now)
            # 保留最近100条记录
            if len(self._user_activity[user_id]) > 100:
                self._user_activity[user_id] = self._user_activity[user_id][-100:]
        
        if ip_address:
            if ip_address not in self._ip_activity:
                self._ip_activity[ip_address] = []
            self._ip_activity[ip_address].append(now)
            if len(self._ip_activity[ip_address]) > 100:
                self._ip_activity[ip_address] = self._ip_activity[ip_address][-100:]
    
    def _detect_anomalies(self):
        """检测异常行为"""
        now = time.time()
        
        # 检测快速请求异常
        for ip, timestamps in self._ip_activity.items():
            recent_requests = [t for t in timestamps if now - t < self._config["rapid_request_window"]]
            if len(recent_requests) > self._config["rapid_request_threshold"]:
                self._record_anomaly(
                    type="rapid_requests",
                    severity="high",
                    ip_address=ip,
                    details={
                        "request_count": len(recent_requests),
                        "window": self._config["rapid_request_window"],
                        "threshold": self._config["rapid_request_threshold"]
                    }
                )
        
        # 检测用户异常活动
        for user_id, timestamps in self._user_activity.items():
            if len(timestamps) > self._config["suspicious_activity_threshold"]:
                # 检查活动模式是否异常
                time_diff = timestamps[-1] - timestamps[0]
                if time_diff < 60 and len(timestamps) > 10:
                    self._record_anomaly(
                        type="suspicious_user_activity",
                        severity="medium",
                        user_id=user_id,
                        details={
                            "activity_count": len(timestamps),
                            "time_window": time_diff,
                            "pattern": "rapid_consecutive_actions"
                        }
                    )
    
    def _record_anomaly(self, type: str, severity: str, user_id: Optional[str] = None,
                       session_id: Optional[str] = None, ip_address: str = "unknown",
                       details: Dict = None):
        """记录异常事件"""
        event = AnomalyEvent(
            event_id=str(uuid.uuid4()),
            type=type,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            timestamp=time.time(),
            details=details or {}
        )
        
        with self._lock:
            self._anomaly_events.append(event)
            if len(self._anomaly_events) > self._config["anomaly_history_size"]:
                self._anomaly_events = self._anomaly_events[-self._config["anomaly_history_size"]:]
        
        logger.warning(f"检测到异常: {type}, 严重程度: {severity}, IP: {ip_address}")
        self._handle_anomaly(event)
    
    def _handle_anomaly(self, anomaly: AnomalyEvent):
        """处理异常事件"""
        if anomaly.severity == "high":
            # 高严重程度：立即采取措施
            if anomaly.type == "rapid_requests":
                self._apply_rate_limit(anomaly.ip_address)
                anomaly.action_taken = "rate_limit_applied"
        elif anomaly.severity == "medium":
            # 中严重程度：监控并警告
            anomaly.action_taken = "monitoring"
        else:
            anomaly.action_taken = "logged"
    
    def _apply_rate_limit(self, ip_address: str):
        """应用速率限制"""
        # 记录速率限制状态
        logger.info(f"为IP {ip_address} 应用速率限制")
        # 实际实现中可以调用防火墙系统
    
    def create_session(self, user_id: Optional[str] = None, ip_address: str = "unknown") -> str:
        """创建会话"""
        session_id = str(uuid.uuid4())
        
        with self._lock:
            self._active_sessions[session_id] = {
                'session_id': session_id,
                'user_id': user_id,
                'ip_address': ip_address,
                'status': SessionStatus.ACTIVE.value,
                'created_at': time.time(),
                'last_activity': time.time(),
                'locks_held': 0
            }
        
        self._record_activity(user_id, ip_address)
        logger.debug(f"创建会话: {session_id}, 用户: {user_id}, IP: {ip_address}")
        return session_id
    
    def update_session_activity(self, session_id: str):
        """更新会话活动"""
        with self._lock:
            session = self._active_sessions.get(session_id)
            if session:
                session['last_activity'] = time.time()
    
    def terminate_session(self, session_id: str, reason: str = "user_request"):
        """终止会话"""
        return self._terminate_session(session_id, reason)
    
    def _terminate_session(self, session_id: str, reason: str = "user_request"):
        """内部终止会话"""
        with self._lock:
            session = self._active_sessions.get(session_id)
            if not session:
                return False
            
            # 释放该会话持有的所有锁
            locks_to_release = []
            for lock_id, lock_data in self._session_locks.items():
                if lock_data.session_id == session_id:
                    locks_to_release.append(lock_id)
            
            for lock_id in locks_to_release:
                self._release_lock(lock_id, f"session_terminated: {reason}")
            
            session['status'] = SessionStatus.TERMINATED.value
            logger.info(f"会话已终止: {session_id}, 原因: {reason}")
        
        return True
    
    def acquire_session_lock(self, session_id: str, resource: str, 
                            protection_level: ProtectionLevel = ProtectionLevel.MEDIUM,
                            ttl: float = 300.0) -> Optional[str]:
        """获取会话锁"""
        with self._lock:
            # 检查会话是否存在
            session = self._active_sessions.get(session_id)
            if not session:
                logger.error(f"无法获取锁: 会话不存在 {session_id}")
                return None
            
            # 检查锁数量限制
            if session['locks_held'] >= self._config["max_locks_per_session"]:
                logger.error(f"无法获取锁: 会话锁数量已达上限 {session_id}")
                return None
            
            # 检查资源是否已被锁定
            for existing_lock in self._session_locks.values():
                if existing_lock.resource == resource and existing_lock.expires_at > time.time():
                    logger.warning(f"资源已被锁定: {resource}, 持有者: {existing_lock.session_id}")
                    return None
            
            # 创建锁
            lock_id = str(uuid.uuid4())
            now = time.time()
            new_lock = SessionLock(
                lock_id=lock_id,
                session_id=session_id,
                user_id=session.get('user_id'),
                resource=resource,
                acquired_at=now,
                expires_at=now + ttl,
                protection_level=protection_level
            )
            
            self._session_locks[lock_id] = new_lock
            session['locks_held'] += 1
            
            logger.debug(f"会话锁获取成功: {lock_id}, 资源: {resource}, 会话: {session_id}")
            return lock_id
    
    def release_session_lock(self, lock_id: str, reason: str = "user_request") -> bool:
        """释放会话锁"""
        return self._release_lock(lock_id, reason)
    
    def _release_lock(self, lock_id: str, reason: str = "user_request") -> bool:
        """内部释放锁"""
        with self._lock:
            lock_data = self._session_locks.get(lock_id)
            if not lock_data:
                return False
            
            # 更新会话锁计数
            session = self._active_sessions.get(lock_data.session_id)
            if session:
                session['locks_held'] = max(0, session['locks_held'] - 1)
            
            del self._session_locks[lock_id]
            logger.debug(f"会话锁已释放: {lock_id}, 资源: {lock_data.resource}, 原因: {reason}")
            return True
    
    def refresh_session_lock(self, lock_id: str, ttl: float = 300.0) -> bool:
        """刷新会话锁"""
        with self._lock:
            lock_data = self._session_locks.get(lock_id)
            if not lock_data:
                return False
            
            lock_data.expires_at = time.time() + ttl
            logger.debug(f"会话锁已刷新: {lock_id}, 新过期时间: {lock_data.expires_at}")
            return True
    
    def is_resource_locked(self, resource: str) -> bool:
        """检查资源是否被锁定"""
        now = time.time()
        with self._lock:
            for lock_data in self._session_locks.values():
                if lock_data.resource == resource and lock_data.expires_at > now:
                    return True
        return False
    
    def record_operation(self, session_id: str, operation: str, 
                        resource: str, success: bool, details: Dict = None):
        """记录操作"""
        with self._lock:
            lock_id = None
            for lid, lock_data in self._session_locks.items():
                if lock_data.session_id == session_id and lock_data.resource == resource:
                    lock_id = lid
                    break
            
            if lock_id:
                self._session_locks[lock_id].operations.append({
                    'operation': operation,
                    'success': success,
                    'timestamp': time.time(),
                    'details': details or {}
                })
        
        self.update_session_activity(session_id)
    
    def protect_operation(self, session_id: str, resource: str, 
                         operation_func: Callable, *args, **kwargs) -> Any:
        """保护操作 - 带锁执行"""
        lock_id = None
        result = None
        success = False
        
        try:
            # 获取锁
            lock_id = self.acquire_session_lock(session_id, resource)
            if not lock_id:
                raise RuntimeError(f"无法获取资源锁: {resource}")
            
            # 执行操作
            result = operation_func(*args, **kwargs)
            success = True
            
            return result
        except Exception as e:
            # 记录异常
            self._record_anomaly(
                type="operation_failure",
                severity="medium",
                session_id=session_id,
                details={
                    "resource": resource,
                    "operation": operation_func.__name__ if hasattr(operation_func, '__name__') else str(operation_func),
                    "error": str(e),
                    "traceback": traceback.format_exc()[:1000]
                }
            )
            raise
        finally:
            # 记录操作
            if session_id and resource:
                self.record_operation(session_id, 
                                     operation_func.__name__ if hasattr(operation_func, '__name__') else str(operation_func),
                                     resource, success)
            
            # 释放锁
            if lock_id:
                self.release_session_lock(lock_id, "operation_completed")
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """获取会话状态"""
        with self._lock:
            return self._active_sessions.get(session_id)
    
    def get_lock_status(self, lock_id: str) -> Optional[SessionLock]:
        """获取锁状态"""
        with self._lock:
            return self._session_locks.get(lock_id)
    
    def get_anomaly_events(self, limit: int = 50) -> List[AnomalyEvent]:
        """获取异常事件"""
        with self._lock:
            return list(reversed(self._anomaly_events[-limit:]))
    
    def get_protection_stats(self) -> Dict:
        """获取保护统计信息"""
        with self._lock:
            now = time.time()
            active_locks = sum(1 for l in self._session_locks.values() if l.expires_at > now)
            active_sessions = sum(1 for s in self._active_sessions.values() 
                                  if s['status'] == SessionStatus.ACTIVE.value)
            
            return {
                'active_sessions': active_sessions,
                'total_sessions': len(self._active_sessions),
                'active_locks': active_locks,
                'total_locks': len(self._session_locks),
                'anomaly_count': len(self._anomaly_events),
                'high_severity_anomalies': sum(1 for e in self._anomaly_events if e.severity == 'high'),
                'monitoring_active': self._running
            }


# 保护装饰器
def protected_operation(resource: str, protection_level: ProtectionLevel = ProtectionLevel.MEDIUM):
    """保护操作装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 获取会话ID（假设第一个参数或kwargs中包含session_id）
            session_id = kwargs.get('session_id')
            if not session_id and hasattr(self, 'session_id'):
                session_id = self.session_id
            
            if not session_id:
                # 如果没有会话ID，直接执行（用于不需要会话保护的场景）
                return func(self, *args, **kwargs)
            
            manager = exception_protection_manager
            return manager.protect_operation(session_id, resource, func, self, *args, **kwargs)
        return wrapper
    return decorator


# 创建全局实例
exception_protection_manager = ExceptionProtectionManager()


def init_exception_protection():
    """初始化异常保护系统"""
    logger.info("初始化异常保护系统...")
    exception_protection_manager.start_monitor()
    
    # 注册信号处理
    def handle_sigterm(signum, frame):
        logger.warning("收到终止信号，正在安全关闭...")
        exception_protection_manager.stop_monitor()
    
    def handle_sigint(signum, frame):
        logger.warning("收到中断信号，正在安全关闭...")
        exception_protection_manager.stop_monitor()
    
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigint)
    
    logger.info("异常保护系统初始化完成")
    return exception_protection_manager