#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

activity_api = Bluelogger.info('activity_api', __name__)


def _get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def _ensure_activity_table():
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                user_role TEXT,
                activity_type TEXT NOT NULL,
                activity_detail TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        pass


_ensure_activity_table()


def log_activity(user_id, username, user_role, activity_type, activity_detail='', ip_address='', user_agent='',
success=True, error_message=''):
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_activity (user_id, username, user_role, activity_type, 
                                     activity_detail, ip_address, user_agent, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, user_role, activity_type, activity_detail, ip_address, user_agent, success,
        error_message))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        return False


def get_user_activity(user_id, limit=50, offset=0):
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, activity_type, activity_detail, ip_address, timestamp, success, error_message
            FROM user_activity
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'id': row[0],
                'activity_type': row[1],
                'activity_detail': row[2],
                'ip_address': row[3],
                'timestamp': row[4],
                'success': row[5],
                'error_message': row[6]
            })
        
        cursor.execute('SELECT COUNT(*) FROM user_activity WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'data': activities,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_all_activity(limit=50, offset=0, activity_type=None, user_role=None):
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, user_id, username, user_role, activity_type, activity_detail, 
                   ip_address, timestamp, success, error_message
            FROM user_activity
        '''
        
        params = []
        
        conditions = []
        if activity_type:
            conditions.append('activity_type = ?')
            params.append(activity_type)
        if user_role:
            conditions.append('user_role = ?')
            params.append(user_role)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'user_role': row[3],
                'activity_type': row[4],
                'activity_detail': row[5],
                'ip_address': row[6],
                'timestamp': row[7],
                'success': row[8],
                'error_message': row[9]
            })
        
        count_query = 'SELECT COUNT(*) FROM user_activity'
        if conditions:
            count_query += ' WHERE ' + ' AND '.join(conditions)
        
        cursor.execute(count_query, params[:-2])
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'data': activities,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_activity_summary():
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_activity')
        total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT activity_type, COUNT(*) as count
            FROM user_activity
            GROUP BY activity_type
            ORDER BY count DESC
        ''')
        
        by_type = []
        for row in cursor.fetchall():
            by_type.append({
                'activity_type': row[0],
                'count': row[1]
            })
        
        cursor.execute('''
            SELECT user_role, COUNT(*) as count
            FROM user_activity
            GROUP BY user_role
            ORDER BY count DESC
        ''')
        
        by_role = []
        for row in cursor.fetchall():
            by_role.append({
                'user_role': row[0],
                'count': row[1]
            })
        
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM user_activity
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        ''')
        
        by_date = []
        for row in cursor.fetchall():
            by_date.append({
                'date': row[0],
                'count': row[1]
            })
        
        conn.close()
        
        return {
            'success': True,
            'data': {
                'total_activities': total,
                'by_type': by_type,
                'by_role': by_role,
                'by_date_last_7_days': by_date
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@activity_api.route('/api/activity/log', methods=['POST'])
@require_login
def log_activity_api():
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    username = data.get('username')
    user_role = data.get('user_role')
    activity_type = data.get('activity_type')
    activity_detail = data.get('activity_detail', '')
    
    if not activity_type:
        return jsonify({'success': False, 'error': 'activity_type不能为空'}), 400
    
    ip_address = request.remote_addr
    user_agent = request.user_agent.string
    
    success = log_activity(user_id, username, user_role, activity_type, activity_detail, ip_address, user_agent)
    
    if success:
        return jsonify({'success': True, 'message': '活动记录成功'})
    else:
        return jsonify({'success': False, 'error': '记录失败'}), 500


@activity_api.route('/api/activity/user/<user_id>', methods=['GET'])
@require_admin
def get_user_activity_api(user_id):
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    result = get_user_activity(user_id, limit, offset)
    return jsonify(result)


@activity_api.route('/api/activity/all', methods=['GET'])
@require_admin
def get_all_activity_api():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    activity_type = request.args.get('type')
    user_role = request.args.get('role')
    
    result = get_all_activity(limit, offset, activity_type, user_role)
    return jsonify(result)


@activity_api.route('/api/activity/summary', methods=['GET'])
@require_admin
def get_activity_summary_api():
    result = get_activity_summary()
    return jsonify(result)


@activity_api.route('/api/activity/clean', methods=['POST'])
@require_admin
def clean_activity():
    data = request.get_json() or {}
    days = data.get('days', 30)
    
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_activity
            WHERE timestamp < DATETIME('now', '-' || ? || ' days')
        ''', (days,))
        
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'已清理 {deleted} 条{days}天前的活动记录',
            'deleted': deleted
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@activity_api.route('/api/activity/types', methods=['GET'])
@require_admin
def get_activity_types():
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT activity_type FROM user_activity ORDER BY activity_type')
        
        types = []
        for row in cursor.fetchall():
            types.append(row[0])
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': types,
            'count': len(types)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500