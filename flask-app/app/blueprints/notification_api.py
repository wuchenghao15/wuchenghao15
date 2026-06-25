import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
通知系统API - Flask Blueprint
"""

from flask import Blueprint, request, jsonify, session
import json
import uuid
from datetime import datetime
import sqlite3
import os
import sys

notification_api = Blueprint('notification_api', __name__, url_prefix='/api/notifications')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db():
    return sqlite3.connect(DATABASE_PATH)


def log_notification_action(notification_id, action, user_id, details=None):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notification_logs (id, notification_id, action, user_id, details) VALUES (?, ?, ?, ?, ?)', (str(uuid.uuid4()), notification_id, action, user_id, json.dumps(details) if details else None))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.info(f"日志记录失败: {e}")


@notification_api.route('/', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id', 1)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status = request.args.get('status', 'all')
    channel = request.args.get('channel', 'all')
    
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    query = 'SELECT * FROM notifications WHERE recipient_id = ?'
    params = [user_id]
    
    if status != 'all':
        query += ' AND status = ?'
        params.append(status)
    
    if channel != 'all':
        query += ' AND type LIKE ?'
        params.append('%' + channel + '%')
    
    query += ' ORDER BY priority ASC, created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    notifications = []
    for row in cursor.fetchall():
        notifications.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'type': row[3],
            'sender_id': row[4],
            'recipient_id': row[5],
            'priority': row[7],
            'status': row[8],
            'created_at': row[9],
            'metadata': json.loads(row[12]) if row[12] else {}
        })
    
    cursor.execute('SELECT COUNT(*) FROM notifications WHERE recipient_id = ?', (user_id,))
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': notifications,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })


@notification_api.route('/<notification_id>', methods=['GET'])
def get_notification(notification_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM notifications WHERE id = ?', (notification_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'success': False, 'message': '通知不存在'}), 404
    
    cursor.execute('SELECT * FROM notification_read WHERE notification_id = ?', (notification_id,))
    read_info = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'type': row[3],
            'sender_id': row[4],
            'recipient_id': row[5],
            'priority': row[7],
            'status': row[8],
            'created_at': row[9],
            'expires_at': row[11],
            'metadata': json.loads(row[12]) if row[12] else {},
            'read_at': read_info[2] if read_info else None
        }
    })


@notification_api.route('/', methods=['POST'])
def send_notification():
    data = request.json
    user_id = session.get('user_id', 1)
    
    notification_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO notifications (id, title, content, type, sender_id, recipient_id, priority, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (notification_id, data.get('title', ''), data.get('content', ''), data.get('type', 'system_info'), user_id, data.get('recipient_id'), data.get('priority', 2), now, now, json.dumps(data.get('metadata', {}))))
    
    log_notification_action(notification_id, 'created', user_id, {'type': data.get('type')})
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'notification_id': notification_id,
        'message': '通知发送成功'
    })


@notification_api.route('/<notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    user_id = session.get('user_id', 1)
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE notifications SET status = "read", updated_at = ? WHERE id = ?', (now, notification_id))
    
    cursor.execute('SELECT id FROM notification_read WHERE notification_id = ? AND user_id = ?', (notification_id, user_id))
    if cursor.fetchone():
        cursor.execute('UPDATE notification_read SET read_at = ? WHERE notification_id = ? AND user_id = ?', (now, notification_id, user_id))
    else:
        cursor.execute('INSERT INTO notification_read (id, notification_id, user_id, read_at) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), notification_id, user_id, now))
    
    log_notification_action(notification_id, 'read', user_id)
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '已标记为已读'})


@notification_api.route('/batch/read', methods=['POST'])
def mark_batch_read():
    user_id = session.get('user_id', 1)
    data = request.json
    notification_ids = data.get('ids', [])
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    for nid in notification_ids:
        cursor.execute('UPDATE notifications SET status = "read", updated_at = ? WHERE id = ?', (now, nid))
        
        cursor.execute('SELECT id FROM notification_read WHERE notification_id = ? AND user_id = ?', (nid, user_id))
        if cursor.fetchone():
            cursor.execute('UPDATE notification_read SET read_at = ? WHERE notification_id = ? AND user_id = ?', (now, nid, user_id))
        else:
            cursor.execute('INSERT INTO notification_read (id, notification_id, user_id, read_at) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), nid, user_id, now))
    
    log_notification_action(','.join(notification_ids), 'batch_read', user_id)
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '已标记 ' + str(len(notification_ids)) + ' 条通知为已读'})


@notification_api.route('/<notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    user_id = session.get('user_id', 1)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
    cursor.execute('DELETE FROM notification_read WHERE notification_id = ?', (notification_id,))
    
    log_notification_action(notification_id, 'deleted', user_id)
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '通知已删除'})


@notification_api.route('/unread/count', methods=['GET'])
def get_unread_count():
    user_id = session.get('user_id', 1)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND status = "unread"', (user_id,))
    count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({'success': True, 'count': count})


@notification_api.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    user_id = session.get('user_id', 1)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM notification_subscriptions WHERE user_id = ?', (user_id,))
    subscriptions = []
    for row in cursor.fetchall():
        subscriptions.append({
            'id': row[0],
            'channel_type': row[2],
            'enabled': row[3] == 1,
            'settings': json.loads(row[4]) if row[4] else {},
            'created_at': row[5]
        })
    
    conn.close()
    
    return jsonify({'success': True, 'data': subscriptions})


@notification_api.route('/subscriptions', methods=['POST'])
def update_subscription():
    user_id = session.get('user_id', 1)
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM notification_subscriptions WHERE user_id = ? AND channel_type = ?', (user_id, data.get('channel_type')))
    
    if cursor.fetchone():
        cursor.execute('UPDATE notification_subscriptions SET enabled = ?, settings = ?, updated_at = ? WHERE user_id = ? AND channel_type = ?', (1 if data.get('enabled') else 0, json.dumps(data.get('settings', {})), datetime.now().isoformat(), user_id, data.get('channel_type')))
    else:
        cursor.execute('INSERT INTO notification_subscriptions (id, user_id, channel_type, enabled, settings) VALUES (?, ?, ?, ?, ?)', (str(uuid.uuid4()), user_id, data.get('channel_type'), 1 if data.get('enabled') else 0, json.dumps(data.get('settings', {}))))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '订阅设置已更新'})


@notification_api.route('/channels', methods=['GET'])
def get_channels():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM notification_channels WHERE is_active = 1')
    channels = []
    for row in cursor.fetchall():
        channels.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'notification_types': json.loads(row[3]) if row[3] else []
        })
    
    conn.close()
    
    return jsonify({'success': True, 'data': channels})


@notification_api.route('/broadcast', methods=['POST'])
def send_broadcast():
    data = request.json
    user_id = session.get('user_id', 1)
    
    if session.get('role') not in ['admin', 'super_admin']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    notification_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE is_active = 1')
    users = cursor.fetchall()
    
    for user in users:
        nid = str(uuid.uuid4())
        cursor.execute('INSERT INTO notifications (id, title, content, type, sender_id, recipient_id, priority, created_at, updated_at) VALUES (?, ?, ?, "broadcast", ?, ?, ?, ?, ?)', (nid, data.get('title', ''), data.get('content', ''), user_id, user[0], 2, now, now))
    
    log_notification_action(notification_id, 'broadcast', user_id, {'recipient_count': len(users)})
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '广播已发送给 ' + str(len(users)) + ' 位用户'})
