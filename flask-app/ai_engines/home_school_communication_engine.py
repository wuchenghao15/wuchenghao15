# -*- coding: utf-8 -*-
"""
家校沟通引擎
家长-教师-学生三方沟通、消息通知、学习情况同步、家长会预约、家校互动记录
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('home_school_communication_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HomeSchoolCommunicationEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class HomeSchoolCommunicationEngine:
    """家校沟通引擎 - 家长-教师-学生三方沟通"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._init_database()
        self._initialized = True
        logger.info("HomeSchoolCommunicationEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 家校关系表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS home_school_relations (
                        relation_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        parent_id TEXT NOT NULL,
                        parent_name TEXT,
                        parent_role TEXT DEFAULT 'parent',
                        contact_phone TEXT,
                        contact_email TEXT,
                        is_primary BOOLEAN DEFAULT 0,
                        notification_enabled BOOLEAN DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(student_id, parent_id)
                    )
                ''')

                # 2. 家校消息表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS home_school_messages (
                        message_id TEXT PRIMARY KEY,
                        sender_id TEXT NOT NULL,
                        sender_role TEXT,
                        recipient_id TEXT NOT NULL,
                        recipient_role TEXT,
                        student_id TEXT,
                        subject TEXT,
                        content TEXT NOT NULL,
                        message_type TEXT DEFAULT 'normal',
                        priority TEXT DEFAULT 'normal',
                        attachments TEXT DEFAULT '[]',
                        read_status TEXT DEFAULT 'unread',
                        read_at TEXT,
                        parent_message_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 3. 家长会预约表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_meetings (
                        meeting_id TEXT PRIMARY KEY,
                        teacher_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        meeting_type TEXT DEFAULT 'regular',
                        meeting_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        location TEXT,
                        location_url TEXT,
                        max_attendees INTEGER DEFAULT 30,
                        current_attendees INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        agenda TEXT DEFAULT '[]',
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 4. 家长会预约记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_meeting_registrations (
                        registration_id TEXT PRIMARY KEY,
                        meeting_id TEXT NOT NULL,
                        parent_id TEXT NOT NULL,
                        student_id TEXT,
                        status TEXT DEFAULT 'registered',
                        attended BOOLEAN DEFAULT 0,
                        feedback TEXT,
                        registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES parent_meetings(meeting_id)
                    )
                ''')

                # 5. 学习情况同步表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_sync_records (
                        sync_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        parent_id TEXT,
                        sync_type TEXT,
                        sync_content TEXT,
                        sync_data TEXT DEFAULT '{}',
                        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        read_at TEXT,
                        status TEXT DEFAULT 'sent'
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hsr_student ON home_school_relations(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hsm_recipient ON home_school_messages(recipient_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hsm_student ON home_school_messages(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pm_teacher ON parent_meetings(teacher_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pmr_meeting ON parent_meeting_registrations(meeting_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lsr_student ON learning_sync_records(student_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化家校沟通数据库失败: {e}")

    # ==================== 家校关系管理 ====================

    def bind_parent(self, student_id: str, parent_id: str, parent_name: str = None,
                    parent_role: str = 'parent', contact_phone: str = None,
                    contact_email: str = None, is_primary: bool = False) -> Dict[str, Any]:
        """绑定家长与学生"""
        with self._lock:
            try:
                relation_id = f"rel_{int(time.time())}_{parent_id[:8]}_{student_id[:8]}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO home_school_relations
                        (relation_id, student_id, parent_id, parent_name, parent_role,
                         contact_phone, contact_email, is_primary, notification_enabled)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (relation_id, student_id, parent_id, parent_name, parent_role,
                          contact_phone, contact_email, 1 if is_primary else 0))
                    conn.commit()

                return {'success': True, 'relation_id': relation_id, 'message': '家长绑定成功'}
            except Exception as e:
                logger.error(f"绑定家长失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_parent_relations(self, student_id: str) -> Dict[str, Any]:
        """获取学生的所有家长"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT parent_id, parent_name, parent_role, contact_phone,
                           contact_email, is_primary, notification_enabled
                    FROM home_school_relations
                    WHERE student_id = ?
                    ORDER BY is_primary DESC
                ''', (student_id,))
                rows = cursor.fetchall()

                parents = [{
                    'parent_id': r[0], 'parent_name': r[1], 'parent_role': r[2],
                    'contact_phone': r[3], 'contact_email': r[4],
                    'is_primary': bool(r[5]), 'notification_enabled': bool(r[6])
                } for r in rows]

                return {
                    'success': True,
                    'student_id': student_id,
                    'parents': parents,
                    'count': len(parents)
                }
        except Exception as e:
            logger.error(f"获取家长关系失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_student_relations(self, parent_id: str) -> Dict[str, Any]:
        """获取家长的所有学生"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_id, parent_name, parent_role, is_primary
                    FROM home_school_relations
                    WHERE parent_id = ?
                ''', (parent_id,))
                rows = cursor.fetchall()

                students = [{
                    'student_id': r[0], 'parent_name': r[1], 'parent_role': r[2],
                    'is_primary': bool(r[3])
                } for r in rows]

                return {
                    'success': True,
                    'parent_id': parent_id,
                    'students': students,
                    'count': len(students)
                }
        except Exception as e:
            logger.error(f"获取学生关系失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 消息沟通 ====================

    def send_message(self, sender_id: str, sender_role: str, recipient_id: str,
                     recipient_role: str, content: str, subject: str = None,
                     student_id: str = None, message_type: str = 'normal',
                     priority: str = 'normal', attachments: List = None,
                     parent_message_id: str = None) -> Dict[str, Any]:
        """发送家校消息"""
        with self._lock:
            try:
                message_id = f"msg_{int(time.time() * 1000)}_{sender_id[:8]}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO home_school_messages
                        (message_id, sender_id, sender_role, recipient_id, recipient_role,
                         student_id, subject, content, message_type, priority,
                         attachments, parent_message_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (message_id, sender_id, sender_role, recipient_id, recipient_role,
                          student_id, subject, content, message_type, priority,
                          json.dumps(attachments or [], ensure_ascii=False),
                          parent_message_id))
                    conn.commit()

                return {
                    'success': True,
                    'message_id': message_id,
                    'message': '消息已发送'
                }
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_messages(self, user_id: str, role: str = None, student_id: str = None,
                     unread_only: bool = False, limit: int = 30) -> Dict[str, Any]:
        """获取用户消息列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT message_id, sender_id, sender_role, recipient_id, recipient_role,
                                student_id, subject, content, message_type, priority,
                                read_status, read_at, created_at
                         FROM home_school_messages
                         WHERE recipient_id = ?'''
                params = [user_id]
                if student_id:
                    sql += ' AND student_id = ?'
                    params.append(student_id)
                if unread_only:
                    sql += ' AND read_status = "unread"'
                sql += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                messages = [{
                    'message_id': r[0], 'sender_id': r[1], 'sender_role': r[2],
                    'recipient_id': r[3], 'recipient_role': r[4], 'student_id': r[5],
                    'subject': r[6], 'content': r[7], 'message_type': r[8],
                    'priority': r[9], 'read_status': r[10], 'read_at': r[11],
                    'created_at': r[12]
                } for r in rows]

                # 获取未读数
                cursor.execute('SELECT COUNT(*) FROM home_school_messages WHERE recipient_id = ? AND read_status = "unread"',
                               (user_id,))
                unread_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'user_id': user_id,
                    'messages': messages,
                    'count': len(messages),
                    'unread_count': unread_count
                }
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return {'success': False, 'error': str(e)}

    def mark_message_read(self, message_id: str) -> Dict[str, Any]:
        """标记消息为已读"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE home_school_messages
                        SET read_status = 'read', read_at = ?
                        WHERE message_id = ?
                    ''', (datetime.now().isoformat(), message_id))
                    conn.commit()

                return {'success': True, 'message': '消息已标记为已读'}
            except Exception as e:
                logger.error(f"标记已读失败: {e}")
                return {'success': False, 'error': str(e)}

    def mark_all_read(self, user_id: str) -> Dict[str, Any]:
        """标记所有消息为已读"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE home_school_messages
                        SET read_status = 'read', read_at = ?
                        WHERE recipient_id = ? AND read_status = 'unread'
                    ''', (datetime.now().isoformat(), user_id))
                    affected = cursor.rowcount
                    conn.commit()

                return {'success': True, 'marked_read': affected, 'message': f'已标记 {affected} 条消息为已读'}
            except Exception as e:
                logger.error(f"标记全部已读失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 家长会管理 ====================

    def create_parent_meeting(self, teacher_id: str, title: str, meeting_date: str,
                              start_time: str, end_time: str, location: str = None,
                              location_url: str = None, description: str = None,
                              meeting_type: str = 'regular', max_attendees: int = 30,
                              agenda: List = None) -> Dict[str, Any]:
        """创建家长会"""
        with self._lock:
            try:
                meeting_id = f"mtg_{int(time.time())}_{teacher_id[:8]}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO parent_meetings
                        (meeting_id, teacher_id, title, description, meeting_type,
                         meeting_date, start_time, end_time, location, location_url,
                         max_attendees, agenda)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (meeting_id, teacher_id, title, description, meeting_type,
                          meeting_date, start_time, end_time, location, location_url,
                          max_attendees, json.dumps(agenda or [], ensure_ascii=False)))
                    conn.commit()

                return {
                    'success': True,
                    'meeting_id': meeting_id,
                    'message': '家长会已创建'
                }
            except Exception as e:
                logger.error(f"创建家长会失败: {e}")
                return {'success': False, 'error': str(e)}

    def register_meeting(self, meeting_id: str, parent_id: str,
                         student_id: str = None) -> Dict[str, Any]:
        """家长预约家长会"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    # 检查会议状态和容量
                    cursor.execute('SELECT status, max_attendees, current_attendees FROM parent_meetings WHERE meeting_id = ?',
                                   (meeting_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '家长会不存在'}
                    if row[0] != 'scheduled':
                        return {'success': False, 'message': '家长会已结束或取消'}
                    if row[2] >= row[1]:
                        return {'success': False, 'message': '家长会名额已满'}

                    # 检查是否已预约
                    cursor.execute('SELECT COUNT(*) FROM parent_meeting_registrations WHERE meeting_id = ? AND parent_id = ?',
                                   (meeting_id, parent_id))
                    if cursor.fetchone()[0] > 0:
                        return {'success': False, 'message': '已预约过此家长会'}

                    registration_id = f"reg_{int(time.time())}_{parent_id[:8]}"
                    cursor.execute('''
                        INSERT INTO parent_meeting_registrations
                        (registration_id, meeting_id, parent_id, student_id)
                        VALUES (?, ?, ?, ?)
                    ''', (registration_id, meeting_id, parent_id, student_id))

                    # 更新参会人数
                    cursor.execute('UPDATE parent_meetings SET current_attendees = current_attendees + 1 WHERE meeting_id = ?',
                                   (meeting_id,))
                    conn.commit()

                return {
                    'success': True,
                    'registration_id': registration_id,
                    'message': '家长会预约成功'
                }
            except Exception as e:
                logger.error(f"预约家长会失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_upcoming_meetings(self, parent_id: str = None, teacher_id: str = None,
                              limit: int = 10) -> Dict[str, Any]:
        """获取即将到来的家长会"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                today = datetime.now().strftime('%Y-%m-%d')
                sql = '''SELECT meeting_id, teacher_id, title, description, meeting_type,
                                meeting_date, start_time, end_time, location, location_url,
                                max_attendees, current_attendees, status
                         FROM parent_meetings
                         WHERE meeting_date >= ? AND status = 'scheduled'
                         ORDER BY meeting_date ASC, start_time ASC LIMIT ?'''
                cursor.execute(sql, (today, limit))
                rows = cursor.fetchall()

                meetings = []
                for r in rows:
                    meeting = {
                        'meeting_id': r[0], 'teacher_id': r[1], 'title': r[2],
                        'description': r[3], 'meeting_type': r[4], 'meeting_date': r[5],
                        'start_time': r[6], 'end_time': r[7], 'location': r[8],
                        'location_url': r[9], 'max_attendees': r[10],
                        'current_attendees': r[11], 'status': r[12]
                    }

                    # 如果是家长，检查是否已预约
                    if parent_id:
                        cursor.execute('SELECT registration_id, status FROM parent_meeting_registrations WHERE meeting_id = ? AND parent_id = ?',
                                       (r[0], parent_id))
                        reg_row = cursor.fetchone()
                        meeting['registered'] = bool(reg_row)
                        meeting['registration_status'] = reg_row[1] if reg_row else None

                    meetings.append(meeting)

                return {
                    'success': True,
                    'meetings': meetings,
                    'count': len(meetings)
                }
        except Exception as e:
            logger.error(f"获取家长会失败: {e}")
            return {'success': False, 'error': str(e)}

    def mark_meeting_attendance(self, registration_id: str, attended: bool = True,
                                feedback: str = None) -> Dict[str, Any]:
        """标记家长会参会情况"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE parent_meeting_registrations
                        SET attended = ?, feedback = ?
                        WHERE registration_id = ?
                    ''', (1 if attended else 0, feedback, registration_id))
                    conn.commit()

                return {'success': True, 'message': '参会情况已更新'}
            except Exception as e:
                logger.error(f"标记参会失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 学习情况同步 ====================

    def sync_learning_status(self, student_id: str, parent_id: str, sync_type: str,
                             sync_content: str, sync_data: Dict = None) -> Dict[str, Any]:
        """同步学习情况到家长"""
        with self._lock:
            try:
                sync_id = f"sync_{int(time.time() * 1000)}_{student_id[:8]}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_sync_records
                        (sync_id, student_id, parent_id, sync_type, sync_content, sync_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (sync_id, student_id, parent_id, sync_type, sync_content,
                          json.dumps(sync_data or {}, ensure_ascii=False)))
                    conn.commit()

                return {
                    'success': True,
                    'sync_id': sync_id,
                    'message': '学习情况已同步至家长'
                }
            except Exception as e:
                logger.error(f"同步学习情况失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_sync_records(self, parent_id: str = None, student_id: str = None,
                         limit: int = 20) -> Dict[str, Any]:
        """获取学习情况同步记录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT sync_id, student_id, parent_id, sync_type, sync_content,
                                sync_data, sent_at, read_at, status
                         FROM learning_sync_records WHERE 1=1'''
                params = []
                if parent_id:
                    sql += ' AND parent_id = ?'
                    params.append(parent_id)
                if student_id:
                    sql += ' AND student_id = ?'
                    params.append(student_id)
                sql += ' ORDER BY sent_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                records = []
                for r in rows:
                    sync_data = r[5]
                    try:
                        sync_data = json.loads(sync_data) if sync_data else {}
                    except Exception:
                        sync_data = {}
                    records.append({
                        'sync_id': r[0], 'student_id': r[1], 'parent_id': r[2],
                        'sync_type': r[3], 'sync_content': r[4], 'sync_data': sync_data,
                        'sent_at': r[6], 'read_at': r[7], 'status': r[8]
                    })

                return {
                    'success': True,
                    'records': records,
                    'count': len(records)
                }
        except Exception as e:
            logger.error(f"获取同步记录失败: {e}")
            return {'success': False, 'error': str(e)}

    def mark_sync_read(self, sync_id: str) -> Dict[str, Any]:
        """标记同步记录为已读"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE learning_sync_records
                        SET read_at = ?, status = 'read'
                        WHERE sync_id = ?
                    ''', (datetime.now().isoformat(), sync_id))
                    conn.commit()

                return {'success': True, 'message': '已标记为已读'}
            except Exception as e:
                logger.error(f"标记同步已读失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 统计 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM home_school_relations')
                relation_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM home_school_messages')
                msg_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM home_school_messages WHERE read_status = "unread"')
                unread_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM parent_meetings')
                meeting_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM parent_meeting_registrations')
                reg_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_sync_records')
                sync_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'relations': relation_count,
                    'messages': msg_count,
                    'unread_messages': unread_count,
                    'meetings': meeting_count,
                    'registrations': reg_count,
                    'sync_records': sync_count
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}


# 单例实例
home_school_communication_engine = HomeSchoolCommunicationEngine()
