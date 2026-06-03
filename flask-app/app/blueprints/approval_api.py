# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
审批流程API - Flask Blueprint
"""

from flask import Blueprint, request, jsonify, session
import json
import uuid
from datetime import datetime
import sqlite3
import os

approval_api = Blueprint('approval_api', __name__, url_prefix='/api/approval')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db():
    return sqlite3.connect(DATABASE_PATH)


@approval_api.route('/request', methods=['POST'])
def create_request():
    data = request.json
    user_id = session.get('user_id', 1)
    
    request_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO approval_requests (id, type, title, description, requester_id, status, priority, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (request_id, data.get('type', 'exam_pause'), data.get('title', ''), data.get('description', ''), user_id, 'pending', data.get('priority', 'normal'), now, now)
    )
    
    cursor.execute(
        'INSERT INTO approval_flows (id, request_id, step, assignee_role, action) VALUES (?, ?, ?, ?, ?)',
        (str(uuid.uuid4()), request_id, 1, 'teacher', 'pending')
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'request_id': request_id,
        'message': '审批请求已创建'
    })


@approval_api.route('/requests', methods=['GET'])
def get_requests():
    status = request.args.get('status', 'all')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if status == 'all':
        cursor.execute('SELECT * FROM approval_requests ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC', (status,))
    
    requests = []
    for row in cursor.fetchall():
        requests.append({
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'requester_id': row[4],
            'status': row[5],
            'priority': row[6],
            'created_at': row[7]
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': requests
    })


@approval_api.route('/request/<request_id>', methods=['GET'])
def get_request(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM approval_requests WHERE id = ?', (request_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'success': False, 'message': '审批不存在'}), 404
    
    cursor.execute('SELECT * FROM approval_flows WHERE request_id = ? ORDER BY step', (request_id,))
    flows = []
    for flow_row in cursor.fetchall():
        flows.append({
            'step': flow_row[2],
            'assignee_role': flow_row[3],
            'action': flow_row[5],
            'comment': flow_row[6],
            'created_at': flow_row[7]
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'requester_id': row[4],
            'status': row[5],
            'priority': row[6],
            'created_at': row[7],
            'flows': flows
        }
    })


@approval_api.route('/request/<request_id>/action', methods=['POST'])
def approve_request(request_id):
    data = request.json
    action = data.get('action')
    comment = data.get('comment', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE approval_requests SET status = ?, updated_at = ? WHERE id = ?', 
                  (action, datetime.now().isoformat(), request_id))
    
    cursor.execute('UPDATE approval_flows SET action = ?, comment = ?, created_at = ? WHERE request_id = ? AND action = "pending"',
                  (action, comment, datetime.now().isoformat(), request_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '审批已处理'
    })


@approval_api.route('/types', methods=['GET'])
def get_types():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT rule_value FROM approval_rules WHERE rule_code = "approval_types"')
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return jsonify({'success': True, 'data': json.loads(row[0])})
    return jsonify({'success': False, 'data': []})


@approval_api.route('/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT status, COUNT(*) FROM approval_requests GROUP BY status')
    stats = {}
    for row in cursor.fetchall():
        stats[row[0]] = row[1]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': stats
    })


@approval_api.route('/rules', methods=['GET'])
def get_rules():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT rule_code, rule_name, rule_description, rule_type, rule_value FROM approval_rules WHERE is_active = 1 ORDER BY priority')
    rules = []
    for row in cursor.fetchall():
        rules.append({
            'code': row[0],
            'name': row[1],
            'description': row[2],
            'type': row[3],
            'value': row[4]
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': rules
    })


@approval_api.route('/notifications', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id', 1)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM approval_notifications WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    notifications = []
    for row in cursor.fetchall():
        notifications.append({
            'id': row[0],
            'request_id': row[1],
            'type': row[2],
            'message': row[3],
            'is_read': row[4],
            'created_at': row[5]
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': notifications
    })
