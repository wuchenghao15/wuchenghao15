#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS通知中心服务 统一管理和分发系统通知 """

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class Notification:
    """通知"""
    
    def __init__(self, notification_id: str, title: str, content: str,
                 notification_type: str = 'info', priority: str = 'normal',
                 target_user_ids: List[str] = None, target_roles: List[str] = None,
                 is_read: bool = False, created_at: str = None):
        self.notification_id = notification_id
        self.title = title
        self.content = content
        self.notification_type = notification_type
        self.priority = priority
        self.target_user_ids = target_user_ids or []
        self.target_roles = target_roles or []
        self.is_read = is_read
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'notification_id': self.notification_id,
            'title': self.title,
            'content': self.content,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'target_user_ids': self.target_user_ids,
            'target_roles': self.target_roles,
            'is_read': self.is_read,
            'created_at': self.created_at
        }

class NotificationCenter:
    """通知中心"""
    
    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.pending_notifications: List[Dict[str, Any]] = []
        self.is_running = False
        self.dispatch_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'notification_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'dispatch_interval': 5,
            'max_notifications_per_user': 100,
            'retention_days': 30,
            'enable_email_notification': True,
            'enable_sms_notification': False,
            'enable_system_notification': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'notification_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS notifications ( id INTEGER PRIMARY KEY AUTOINCREMENT, notification_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL, content TEXT NOT NULL, notification_type TEXT DEFAULT 'info', priority TEXT DEFAULT 'normal', target_user_ids TEXT, target_roles TEXT, is_read INTEGER DEFAULT 0, read_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS user_notifications ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, notification_id TEXT NOT NULL, is_read INTEGER DEFAULT 0, read_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_notifications_id ON notifications(notification_id) ''')
            
            cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_user_notifications_user ON user_notifications(user_id) ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[通知] 初始化数据库失败: {e}")
    
    def _generate_notification_id(self) -> str:
        """生成通知ID"""
        return f"notif_{int(time.time())}_{hash(os.urandom(16))}"
    
    def add_notification(self, title: str, content: str,
                        notification_type: str = 'info', priority: str = 'normal',
                        target_user_ids: List[str] = None, target_roles: List[str] = None) -> str:
        """添加通知"""
        notification_id = self._generate_notification_id()
        
        notification = Notification(
            notification_id=notification_id,
            title=title,
            content=content,
            notification_type=notification_type,
            priority=priority,
            target_user_ids=target_user_ids or [],
            target_roles=target_roles or []
        )
        
        with self.lock:
            self.notifications[notification_id] = notification
        
        self._save_notification_to_db(notification)
        
        pending = {
            'notification_id': notification_id,
            'title': title,
            'content': content,
            'type': notification_type,
            'priority': priority,
            'target_user_ids': target_user_ids or [],
            'target_roles': target_roles or []
        }
        
        self.pending_notifications.append(pending)
        
        logger(f"[通知] 添加通知: {title}")
        return notification_id
    
    def _save_notification_to_db(self, notification: Notification):
        """保存通知到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO notifications (notification_id, title, content, notification_type, priority, target_user_ids, target_roles, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                notification.notification_id, notification.title, notification.content,
                notification.notification_type, notification.priority,
                json.dumps(notification.target_user_ids),
                json.dumps(notification.target_roles),
                1 if notification.is_read else 0,
                notification.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[通知] 保存通知失败: {e}")
    
    def _dispatch_loop(self):
        """分发循环"""
        while self.is_running:
            try:
                time.sleep(self.config['dispatch_interval'])
                
                if self.pending_notifications:
                    with self.lock:
                        notifications_to_dispatch = self.pending_notifications[:]
                        self.pending_notifications = []
                
                    for notification in notifications_to_dispatch:
                        self._dispatch_notification(notification)
            except Exception as e:
                logger(f"[通知] 分发循环错误: {e}")
    
    def _dispatch_notification(self, notification: Dict[str, Any]):
        """分发通知"""
        if self.config['enable_email_notification']:
            try:
                from email_service import email_service
                for user_id in notification.get('target_user_ids', []):
                    email_service.send_email(
                        to_email=f"{user_id}@mtscos.com",
                        subject=notification['title'],
                        content=notification['content'],
                        is_html=False
                    )
            except Exception as e:
                logger(f"[通知] 邮件通知失败: {e}")
        
        if self.config['enable_sms_notification']:
            try:
                from sms_service import sms_service
                for user_id in notification.get('target_user_ids', []):
                    sms_service.send_sms(
                        phone_number=f"13800138000",
                        message=f"{notification['title']}: {notification['content']}"
                    )
            except Exception as e:
                logger(f"[通知] 短信通知失败: {e}")
    
    def get_notifications(self, user_id: str = None, notification_type: str = None,
                         priority: str = None, is_read: bool = None,
                         limit: int = 50) -> List[Notification]:
        """获取通知列表"""
        result = []
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT notification_id, title, content, notification_type, priority, target_user_ids, target_roles, is_read, created_at FROM notifications WHERE 1=1'
            params = []
            
            if user_id:
                query += ' AND (target_user_ids LIKE ? OR target_roles LIKE ?)'
                params.append(f'%{user_id}%')
                params.append('%')
            
            if notification_type:
                query += ' AND notification_type = ?'
                params.append(notification_type)
            
            if priority:
                query += ' AND priority = ?'
                params.append(priority)
            
            if is_read is not None:
                query += ' AND is_read = ?'
                params.append(1 if is_read else 0)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                notification_id, title, content, notification_type, priority, target_user_ids, target_roles, is_read,
                created_at = row
                
                notification = Notification(
                    notification_id=notification_id,
                    title=title,
                    content=content,
                    notification_type=notification_type,
                    priority=priority,
                    target_user_ids=json.loads(target_user_ids) if target_user_ids else [],
                    target_roles=json.loads(target_roles) if target_roles else [],
                    is_read=bool(is_read),
                    created_at=created_at
                )
                
                result.append(notification)
            
            conn.close()
        except Exception as e:
            logger(f"[通知] 获取通知失败: {e}")
        
        return result
    
    def get_unread_count(self, user_id: str = None) -> int:
        """获取未读通知数量"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM notifications WHERE is_read = 0'
            params = []
            
            if user_id:
                query += ' AND (target_user_ids LIKE ? OR target_roles LIKE ?)'
                params.append(f'%{user_id}%')
                params.append('%')
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except Exception as e:
            logger(f"[通知] 获取未读数量失败: {e}")
            return 0
    
    def mark_as_read(self, notification_id: str):
        """标记通知为已读"""
        with self.lock:
            if notification_id in self.notifications:
                self.notifications[notification_id].is_read = True
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(''' UPDATE notifications SET is_read = 1, read_at = ? WHERE notification_id = ? ''', (datetime.now().isoformat(), notification_id))
            
            conn.commit()
            conn.close()
            
            logger(f"[通知] 标记已读: {notification_id}")
        except Exception as e:
            logger(f"[通知] 标记已读失败: {e}")
    
    def mark_all_as_read(self, user_id: str = None):
        """标记所有通知为已读"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'UPDATE notifications SET is_read = 1, read_at = ? WHERE is_read = 0'
            params = [datetime.now().isoformat()]
            
            if user_id:
                query += ' AND (target_user_ids LIKE ? OR target_roles LIKE ?)'
                params.append(f'%{user_id}%')
                params.append('%')
            
            cursor.execute(query, params)
            count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger(f"[通知] 标记所有已读: {count}条")
        except Exception as e:
            logger(f"[通知] 标记所有已读失败: {e}")
    
    def delete_notification(self, notification_id: str):
        """删除通知"""
        with self.lock:
            if notification_id in self.notifications:
                del self.notifications[notification_id]
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM notifications WHERE notification_id = ?', (notification_id,))
            
            conn.commit()
            conn.close()
            
            logger(f"[通知] 删除通知: {notification_id}")
        except Exception as e:
            logger(f"[通知] 删除通知失败: {e}")
    
    def _cleanup_expired_notifications(self):
        """清理过期通知"""
        retention_days = self.config['retention_days']
        cutoff_time = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM notifications WHERE created_at < ?', (cutoff_time,))
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger(f"[通知] 清理过期通知: {deleted}条")
        except Exception as e:
            logger(f"[通知] 清理通知失败: {e}")
    
    def send_system_notification(self, title: str, content: str):
        """发送系统通知"""
        self.add_notification(
            title=title,
            content=content,
            notification_type='system',
            priority='high',
            target_roles=['admin']
        )
    
    def send_alert_notification(self, title: str, content: str):
        """发送警报通知"""
        self.add_notification(
            title=title,
            content=content,
            notification_type='alert',
            priority='critical',
            target_roles=['admin']
        )
    
    def send_user_notification(self, user_id: str, title: str, content: str):
        """发送用户通知"""
        self.add_notification(
            title=title,
            content=content,
            notification_type='user',
            priority='normal',
            target_user_ids=[user_id]
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'pending_notifications': len(self.pending_notifications),
            'total_notifications': len(self.notifications),
            'dispatch_interval': self.config['dispatch_interval'],
            'enable_email_notification': self.config['enable_email_notification'],
            'enable_sms_notification': self.config['enable_sms_notification'],
            'enable_system_notification': self.config['enable_system_notification']
        }
    
    def start(self):
        """启动通知中心"""
        if self.is_running:
            return
        
        self.is_running = True
        self.dispatch_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.dispatch_thread.start()
        logger(f"[通知] 通知中心服务已启动")
    
    def stop(self):
        """停止通知中心"""
        self.is_running = False
        if self.dispatch_thread:
            self.dispatch_thread.join()
        
        self._cleanup_expired_notifications()
        logger(f"[通知] 通知中心服务已停止")

notification_center = NotificationCenter()



