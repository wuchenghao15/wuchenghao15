# -*- coding: utf-8 -*-
"""
通知消息服务
提供系统通知、消息推送、通知管理等功能
"""

import logging
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class NotificationService:
    """通知消息服务"""

    _instance = None

    def __new__(cls, db_path: str = None):
        if not cls._instance:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )
        self._init_tables()
        logger.info("通知消息服务初始化完成")

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL DEFAULT 'info',
                title TEXT NOT NULL,
                content TEXT,
                category TEXT,
                icon TEXT,
                link TEXT,
                is_read INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 0,
                sender_id INTEGER,
                sender_name TEXT,
                extra_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_settings (
                user_id INTEGER PRIMARY KEY,
                system_enabled INTEGER DEFAULT 1,
                exam_enabled INTEGER DEFAULT 1,
                message_enabled INTEGER DEFAULT 1,
                email_enabled INTEGER DEFAULT 0,
                sound_enabled INTEGER DEFAULT 1,
                push_enabled INTEGER DEFAULT 0,
                quiet_start TEXT DEFAULT '22:00',
                quiet_end TEXT DEFAULT '07:00',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_notifications_user ON user_notifications(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_notifications_read ON user_notifications(is_read)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_receiver ON user_messages(receiver_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON user_messages(sender_id)')

            conn.commit()

    def send_notification(self, user_id: int, title: str, content: str = None,
                          notification_type: str = 'info', category: str = None,
                          icon: str = None, link: str = None, priority: int = 0,
                          sender_id: int = None, sender_name: str = None,
                          extra_data: Dict = None) -> int:
        """发送通知"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            extra_json = json.dumps(extra_data) if extra_data else None

            cursor.execute(
                '''INSERT INTO user_notifications 
                   (user_id, type, title, content, category, icon, link, priority, 
                    sender_id, sender_name, extra_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, notification_type, title, content, category, icon, link,
                 priority, sender_id, sender_name, extra_json)
            )
            conn.commit()
            notification_id = cursor.lastrowid
            logger.info(f"发送通知: 用户={user_id}, 标题={title}")
            return notification_id

    def send_bulk_notification(self, user_ids: List[int], title: str, content: str = None,
                               notification_type: str = 'info', **kwargs) -> int:
        """批量发送通知"""
        count = 0
        for user_id in user_ids:
            self.send_notification(user_id, title, content, notification_type, **kwargs)
            count += 1
        return count

    def get_notifications(self, user_id: int, limit: int = 50,
                          is_read: bool = None,
                          notification_type: str = None,
                          category: str = None) -> List[Dict]:
        """获取通知列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM user_notifications WHERE user_id = ?'
            params = [user_id]

            if is_read is not None:
                query += ' AND is_read = ?'
                params.append(1 if is_read else 0)

            if notification_type:
                query += ' AND type = ?'
                params.append(notification_type)

            if category:
                query += ' AND category = ?'
                params.append(category)

            query += ' ORDER BY priority DESC, created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            user_notifications = []
            for row in cursor.fetchall():
                n = dict(row)
                if n.get('extra_data'):
                    try:
                        n['extra_data'] = json.loads(n['extra_data'])
                    except Exception:
                        pass
                user_notifications.append(n)
            return user_notifications

    def get_unread_count(self, user_id: int, notification_type: str = None) -> int:
        """获取未读通知数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT COUNT(*) as count FROM user_notifications WHERE user_id = ? AND is_read = 0'
            params = [user_id]

            if notification_type:
                query += ' AND type = ?'
                params.append(notification_type)

            cursor.execute(query, params)
            return cursor.fetchone()['count']

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE user_notifications SET is_read = 1, read_at = ? 
                   WHERE id = ? AND user_id = ?''',
                (datetime.now().isoformat(), notification_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def mark_all_as_read(self, user_id: int) -> int:
        """标记所有通知为已读"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE user_notifications SET is_read = 1, read_at = ? 
                   WHERE user_id = ? AND is_read = 0''',
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
            return cursor.rowcount

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """删除通知"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM user_notifications WHERE id = ? AND user_id = ?',
                (notification_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear_all(self, user_id: int) -> int:
        """清空所有通知"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_notifications WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount

    def get_settings(self, user_id: int) -> Dict:
        """获取通知设置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM notification_settings WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)

            cursor.execute(
                'INSERT INTO notification_settings (user_id) VALUES (?)',
                (user_id,)
            )
            conn.commit()
            return {
                'user_id': user_id,
                'system_enabled': 1,
                'exam_enabled': 1,
                'message_enabled': 1,
                'email_enabled': 0,
                'sound_enabled': 1,
                'push_enabled': 0,
                'quiet_start': '22:00',
                'quiet_end': '07:00'
            }

    def update_settings(self, user_id: int, settings: Dict) -> Dict:
        """更新通知设置"""
        allowed_fields = [
            'system_enabled', 'exam_enabled', 'message_enabled',
            'email_enabled', 'sound_enabled', 'push_enabled',
            'quiet_start', 'quiet_end'
        ]

        fields_to_update = {}
        for field in allowed_fields:
            if field in settings:
                fields_to_update[field] = settings[field]

        if not fields_to_update:
            return self.get_settings(user_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT user_id FROM notification_settings WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()

            if exists:
                set_clause = ', '.join([f'{k} = ?' for k in fields_to_update.keys()])
                values = list(fields_to_update.values()) + [datetime.now().isoformat(), user_id]
                cursor.execute(
                    f'UPDATE notification_settings SET {set_clause}, updated_at = ? WHERE user_id = ?',
                    values
                )
            else:
                fields = list(fields_to_update.keys()) + ['user_id']
                placeholders = ', '.join(['?' for _ in fields])
                values = list(fields_to_update.values()) + [user_id]
                cursor.execute(
                    f'INSERT INTO notification_settings ({", ".join(fields)}) VALUES ({placeholders})',
                    values
                )

            conn.commit()

        return self.get_settings(user_id)

    def send_message(self, sender_id: int, receiver_id: int, title: str,
                    content: str, parent_id: int = None) -> int:
        """发送私信"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO user_messages 
                   (sender_id, receiver_id, title, content, parent_id)
                   VALUES (?, ?, ?, ?, ?)''',
                (sender_id, receiver_id, title, content, parent_id)
            )
            conn.commit()
            msg_id = cursor.lastrowid

            self.send_notification(
                receiver_id,
                f'新消息: {title}',
                content[:100] + ('...' if len(content) > 100 else ''),
                notification_type='message',
                icon='💬',
                sender_id=sender_id
            )

            logger.info(f"发送私信: 发送者={sender_id}, 接收者={receiver_id}, 标题={title}")
            return msg_id

    def get_messages(self, user_id: int, folder: str = 'inbox', limit: int = 50) -> List[Dict]:
        """获取消息列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if folder == 'inbox':
                cursor.execute(
                    '''SELECT * FROM user_messages 
                       WHERE receiver_id = ? ORDER BY created_at DESC LIMIT ?''',
                    (user_id, limit)
                )
            elif folder == 'sent':
                cursor.execute(
                    '''SELECT * FROM user_messages 
                       WHERE sender_id = ? ORDER BY created_at DESC LIMIT ?''',
                    (user_id, limit)
                )
            else:
                cursor.execute(
                    '''SELECT * FROM user_messages 
                       WHERE sender_id = ? OR receiver_id = ?
                       ORDER BY created_at DESC LIMIT ?''',
                    (user_id, user_id, limit)
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_message_detail(self, message_id: int, user_id: int) -> Optional[Dict]:
        """获取消息详情"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM user_messages 
                   WHERE id = ? AND (sender_id = ? OR receiver_id = ?)''',
                (message_id, user_id, user_id)
            )
            row = cursor.fetchone()
            if not row:
                return None

            msg = dict(row)

            if msg['receiver_id'] == user_id and not msg['is_read']:
                cursor.execute(
                    '''UPDATE user_messages SET is_read = 1, read_at = ? 
                       WHERE id = ?''',
                    (datetime.now().isoformat(), message_id)
                )
                conn.commit()
                msg['is_read'] = 1
                msg['read_at'] = datetime.now().isoformat()

            return msg

    def get_unread_message_count(self, user_id: int) -> int:
        """获取未读消息数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) as count FROM user_messages WHERE receiver_id = ? AND is_read = 0',
                (user_id,)
            )
            return cursor.fetchone()['count']

    def get_stats(self, user_id: int) -> Dict:
        """获取通知统计"""
        return {
            'unread_notifications': self.get_unread_count(user_id),
            'unread_messages': self.get_unread_message_count(user_id),
            'total_notifications': len(self.get_notifications(user_id, limit=1000)),
            'total_messages': len(self.get_messages(user_id, 'all', limit=1000))
        }
