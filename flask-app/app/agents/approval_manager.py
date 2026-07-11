# -*- coding: utf-8 -*-
"""
人机协同审批系统 - 操作安全护栏
支持：操作等级定义、审批流程、审批记录持久化、自动暂停机制
"""
import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class OperationLevel(Enum):
    NORMAL = 'normal'
    IMPORTANT = 'important'
    CRITICAL = 'critical'
    DANGEROUS = 'dangerous'


class ApprovalStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    EXPIRED = 'expired'


class ApprovalManager:
    """审批管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self._approvals: Dict[str, Dict] = {}
        self._pending_approvals: List[str] = []
        self._auto_paused = False
        self._pause_reason = ''
        self._admin_notifications = []
        
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        
        self._level_config = {
            OperationLevel.NORMAL.value: {
                'require_approval': False,
                'auto_execute': True,
                'approval_timeout': 0,
                'description': '普通操作，可自动执行'
            },
            OperationLevel.IMPORTANT.value: {
                'require_approval': True,
                'auto_execute': False,
                'approval_timeout': 3600,
                'description': '重要操作，需审批'
            },
            OperationLevel.CRITICAL.value: {
                'require_approval': True,
                'auto_execute': False,
                'approval_timeout': 1800,
                'description': '重大操作，需快速审批'
            },
            OperationLevel.DANGEROUS.value: {
                'require_approval': True,
                'auto_execute': False,
                'approval_timeout': 900,
                'description': '危险操作，需紧急审批'
            }
        }
        
        self._init_database()
        self._load_approvals()
        
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    operation_level TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    requester TEXT DEFAULT 'system',
                    approver TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    details TEXT DEFAULT '{}',
                    created_at TEXT,
                    approved_at TEXT,
                    rejected_at TEXT,
                    expires_at TEXT,
                    executed_at TEXT,
                    execution_result TEXT DEFAULT '',
                    audit_log TEXT DEFAULT ''
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_id TEXT,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    read_by TEXT DEFAULT '[]',
                    FOREIGN KEY (approval_id) REFERENCES approvals (approval_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_id TEXT,
                    operation_type TEXT NOT NULL,
                    operation_level TEXT NOT NULL,
                    operator TEXT DEFAULT 'system',
                    status TEXT NOT NULL,
                    details TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (approval_id) REFERENCES approvals (approval_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[审批系统] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[审批系统] 初始化数据库失败: {e}")
    
    def _load_approvals(self):
        """加载审批记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM approvals ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            for row in rows:
                approval = {
                    'approval_id': row[0],
                    'operation_type': row[1],
                    'operation_level': row[2],
                    'status': row[3],
                    'requester': row[4],
                    'approver': row[5],
                    'description': row[6],
                    'details': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8],
                    'approved_at': row[9],
                    'rejected_at': row[10],
                    'expires_at': row[11],
                    'executed_at': row[12],
                    'execution_result': row[13],
                    'audit_log': row[14]
                }
                self._approvals[row[0]] = approval
                
                if row[3] == ApprovalStatus.PENDING.value:
                    self._pending_approvals.append(row[0])
            
            conn.close()
            logger.info(f"[审批系统] 已加载 {len(self._approvals)} 条审批记录")
        except Exception as e:
            logger.error(f"[审批系统] 加载审批记录失败: {e}")
    
    def create_approval(self, operation_type: str, operation_level: str,
                       description: str = '', details: Dict = None) -> str:
        """创建审批请求"""
        approval_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        config = self._level_config.get(operation_level, self._level_config['normal'])
        expires_at = None
        if config['approval_timeout'] > 0:
            expires_at = (datetime.now() + 
                         timedelta(seconds=config['approval_timeout'])).isoformat()
        
        approval = {
            'approval_id': approval_id,
            'operation_type': operation_type,
            'operation_level': operation_level,
            'status': ApprovalStatus.PENDING.value,
            'requester': 'system',
            'approver': '',
            'description': description,
            'details': details or {},
            'created_at': datetime.now().isoformat(),
            'approved_at': None,
            'rejected_at': None,
            'expires_at': expires_at,
            'executed_at': None,
            'execution_result': '',
            'audit_log': f"审批创建于 {datetime.now().isoformat()}"
        }
        
        with self._lock:
            self._approvals[approval_id] = approval
            self._pending_approvals.append(approval_id)
            self._save_approval(approval)
        
        if config['require_approval']:
            self._notify_admins(approval_id, operation_level, description)
            logger.info(f"[审批系统] 创建审批请求: {approval_id} ({operation_level}) - {description}")
        
        return approval_id
    
    def _save_approval(self, approval: Dict):
        """保存审批记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                approval['approval_id'],
                approval['operation_type'],
                approval['operation_level'],
                approval['status'],
                approval['requester'],
                approval['approver'],
                approval['description'],
                json.dumps(approval['details']),
                approval['created_at'],
                approval['approved_at'],
                approval['rejected_at'],
                approval['expires_at'],
                approval['executed_at'],
                approval['execution_result'],
                approval['audit_log']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[审批系统] 保存审批记录失败: {e}")
    
    def _notify_admins(self, approval_id: str, level: str, description: str):
        """通知管理员（私有方法）"""
        level_map = {
            'normal': 'info',
            'important': 'warning',
            'critical': 'error',
            'dangerous': 'critical'
        }
        
        notification = {
            'notification_id': None,
            'approval_id': approval_id,
            'level': level_map.get(level, 'info'),
            'title': f'审批请求: {level.upper()}',
            'message': description,
            'timestamp': datetime.now().isoformat(),
            'read_by': []
        }
        
        self._admin_notifications.append(notification)
        
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_notifications (approval_id, level, title, message, timestamp, read_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                approval_id,
                notification['level'],
                notification['title'],
                notification['message'],
                notification['timestamp'],
                json.dumps([])
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[审批系统] 保存通知失败: {e}")
        
        logger.warning(f"[审批系统] 已推送审批通知给管理员: {level} - {description}")
    
    def notify_admins(self, approval_id: str, level: str, description: str):
        """通知管理员（公开方法，兼容外部调用）"""
        self._notify_admins(approval_id, level, description)
    
    def approve(self, approval_id: str, approver: str = 'admin') -> bool:
        """审批通过"""
        with self._lock:
            approval = self._approvals.get(approval_id)
            if not approval:
                logger.error(f"[审批系统] 审批请求不存在: {approval_id}")
                return False
            
            if approval['status'] != ApprovalStatus.PENDING.value:
                logger.error(f"[审批系统] 审批状态不正确: {approval['status']}")
                return False
            
            approval['status'] = ApprovalStatus.APPROVED.value
            approval['approver'] = approver
            approval['approved_at'] = datetime.now().isoformat()
            approval['audit_log'] += f"\n审批通过于 {datetime.now().isoformat()} by {approver}"
            
            if approval_id in self._pending_approvals:
                self._pending_approvals.remove(approval_id)
            
            self._save_approval(approval)
        
        logger.info(f"[审批系统] 审批通过: {approval_id} by {approver}")
        return True
    
    def reject(self, approval_id: str, approver: str = 'admin', reason: str = '') -> bool:
        """拒绝审批"""
        with self._lock:
            approval = self._approvals.get(approval_id)
            if not approval:
                return False
            
            if approval['status'] != ApprovalStatus.PENDING.value:
                return False
            
            approval['status'] = ApprovalStatus.REJECTED.value
            approval['approver'] = approver
            approval['rejected_at'] = datetime.now().isoformat()
            approval['audit_log'] += f"\n审批拒绝于 {datetime.now().isoformat()} by {approver}: {reason}"
            
            if approval_id in self._pending_approvals:
                self._pending_approvals.remove(approval_id)
            
            self._save_approval(approval)
        
        logger.info(f"[审批系统] 审批拒绝: {approval_id} by {approver} - {reason}")
        return True
    
    def check_approval(self, approval_id: str) -> str:
        """检查审批状态"""
        approval = self._approvals.get(approval_id)
        if not approval:
            return 'not_found'
        
        if approval['status'] == ApprovalStatus.EXPIRED.value:
            return 'expired'
        
        if approval['expires_at'] and datetime.now().isoformat() > approval['expires_at']:
            approval['status'] = ApprovalStatus.EXPIRED.value
            self._save_approval(approval)
            return 'expired'
        
        return approval['status']
    
    def is_auto_paused(self) -> bool:
        """检查是否自动暂停"""
        return self._auto_paused
    
    def pause_auto_operations(self, reason: str = ''):
        """暂停所有自动操作"""
        self._auto_paused = True
        self._pause_reason = reason
        logger.warning(f"[审批系统] 自动操作已暂停: {reason}")
        
        self._notify_admins(None, 'dangerous', f'系统自动暂停: {reason}')
    
    def resume_auto_operations(self):
        """恢复自动操作"""
        self._auto_paused = False
        self._pause_reason = ''
        logger.info("[审批系统] 自动操作已恢复")
    
    def log_operation(self, approval_id: str, operation_type: str, 
                     operation_level: str, status: str, details: Dict = None):
        """记录操作日志"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO operation_logs (approval_id, operation_type, operation_level, 
                    operator, status, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                approval_id,
                operation_type,
                operation_level,
                'system',
                status,
                json.dumps(details or {}),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"[审批系统] 操作日志已记录: {operation_type} {status}")
        except Exception as e:
            logger.error(f"[审批系统] 记录操作日志失败: {e}")
    
    def get_pending_approvals(self) -> List[Dict]:
        """获取待审批列表"""
        return [self._approvals.get(aid) for aid in self._pending_approvals]
    
    def get_approval(self, approval_id: str) -> Optional[Dict]:
        """获取审批详情"""
        return self._approvals.get(approval_id)
    
    def get_all_approvals(self) -> List[Dict]:
        """获取所有审批记录"""
        return sorted(self._approvals.values(), key=lambda x: x['created_at'], reverse=True)
    
    def get_approvals(self) -> List[Dict]:
        """获取所有审批记录（兼容API调用）"""
        return self.get_all_approvals()
    
    def get_notifications(self) -> List[Dict]:
        """获取通知列表"""
        return self._admin_notifications
    
    def get_level_config(self, level: str) -> Dict:
        """获取操作等级配置"""
        return self._level_config.get(level, self._level_config['normal'])


def get_approval_manager() -> ApprovalManager:
    """获取审批管理器单例"""
    return ApprovalManager()


def init_approval_system():
    """初始化审批系统"""
    manager = get_approval_manager()
    logger.info("[审批系统] 人机协同审批系统初始化完成")
    return manager