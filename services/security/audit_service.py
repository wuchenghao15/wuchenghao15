#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS系统审计服务 提供操作审计和安全日志功能 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class AuditLog:
    """审计日志"""
    
    def __init__(self, log_id: str, action: str, resource_type: str,
                 resource_id: str, user_id: str = None, user_ip: str = None,
                 user_agent: str = None, before_state: Dict[str, Any] = None,
                 after_state: Dict[str, Any] = None, status: str = 'success',
                 error_message: str = None, created_at: str = None):
        self.log_id = log_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.user_id = user_id
        self.user_ip = user_ip
        self.user_agent = user_agent
        self.before_state = before_state or {}
        self.after_state = after_state or {}
        self.status = status
        self.error_message = error_message
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'log_id': self.log_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'user_ip': self.user_ip,
            'user_agent': self.user_agent,
            'before_state': self.before_state,
            'after_state': self.after_state,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at
        }

class AuditService:
    """审计服务"""
    
    def __init__(self):
        self.logs: Dict[str, AuditLog] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'audit_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'retention_days': 90,
            'max_logs_in_memory': 10000,
            'enable_real_time_monitoring': True,
            'alert_thresholds': {
                'failed_login_attempts': 5,
                'unauthorized_access': 3,
                'privilege_escalation': 1
            }
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'audit_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS audit_logs ( id INTEGER PRIMARY KEY AUTOINCREMENT, log_id TEXT NOT NULL UNIQUE, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, user_id TEXT, user_ip TEXT, user_agent TEXT, before_state TEXT, after_state TEXT, status TEXT DEFAULT 'success', error_message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS security_alerts ( id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT NOT NULL, severity TEXT DEFAULT 'medium', message TEXT NOT NULL, source_ip TEXT, user_id TEXT, action_taken TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, resolved_at TEXT, resolved_by TEXT ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS audit_rules ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_name TEXT NOT NULL UNIQUE, action TEXT, resource_type TEXT, severity TEXT DEFAULT 'medium', enabled INTEGER DEFAULT 1, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_audit_logs_id ON audit_logs(log_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_security_alerts_type ON security_alerts(alert_type) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[审计] 初始化数据库失败: {e}")
    
    def _generate_log_id(self) -> str:
        """生成日志ID"""
        return f"audit_{int(time.time())}_{hash(os.urandom(16))}"
    
    def log(self, action: str, resource_type: str, resource_id: str,
            user_id: str = None, user_ip: str = None, user_agent: str = None,
            before_state: Dict[str, Any] = None, after_state: Dict[str, Any] = None,
            status: str = 'success', error_message: str = None):
        """记录审计日志"""
        log_id = self._generate_log_id()
        
        log_entry = AuditLog(
            log_id=log_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent,
            before_state=before_state,
            after_state=after_state,
            status=status,
            error_message=error_message
        )
        
        with self.lock:
            self.logs[log_id] = log_entry
            
            if len(self.logs) > self.config['max_logs_in_memory']:
                oldest_log_id = min(self.logs.keys(), key=lambda k: self.logs[k].created_at)
                del self.logs[oldest_log_id]
        
        self._save_log_to_db(log_entry)
        self._check_security_rules(log_entry)
        
        logger(f"[审计] {action} {resource_type}/{resource_id} by {user_id or 'system'}")
    
    def _save_log_to_db(self, log_entry: AuditLog):
        """保存日志到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO audit_logs (log_id, action, resource_type, resource_id, user_id, user_ip, user_agent, before_state, after_state, status, error_message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                log_entry.log_id, log_entry.action, log_entry.resource_type,
                log_entry.resource_id, log_entry.user_id, log_entry.user_ip,
                log_entry.user_agent,
                json.dumps(log_entry.before_state),
                json.dumps(log_entry.after_state),
                log_entry.status, log_entry.error_message,
                log_entry.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[审计] 保存日志失败: {e}")
    
    def _check_security_rules(self, log_entry: AuditLog):
        """检查安全规则"""
        if log_entry.action == 'login' and log_entry.status == 'failed':
            self._check_failed_login(log_entry)
        
        if log_entry.action == 'access' and log_entry.status == 'failed':
            self._check_unauthorized_access(log_entry)
    
    def _check_failed_login(self, log_entry: AuditLog):
        """检查失败登录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT COUNT(*) FROM audit_logs WHERE action = 'login' AND status = 'failed' AND user_id = ? AND created_at >= ? ''', (log_entry.user_id, (datetime.now() - timedelta(minutes=5)).isoformat()))
            
            count = cursor.fetchone()[0]
            
            conn.close()
            
            if count >= self.config['alert_thresholds']['failed_login_attempts']:
                self._create_alert(
                    alert_type='failed_login',
                    severity='high',
                    message=f"多次登录失败: {count}次，用户: {log_entry.user_id}, IP: {log_entry.user_ip}",
                    source_ip=log_entry.user_ip,
                    user_id=log_entry.user_id
                )
        except Exception as e:
            logger(f"[审计] 检查失败登录失败: {e}")
    
    def _check_unauthorized_access(self, log_entry: AuditLog):
        """检查未授权访问"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT COUNT(*) FROM audit_logs WHERE action = 'access' AND status = 'failed' AND user_ip = ? AND created_at >= ? ''', (log_entry.user_ip, (datetime.now() - timedelta(minutes=10)).isoformat()))
            
            count = cursor.fetchone()[0]
            
            conn.close()
            
            if count >= self.config['alert_thresholds']['unauthorized_access']:
                self._create_alert(
                    alert_type='unauthorized_access',
                    severity='medium',
                    message=f"未授权访问尝试: {count}次，IP: {log_entry.user_ip}",
                    source_ip=log_entry.user_ip
                )
        except Exception as e:
            logger(f"[审计] 检查未授权访问失败: {e}")
    
    def _create_alert(self, alert_type: str, severity: str, message: str,
                      source_ip: str = None, user_id: str = None,
                      action_taken: str = None):
        """创建安全警报"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO security_alerts (alert_type, severity, message, source_ip, user_id, action_taken) VALUES (?, ?, ?, ?, ?, ?) ''', (alert_type, severity, message, source_ip, user_id, action_taken))
            
            conn.commit()
            conn.close()
            
            logger(f"[审计] 创建安全警报: {alert_type} - {message}")
            
            try:
                from notification_center import notification_center
                notification_center.send_alert_notification(
                    f"安全警报: {alert_type}",
                    message
                )
            except:
                pass
        except Exception as e:
            logger(f"[审计] 创建警报失败: {e}")
    
    def resolve_alert(self, alert_id: int, resolved_by: str = None):
        """解决警报"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' UPDATE security_alerts SET resolved_at = ?, resolved_by = ? WHERE id = ? ''', (datetime.now().isoformat(), resolved_by, alert_id))
            
            conn.commit()
            conn.close()
            
            logger(f"[审计] 解决警报: {alert_id}")
        except Exception as e:
            logger(f"[审计] 解决警报失败: {e}")
    
    def get_audit_logs(self, user_id: str = None, action: str = None,
                       resource_type: str = None, resource_id: str = None,
                       status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM audit_logs WHERE 1=1'
            params = []
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            if action:
                query += ' AND action = ?'
                params.append(action)
            if resource_type:
                query += ' AND resource_type = ?'
                params.append(resource_type)
            if resource_id:
                query += ' AND resource_id = ?'
                params.append(resource_id)
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            logs = []
            
            for row in cursor.fetchall():
                log_dict = dict(zip(columns, row))
                if log_dict.get('before_state'):
                    log_dict['before_state'] = json.loads(log_dict['before_state'])
                if log_dict.get('after_state'):
                    log_dict['after_state'] = json.loads(log_dict['after_state'])
                logs.append(log_dict)
            
            conn.close()
            return logs
        except Exception as e:
            logger(f"[审计] 获取审计日志失败: {e}")
            return []
    
    def get_security_alerts(self, alert_type: str = None, severity: str = None,
                           resolved: bool = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取安全警报"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM security_alerts WHERE 1=1'
            params = []
            
            if alert_type:
                query += ' AND alert_type = ?'
                params.append(alert_type)
            if severity:
                query += ' AND severity = ?'
                params.append(severity)
            if resolved is not None:
                if resolved:
                    query += ' AND resolved_at IS NOT NULL'
                else:
                    query += ' AND resolved_at IS NULL'
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            alerts = []
            
            for row in cursor.fetchall():
                alerts.append(dict(zip(columns, row)))
            
            conn.close()
            return alerts
        except Exception as e:
            logger(f"[审计] 获取安全警报失败: {e}")
            return []
    
    def get_audit_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取审计摘要"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            summary = {}
            
            cursor.execute('SELECT COUNT(*) FROM audit_logs WHERE created_at >= ?', (start_time,))
            summary['total_logs'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM audit_logs WHERE created_at >= ? AND status = "failed"', (start_time,))
            summary['failed_actions'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM security_alerts WHERE created_at >= ? AND resolved_at IS NULL',
            (start_time,))
            summary['active_alerts'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT action, COUNT(*) as count FROM audit_logs WHERE created_at >= ? GROUP BY action ORDER BY count DESC LIMIT 10',
            (start_time,))
            summary['top_actions'] = [dict(zip(['action', 'count'], row)) for row in cursor.fetchall()]
            
            cursor.execute('SELECT user_id, COUNT( *) as count FROM audit_logs WHERE created_at >= ? AND user_id IS NOT NULL GROUP BY user_id ORDER BY count DESC LIMIT 10', (start_time,))
            summary['top_users'] = [dict(zip(['user_id', 'count'], row)) for row in cursor.fetchall()]
            
            conn.close()
            
            return summary
        except Exception as e:
            logger(f"[审计] 获取审计摘要失败: {e}")
            return {}
    
    def cleanup_old_logs(self):
        """清理旧日志"""
        retention_days = self.config['retention_days']
        cutoff_time = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM audit_logs WHERE created_at < ?', (cutoff_time,))
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger(f"[审计] 清理旧日志: {deleted}条")
        except Exception as e:
            logger(f"[审计] 清理日志失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'retention_days': self.config['retention_days'],
            'max_logs_in_memory': self.config['max_logs_in_memory'],
            'enable_real_time_monitoring': self.config['enable_real_time_monitoring'],
            'alert_thresholds': self.config['alert_thresholds']
        }
    
    def start(self):
        """启动审计服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[审计] 系统审计服务已启动")
    
    def stop(self):
        """停止审计服务"""
        self.is_running = False
        self.cleanup_old_logs()
        logger(f"[审计] 系统审计服务已停止")

audit_service = AuditService()

def audit(action: str, resource_type: str):
    """装饰器：记录审计日志"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            user_ip = kwargs.get('user_ip')
            
            resource_id = kwargs.get('resource_id', 'unknown')
            
            before_state = {}
            
            try:
                result = func(*args, **kwargs)
                
                audit_service.log(
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(resource_id),
                    user_id=user_id,
                    user_ip=user_ip,
                    before_state=before_state,
                    after_state={'result': 'success'},
                    status='success'
                )
                
                return result
            except Exception as e:
                audit_service.log(
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(resource_id),
                    user_id=user_id,
                    user_ip=user_ip,
                    before_state=before_state,
                    after_state={'result': 'failed'},
                    status='failed',
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator
