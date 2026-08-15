#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 校园通知与消息服务 (v15.3.0)
====================================
提供校园通知发布、站内消息、家校沟通和消息推送等综合服务。

核心能力：
1. 通知管理 - 校园通知发布、置顶、过期管理
2. 站内消息 - 用户间消息发送、群发、已读追踪
3. 家校沟通 - 教师与家长沟通渠道
4. 消息推送 - 多渠道推送（站内/邮件/短信）
5. 消息模板 - 预设消息模板快速发送
6. 消息分类 - 按类型/优先级/对象分类
7. 成人通知 - 成人教育专属通知
8. K12通知 - 九年制义务教育通知
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notification_messaging_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NotificationMessaging')


# ========== 通知配置 ==========

# 通知类型
NOTIFICATION_TYPES = {
    'system': {'name': '系统通知', 'icon': 'info', 'color': '#1890ff'},
    'academic': {'name': '教务通知', 'icon': 'book', 'color': '#52c41a'},
    'exam': {'name': '考试通知', 'icon': 'exam', 'color': '#faad14'},
    'activity': {'name': '活动通知', 'icon': 'calendar', 'color': '#722ed1'},
    'urgent': {'name': '紧急通知', 'icon': 'warning', 'color': '#f5222d'},
    'holiday': {'name': '放假通知', 'icon': 'home', 'color': '#13c2c2'},
    'fee': {'name': '缴费通知', 'icon': 'pay', 'color': '#eb2f96'},
    'meeting': {'name': '会议通知', 'icon': 'team', 'color': '#fa8c16'}
}

# 通知优先级
NOTIFICATION_PRIORITY = {
    1: {'name': '低', 'color': '#d9d9d9', 'push_enabled': False},
    2: {'name': '中', 'color': '#1890ff', 'push_enabled': True},
    3: {'name': '高', 'color': '#faad14', 'push_enabled': True},
    4: {'name': '紧急', 'color': '#f5222d', 'push_enabled': True},
    5: {'name': '特急', 'color': '#f5222d', 'push_enabled': True}
}

# 通知目标范围
TARGET_SCOPES = {
    'all': {'name': '全体用户', 'description': '所有用户可见'},
    'grade': {'name': '指定年级', 'description': '按年级筛选用户'},
    'class': {'name': '指定班级', 'description': '按班级筛选用户'},
    'subject': {'name': '指定科目', 'description': '按科目筛选用户'},
    'role': {'name': '指定角色', 'description': '按角色筛选用户'},
    'individual': {'name': '指定个人', 'description': '指定单个用户'},
    'education_type': {'name': '教育类型', 'description': '按教育类型筛选'}
}

# 消息类型
MESSAGE_TYPES = {
    'text': {'name': '文本消息', 'support_rich': False},
    'rich_text': {'name': '富文本消息', 'support_rich': True},
    'notice': {'name': '公告消息', 'support_rich': True},
    'assignment': {'name': '作业消息', 'support_rich': False},
    'grade': {'name': '成绩消息', 'support_rich': False},
    'feedback': {'name': '反馈消息', 'support_rich': False},
    'reminder': {'name': '提醒消息', 'support_rich': False}
}

# 推送渠道
PUSH_CHANNELS = {
    'in_app': {'name': '站内推送', 'enabled': True, 'priority': 1},
    'email': {'name': '邮件推送', 'enabled': True, 'priority': 2},
    'sms': {'name': '短信推送', 'enabled': False, 'priority': 3},
    'websocket': {'name': '实时推送', 'enabled': True, 'priority': 1}
}

# 消息状态
MESSAGE_STATUS = {
    'draft': '草稿',
    'sent': '已发送',
    'delivered': '已送达',
    'read': '已读',
    'archived': '已归档',
    'deleted': '已删除'
}

# 家校沟通消息分类
HOME_SCHOOL_CATEGORIES = {
    'academic': {'name': '学业沟通', 'description': '学习情况、成绩、作业等'},
    'behavior': {'name': '行为沟通', 'description': '在校表现、纪律等'},
    'attendance': {'name': '考勤沟通', 'description': '出勤、请假等'},
    'health': {'name': '健康沟通', 'description': '身体状况、心理等'},
    'activity': {'name': '活动沟通', 'description': '校园活动、比赛等'},
    'suggestion': {'name': '建议反馈', 'description': '家长建议、意见反馈'},
    'other': {'name': '其他沟通', 'description': '其他事项'}
}


class NotificationMessagingService:
    """校园通知与消息服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        notification_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        notification_type TEXT DEFAULT 'system',
                        priority INTEGER DEFAULT 2,
                        education_type TEXT,
                        target_scope TEXT DEFAULT 'all',
                        target_data TEXT,
                        sender_id INTEGER,
                        sender_name TEXT,
                        is_pinned INTEGER DEFAULT 0,
                        is_published INTEGER DEFAULT 0,
                        publish_time TEXT,
                        expire_time TEXT,
                        read_count INTEGER DEFAULT 0,
                        total_recipients INTEGER DEFAULT 0,
                        attachments TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_reads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        read_at TEXT,
                        UNIQUE(notification_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id TEXT PRIMARY KEY,
                        sender_id INTEGER NOT NULL,
                        sender_name TEXT,
                        receiver_id INTEGER,
                        receiver_type TEXT DEFAULT 'user',
                        group_id TEXT,
                        subject TEXT,
                        content TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text',
                        parent_id TEXT,
                        education_type TEXT,
                        category TEXT,
                        is_read INTEGER DEFAULT 0,
                        read_at TEXT,
                        is_starred INTEGER DEFAULT 0,
                        is_archived INTEGER DEFAULT 0,
                        attachments TEXT,
                        sent_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS message_groups (
                        group_id TEXT PRIMARY KEY,
                        group_name TEXT NOT NULL,
                        group_type TEXT DEFAULT 'normal',
                        creator_id INTEGER,
                        member_count INTEGER DEFAULT 0,
                        max_members INTEGER DEFAULT 100,
                        description TEXT,
                        avatar_url TEXT,
                        is_muted INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS message_group_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        role TEXT DEFAULT 'member',
                        joined_at TEXT,
                        last_read_message_id TEXT,
                        unread_count INTEGER DEFAULT 0,
                        is_muted INTEGER DEFAULT 0,
                        UNIQUE(group_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS message_templates (
                        template_id TEXT PRIMARY KEY,
                        template_name TEXT NOT NULL,
                        template_type TEXT,
                        subject TEXT,
                        content TEXT NOT NULL,
                        variables TEXT,
                        category TEXT,
                        created_by INTEGER,
                        is_active INTEGER DEFAULT 1,
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS home_school_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        teacher_id INTEGER NOT NULL,
                        parent_id INTEGER,
                        direction TEXT DEFAULT 'to_parent',
                        category TEXT,
                        subject TEXT,
                        content TEXT NOT NULL,
                        is_read INTEGER DEFAULT 0,
                        read_at TEXT,
                        teacher_name TEXT,
                        parent_name TEXT,
                        attachments TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS push_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT,
                        message_id TEXT,
                        user_id INTEGER NOT NULL,
                        channel TEXT,
                        status TEXT DEFAULT 'pending',
                        retry_count INTEGER DEFAULT 0,
                        error_message TEXT,
                        sent_at TEXT,
                        delivered_at TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('通知与消息服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_notification(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            notification_id = f"ntf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            target_data = json.dumps(kwargs.get('target_data'), ensure_ascii=False) if kwargs.get('target_data') else None
            attachments = json.dumps(kwargs.get('attachments'), ensure_ascii=False) if kwargs.get('attachments') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO notifications (
                            notification_id, title, content, notification_type, priority,
                            education_type, target_scope, target_data, sender_id, sender_name,
                            is_pinned, is_published, publish_time, expire_time,
                            total_recipients, attachments, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        notification_id, title, content,
                        kwargs.get('notification_type', 'system'),
                        kwargs.get('priority', 2),
                        kwargs.get('education_type'),
                        kwargs.get('target_scope', 'all'),
                        target_data,
                        kwargs.get('sender_id'),
                        kwargs.get('sender_name'),
                        kwargs.get('is_pinned', 0),
                        kwargs.get('is_published', 0),
                        kwargs.get('publish_time'),
                        kwargs.get('expire_time'),
                        kwargs.get('total_recipients', 0),
                        attachments, now, now
                    ))
                    conn.commit()
                    logger.info(f'创建通知: {title} ({notification_id})')
                    return {'success': True, 'notification_id': notification_id, 'title': title}
        except Exception as e:
            logger.error(f'创建通知失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_notification(self, notification_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE notifications SET is_published = 1, publish_time = ?, updated_at = ?
                        WHERE notification_id = ? AND is_published = 0
                    ''', (now, now, notification_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布通知: {notification_id}')
                        return {'success': True}
                    return {'success': False, 'error': '通知不存在或已发布'}
        except Exception as e:
            logger.error(f'发布通知失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM notifications WHERE notification_id = ?', (notification_id,))
                row = cursor.fetchone()
                if row:
                    n = dict(row)
                    if n.get('target_data'):
                        n['target_data'] = json.loads(n['target_data'])
                    if n.get('attachments'):
                        n['attachments'] = json.loads(n['attachments'])
                    return n
                return None
        except Exception as e:
            logger.error(f'获取通知失败: {e}')
            return None

    def list_notifications(self, education_type: str = None, notification_type: str = None,
                           priority: int = None, is_published: int = 1,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM notifications WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND (education_type = ? OR education_type IS NULL)'
                    params.append(education_type)
                if notification_type:
                    query += ' AND notification_type = ?'
                    params.append(notification_type)
                if priority:
                    query += ' AND priority = ?'
                    params.append(priority)
                if is_published is not None:
                    query += ' AND is_published = ?'
                    params.append(is_published)
                query += ' AND (expire_time IS NULL OR expire_time > ?)'
                params.append(datetime.now().isoformat())
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY is_pinned DESC, priority DESC, publish_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                notifications = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'notifications': notifications, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取通知列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def read_notification(self, notification_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO notification_reads (notification_id, user_id, read_at)
                        VALUES (?, ?, ?)
                    ''', (notification_id, user_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            UPDATE notifications SET read_count = read_count + 1 WHERE notification_id = ?
                        ''', (notification_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'标记通知已读失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_unread_notification_count(self, user_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT COUNT(*) FROM notifications n
                    WHERE n.is_published = 1
                    AND (n.expire_time IS NULL OR n.expire_time > ?)
                    AND NOT EXISTS (
                        SELECT 1 FROM notification_reads nr
                        WHERE nr.notification_id = n.notification_id AND nr.user_id = ?
                    )
                '''
                params = [datetime.now().isoformat(), user_id]
                if education_type:
                    query += ' AND (n.education_type = ? OR n.education_type IS NULL)'
                    params.append(education_type)
                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                return {'success': True, 'unread_count': count}
        except Exception as e:
            logger.error(f'获取未读通知数失败: {e}')
            return {'success': False, 'error': str(e)}

    def send_message(self, sender_id: int, content: str, **kwargs) -> Dict[str, Any]:
        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            attachments = json.dumps(kwargs.get('attachments'), ensure_ascii=False) if kwargs.get('attachments') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO messages (
                            message_id, sender_id, sender_name, receiver_id, receiver_type,
                            group_id, subject, content, message_type, parent_id,
                            education_type, category, is_read, attachments, sent_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    ''', (
                        message_id, sender_id, kwargs.get('sender_name'),
                        kwargs.get('receiver_id'), kwargs.get('receiver_type', 'user'),
                        kwargs.get('group_id'), kwargs.get('subject'), content,
                        kwargs.get('message_type', 'text'), kwargs.get('parent_id'),
                        kwargs.get('education_type'), kwargs.get('category'),
                        attachments, now, now
                    ))
                    if kwargs.get('group_id'):
                        cursor.execute('''
                            UPDATE message_group_members SET unread_count = unread_count + 1
                            WHERE group_id = ? AND user_id != ?
                        ''', (kwargs['group_id'], sender_id))
                    conn.commit()
                    logger.info(f'发送消息: {message_id}')
                    return {'success': True, 'message_id': message_id}
        except Exception as e:
            logger.error(f'发送消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_messages(self, user_id: int, folder: str = 'inbox',
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if folder == 'inbox':
                    query = 'SELECT * FROM messages WHERE receiver_id = ? AND is_archived = 0'
                    params = [user_id]
                elif folder == 'sent':
                    query = 'SELECT * FROM messages WHERE sender_id = ?'
                    params = [user_id]
                elif folder == 'starred':
                    query = 'SELECT * FROM messages WHERE (receiver_id = ? OR sender_id = ?) AND is_starred = 1'
                    params = [user_id, user_id]
                elif folder == 'archived':
                    query = 'SELECT * FROM messages WHERE receiver_id = ? AND is_archived = 1'
                    params = [user_id]
                else:
                    query = 'SELECT * FROM messages WHERE receiver_id = ? OR sender_id = ?'
                    params = [user_id, user_id]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                messages = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'messages': messages, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取消息列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def read_message(self, message_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE messages SET is_read = 1, read_at = ?
                        WHERE message_id = ? AND receiver_id = ? AND is_read = 0
                    ''', (now, message_id, user_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'标记消息已读失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_unread_message_count(self, user_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND is_read = 0 AND is_archived = 0', (user_id,))
                direct_count = cursor.fetchone()[0]
                cursor.execute('''
                    SELECT SUM(unread_count) FROM message_group_members WHERE user_id = ?
                ''', (user_id,))
                group_count = cursor.fetchone()[0] or 0
                return {'success': True, 'unread_direct': direct_count, 'unread_group': group_count, 'total_unread': direct_count + group_count}
        except Exception as e:
            logger.error(f'获取未读消息数失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_message_group(self, group_name: str, creator_id: int, **kwargs) -> Dict[str, Any]:
        try:
            group_id = f"grp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO message_groups (
                            group_id, group_name, group_type, creator_id, member_count,
                            max_members, description, avatar_url, is_muted, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, 0, ?, ?)
                    ''', (group_id, group_name, kwargs.get('group_type', 'normal'),
                          creator_id, kwargs.get('max_members', 100),
                          kwargs.get('description'), kwargs.get('avatar_url'), now, now))
                    cursor.execute('''
                        INSERT INTO message_group_members (group_id, user_id, role, joined_at, unread_count, is_muted)
                        VALUES (?, ?, 'admin', ?, 0, 0)
                    ''', (group_id, creator_id, now))
                    conn.commit()
                    logger.info(f'创建消息群组: {group_name} ({group_id})')
                    return {'success': True, 'group_id': group_id, 'group_name': group_name}
        except Exception as e:
            logger.error(f'创建消息群组失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_group_member(self, group_id: str, user_id: int, role: str = 'member') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT member_count, max_members FROM message_groups WHERE group_id = ?', (group_id,))
                    grp = cursor.fetchone()
                    if not grp:
                        return {'success': False, 'error': '群组不存在'}
                    if grp[0] >= grp[1]:
                        return {'success': False, 'error': '群组成员已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO message_group_members (group_id, user_id, role, joined_at, unread_count, is_muted)
                        VALUES (?, ?, ?, ?, 0, 0)
                    ''', (group_id, user_id, role, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE message_groups SET member_count = member_count + 1, updated_at = ? WHERE group_id = ?', (now, group_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加群组成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def send_home_school_message(self, student_id: int, teacher_id: int,
                                  direction: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO home_school_messages (
                            student_id, teacher_id, parent_id, direction, category,
                            subject, content, is_read, teacher_name, parent_name,
                            attachments, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ''', (
                        student_id, teacher_id, kwargs.get('parent_id'),
                        direction, kwargs.get('category', 'academic'),
                        kwargs.get('subject'), content,
                        kwargs.get('teacher_name'), kwargs.get('parent_name'),
                        json.dumps(kwargs.get('attachments'), ensure_ascii=False) if kwargs.get('attachments') else None,
                        now
                    ))
                    msg_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f'发送家校消息: {msg_id}')
                    return {'success': True, 'message_id': msg_id}
        except Exception as e:
            logger.error(f'发送家校消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_home_school_messages(self, student_id: int = None, teacher_id: int = None,
                                  parent_id: int = None, category: str = None,
                                  page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM home_school_messages WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if teacher_id:
                    query += ' AND teacher_id = ?'
                    params.append(teacher_id)
                if parent_id:
                    query += ' AND parent_id = ?'
                    params.append(parent_id)
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                messages = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'messages': messages, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取家校消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_template(self, template_name: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            variables = json.dumps(kwargs.get('variables'), ensure_ascii=False) if kwargs.get('variables') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO message_templates (
                            template_id, template_name, template_type, subject, content,
                            variables, category, created_by, is_active, usage_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
                    ''', (template_id, template_name, kwargs.get('template_type'),
                          kwargs.get('subject'), content, variables,
                          kwargs.get('category'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建消息模板: {template_name} ({template_id})')
                    return {'success': True, 'template_id': template_id}
        except Exception as e:
            logger.error(f'创建消息模板失败: {e}')
            return {'success': False, 'error': str(e)}

    def use_template(self, template_id: str, variables: dict = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM message_templates WHERE template_id = ? AND is_active = 1', (template_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '模板不存在或已禁用'}
                tmpl = dict(row)
                content = tmpl['content']
                subject = tmpl.get('subject', '')
                if variables:
                    for key, value in variables.items():
                        content = content.replace(f'{{{key}}}', str(value))
                        if subject:
                            subject = subject.replace(f'{{{key}}}', str(value))
                cursor.execute('UPDATE message_templates SET usage_count = usage_count + 1 WHERE template_id = ?', (template_id,))
                conn.commit()
                return {'success': True, 'subject': subject, 'content': content}
        except Exception as e:
            logger.error(f'使用消息模板失败: {e}')
            return {'success': False, 'error': str(e)}

    def star_message(self, message_id: str, user_id: int) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE messages SET is_starred = 1 WHERE message_id = ? AND (receiver_id = ? OR sender_id = ?)
                    ''', (message_id, user_id, user_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'星标消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_message(self, message_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE messages SET is_archived = 1 WHERE message_id = ?', (message_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'归档消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def pin_notification(self, notification_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE notifications SET is_pinned = 1, updated_at = ? WHERE notification_id = ?',
                                 (datetime.now().isoformat(), notification_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'置顶通知失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_notification_stats(self, notification_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT total_recipients, read_count FROM notifications WHERE notification_id = ?', (notification_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '通知不存在'}
                total, read = row
                return {
                    'success': True,
                    'total_recipients': total,
                    'read_count': read,
                    'unread_count': total - read,
                    'read_rate': round(read / total * 100, 2) if total > 0 else 0
                }
        except Exception as e:
            logger.error(f'获取通知统计失败: {e}')
            return {'success': False, 'error': str(e)}
