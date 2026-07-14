# -*- coding: utf-8 -*-
"""
消息通知系统API - 站内消息、邮件通知、推送服务、消息管理
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

notification_system_api = Blueprint('notification_system_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_response(code=200, message='success', data=None):
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT DEFAULT 'info',
                priority TEXT DEFAULT 'normal',
                read INTEGER DEFAULT 0,
                read_at TEXT,
                link TEXT,
                sender_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (sender_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                email_notify INTEGER DEFAULT 1,
                push_notify INTEGER DEFAULT 1,
                system_notify INTEGER DEFAULT 1,
                exam_notify INTEGER DEFAULT 1,
                course_notify INTEGER DEFAULT 1,
                homework_notify INTEGER DEFAULT 1,
                community_notify INTEGER DEFAULT 1,
                sound_enabled INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                title_template TEXT,
                content_template TEXT,
                type TEXT DEFAULT 'info',
                priority TEXT DEFAULT 'normal',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                to_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                content TEXT,
                template_code TEXT,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                scheduled_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                error_message TEXT,
                FOREIGN KEY (template_code) REFERENCES notification_templates(template_code)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                data TEXT,
                platform TEXT DEFAULT 'web',
                status TEXT DEFAULT 'pending',
                delivered_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '🔔',
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notification_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                enabled INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES notification_categories(id),
                UNIQUE(user_id, category_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 消息通知系统表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建消息通知系统表失败: {e}")


create_tables()


@notification_system_api.route('/api/notifications', methods=['GET'])
@require_login
def get_notifications():
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        type_filter = request.args.get('type', '')
        read_status = request.args.get('read', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if role in ['admin', 'super_admin']:
            target_user_id = request.args.get('user_id')
            if target_user_id:
                where_clauses.append('n.recipient_id = ?')
                params.append(target_user_id)
        else:
            where_clauses.append('n.recipient_id = ?')
            params.append(user_id)

        if type_filter:
            where_clauses.append('n.type = ?')
            params.append(type_filter)

        if read_status:
            if read_status == 'unread':
                where_clauses.append("n.status = 'unread'")
            elif read_status == 'read':
                where_clauses.append("n.status = 'read'")

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM notifications n {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        cursor.execute(f"SELECT COUNT(*) FROM notifications n WHERE n.recipient_id = ? AND n.status = 'unread'", [user_id])
        unread_count = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT n.id, n.recipient_id, n.title, n.content, n.type, n.priority, 
                   n.status, n.sender_id, n.created_at, n.expires_at, n.metadata,
                   u.username as sender_name
            FROM notifications n
            LEFT JOIN users u ON n.sender_id = u.id
            {where_sql}
            ORDER BY n.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row['id'],
                'user_id': row['recipient_id'],
                'title': row['title'],
                'content': row['content'] or '',
                'type': row['type'],
                'priority': row['priority'],
                'read': row['status'] == 'read',
                'read_at': None,
                'link': '',
                'sender_id': row['sender_id'],
                'sender_name': row['sender_name'] or '',
                'created_at': row['created_at'],
                'expires_at': row['expires_at']
            })
        conn.close()

        return create_response(200, 'success', {
            'notifications': notifications,
            'total': total,
            'unread_count': unread_count,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取通知失败: {e}")
        return create_response(500, '获取通知失败')


@notification_system_api.route('/api/notifications/<int:notification_id>', methods=['GET'])
@require_login
def get_notification_detail(notification_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT n.id, n.user_id, n.title, n.content, n.type, n.priority, 
                   n.read, n.read_at, n.link, n.sender_id, n.created_at, n.expires_at,
                   u.username as sender_name
            FROM notifications n
            LEFT JOIN users u ON n.sender_id = u.id
            WHERE n.id = ?
        ''', (notification_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '通知不存在')

        if role not in ['admin', 'super_admin'] and row['user_id'] != user_id:
            conn.close()
            return create_response(403, '无权查看')

        if row['read'] == 0:
            cursor.execute('UPDATE notifications SET read = 1, read_at = ? WHERE id = ?',
                         (datetime.now().isoformat(), notification_id))
            conn.commit()

        conn.close()
        return create_response(200, 'success', {
            'id': row['id'],
            'user_id': row['user_id'],
            'title': row['title'],
            'content': row['content'] or '',
            'type': row['type'],
            'priority': row['priority'],
            'read': row['read'] == 1,
            'read_at': row['read_at'],
            'link': row['link'] or '',
            'sender_id': row['sender_id'],
            'sender_name': row['sender_name'] or '',
            'created_at': row['created_at'],
            'expires_at': row['expires_at']
        })

    except Exception as e:
        logger.error(f"获取通知详情失败: {e}")
        return create_response(500, '获取通知详情失败')


@notification_system_api.route('/api/notifications', methods=['POST'])
@require_admin
def send_notification():
    try:
        data = request.get_json() or {}
        user_ids = data.get('user_ids', [])
        title = data.get('title', '')
        content = data.get('content', '')
        notification_type = data.get('type', 'info')
        priority = data.get('priority', 'normal')
        link = data.get('link', '')
        sender_id = session.get('user_id')

        if not user_ids or not title:
            return create_response(400, '缺少必要参数')

        conn = get_db_connection()
        cursor = conn.cursor()

        for user_id in user_ids:
            cursor.execute('''
                INSERT INTO notifications (user_id, title, content, type, priority, link, sender_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, title, content, notification_type, priority, link, sender_id))

        conn.commit()
        conn.close()

        return create_response(201, '通知发送成功', {'count': len(user_ids)})

    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        return create_response(500, '发送通知失败')


@notification_system_api.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@require_login
def delete_notification(notification_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if role not in ['admin', 'super_admin']:
            cursor.execute('SELECT user_id FROM notifications WHERE id = ?', (notification_id,))
            row = cursor.fetchone()
            if not row or row['user_id'] != user_id:
                conn.close()
                return create_response(403, '无权操作')

        cursor.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return create_response(404, '通知不存在')
        return create_response(200, '通知已删除')

    except Exception as e:
        logger.error(f"删除通知失败: {e}")
        return create_response(500, '删除通知失败')


@notification_system_api.route('/api/notifications/mark_read', methods=['POST'])
@require_login
def mark_notifications_read():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        notification_ids = data.get('notification_ids', [])

        conn = get_db_connection()
        cursor = conn.cursor()

        if notification_ids:
            placeholders = ','.join('?' * len(notification_ids))
            cursor.execute(f'''
                UPDATE notifications SET read = 1, read_at = ? 
                WHERE id IN ({placeholders}) AND user_id = ?
            ''', [datetime.now().isoformat()] + notification_ids + [user_id])
        else:
            cursor.execute('UPDATE notifications SET read = 1, read_at = ? WHERE user_id = ? AND read = 0',
                         (datetime.now().isoformat(), user_id))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return create_response(200, f'已标记 {affected} 条通知为已读')

    except Exception as e:
        logger.error(f"标记通知已读失败: {e}")
        return create_response(500, '标记通知已读失败')


@notification_system_api.route('/api/notifications/unread_count', methods=['GET'])
@require_login
def get_unread_count():
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = 0', (user_id,))
        count = cursor.fetchone()[0] or 0

        conn.close()
        return create_response(200, 'success', {'unread_count': count})

    except Exception as e:
        logger.error(f"获取未读数量失败: {e}")
        return create_response(500, '获取未读数量失败')


@notification_system_api.route('/api/notifications/settings', methods=['GET', 'PUT'])
@require_login
def notification_settings():
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('''
                SELECT email_notify, push_notify, system_notify, exam_notify, 
                       course_notify, homework_notify, community_notify, sound_enabled
                FROM notification_settings WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            if row:
                settings = {
                    'email_notify': row['email_notify'] == 1,
                    'push_notify': row['push_notify'] == 1,
                    'system_notify': row['system_notify'] == 1,
                    'exam_notify': row['exam_notify'] == 1,
                    'course_notify': row['course_notify'] == 1,
                    'homework_notify': row['homework_notify'] == 1,
                    'community_notify': row['community_notify'] == 1,
                    'sound_enabled': row['sound_enabled'] == 1
                }
            else:
                settings = {
                    'email_notify': True,
                    'push_notify': True,
                    'system_notify': True,
                    'exam_notify': True,
                    'course_notify': True,
                    'homework_notify': True,
                    'community_notify': True,
                    'sound_enabled': True
                }

            conn.close()
            return create_response(200, 'success', {'settings': settings})

        elif request.method == 'PUT':
            data = request.get_json() or {}

            cursor.execute('''
                INSERT OR REPLACE INTO notification_settings 
                (user_id, email_notify, push_notify, system_notify, exam_notify, 
                 course_notify, homework_notify, community_notify, sound_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                1 if data.get('email_notify', True) else 0,
                1 if data.get('push_notify', True) else 0,
                1 if data.get('system_notify', True) else 0,
                1 if data.get('exam_notify', True) else 0,
                1 if data.get('course_notify', True) else 0,
                1 if data.get('homework_notify', True) else 0,
                1 if data.get('community_notify', True) else 0,
                1 if data.get('sound_enabled', True) else 0
            ))

            conn.commit()
            conn.close()
            return create_response(200, '通知设置更新成功')

    except Exception as e:
        logger.error(f"通知设置操作失败: {e}")
        return create_response(500, '通知设置操作失败')


@notification_system_api.route('/api/notifications/templates', methods=['GET'])
@require_admin
def get_templates():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, template_code, name, title_template, content_template, type, priority FROM notification_templates')
        templates = []
        for row in cursor.fetchall():
            templates.append({
                'id': row['id'],
                'template_code': row['template_code'],
                'name': row['name'],
                'title_template': row['title_template'] or '',
                'content_template': row['content_template'] or '',
                'type': row['type'],
                'priority': row['priority']
            })
        conn.close()
        return create_response(200, 'success', {'templates': templates})

    except Exception as e:
        logger.error(f"获取通知模板失败: {e}")
        return create_response(500, '获取通知模板失败')


@notification_system_api.route('/api/notifications/templates', methods=['POST'])
@require_admin
def create_template():
    try:
        data = request.get_json() or {}
        template_code = data.get('template_code', '')
        name = data.get('name', '')
        title_template = data.get('title_template', '')
        content_template = data.get('content_template', '')
        template_type = data.get('type', 'info')
        priority = data.get('priority', 'normal')

        if not template_code or not name:
            return create_response(400, '模板代码和名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM notification_templates WHERE template_code = ?', (template_code,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '模板代码已存在')

        cursor.execute('''
            INSERT INTO notification_templates 
            (template_code, name, title_template, content_template, type, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_code, name, title_template, content_template, template_type, priority))

        conn.commit()
        conn.close()
        return create_response(201, '通知模板创建成功')

    except Exception as e:
        logger.error(f"创建通知模板失败: {e}")
        return create_response(500, '创建通知模板失败')


@notification_system_api.route('/api/notifications/email_queue', methods=['GET'])
@require_admin
def get_email_queue():
    try:
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if status:
            where_clauses.append('status = ?')
            params.append(status)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM email_queue {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, to_email, subject, content, template_code, status, 
                   attempts, max_attempts, scheduled_at, sent_at, error_message
            FROM email_queue
            {where_sql}
            ORDER BY scheduled_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        emails = []
        for row in cursor.fetchall():
            emails.append({
                'id': row['id'],
                'to_email': row['to_email'],
                'subject': row['subject'],
                'content': row['content'] or '',
                'template_code': row['template_code'] or '',
                'status': row['status'],
                'attempts': row['attempts'] or 0,
                'max_attempts': row['max_attempts'] or 3,
                'scheduled_at': row['scheduled_at'],
                'sent_at': row['sent_at'],
                'error_message': row['error_message'] or ''
            })
        conn.close()

        return create_response(200, 'success', {
            'emails': emails,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取邮件队列失败: {e}")
        return create_response(500, '获取邮件队列失败')