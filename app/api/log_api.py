#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

log_api = Bluelogger.info('log_api', __name__)


def get_log_files():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Logs')
    files = []
    
    for root, dirs, filenames in os.walk(log_dir):
        for filename in filenames:
            if filename.endswith(('.log', '.txt')):
                filepath = os.path.join(root, filename)
                try:
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'size': size,
                        'modified_time': datetime.fromtimestamp(mtime).isoformat(),
                        'relative_path': os.path.relpath(filepath, log_dir)
                    })
                except:
                    pass
    
    return sorted(files, key=lambda x: x['modified_time'], reverse=True)


def read_log_file(filepath, lines=100, offset=0):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        
        total_lines = len(all_lines)
        start = max(0, total_lines - lines - offset)
        end = max(0, total_lines - offset)
        
        content = ''.join(all_lines[start:end])
        
        return {
            'success': True,
            'content': content,
            'total_lines': total_lines,
            'lines_read': end - start,
            'offset': offset
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_error_logs_from_db(limit=50, offset=0):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, error_type, error_message, status, created_at
            FROM error_logs
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'error_type': row[1],
                'error_message': row[2],
                'status': row[3],
                'created_at': row[4]
            })
        
        cursor.execute('SELECT COUNT(*) FROM error_logs')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'data': logs,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_maintenance_logs(limit=50, offset=0):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, operation_type, target, result, details, timestamp
            FROM system_maintenance_logs
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'operation_type': row[1],
                'target': row[2],
                'result': row[3],
                'details': row[4],
                'timestamp': row[5]
            })
        
        cursor.execute('SELECT COUNT(*) FROM system_maintenance_logs')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'data': logs,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@log_api.route('/api/logs/files', methods=['GET'])
@require_admin
def list_log_files():
    files = get_log_files()
    return jsonify({
        'success': True,
        'data': files,
        'count': len(files),
        'timestamp': datetime.now().isoformat()
    })


@log_api.route('/api/logs/file/<path:filename>', methods=['GET'])
@require_admin
def get_log_file_content(filename):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Logs')
    filepath = os.path.join(log_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    
    lines = request.args.get('lines', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    result = read_log_file(filepath, lines, offset)
    if result['success']:
        return jsonify({
            'success': True,
            'data': result,
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify(result), 500


@log_api.route('/api/logs/errors', methods=['GET'])
@require_admin
def get_errors():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    result = get_error_logs_from_db(limit, offset)
    return jsonify(result)


@log_api.route('/api/logs/errors/<int:error_id>', methods=['GET'])
@require_admin
def get_error_detail(error_id):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM error_logs WHERE id = ?', (error_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return jsonify({
                'success': True,
                'data': {
                    'id': row[0],
                    'error_type': row[1],
                    'error_message': row[2],
                    'stack_trace': row[3],
                    'request_path': row[4],
                    'request_method': row[5],
                    'user_id': row[6],
                    'user_role': row[7],
                    'client_ip': row[8],
                    'status': row[9],
                    'created_at': row[10],
                    'resolved_at': row[11]
                }
            })
        else:
            return jsonify({'success': False, 'error': '错误日志不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@log_api.route('/api/logs/maintenance', methods=['GET'])
@require_admin
def get_maintenance():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    result = get_maintenance_logs(limit, offset)
    return jsonify(result)


@log_api.route('/api/logs/repair', methods=['GET'])
@require_admin
def get_repair_logs():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fix_id, file_path, error_type, status, confidence, executed_at
            FROM auto_fix_code_records
            ORDER BY executed_at DESC
            LIMIT 50
        ''')
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'fix_id': row[0],
                'file_path': row[1],
                'error_type': row[2],
                'status': row[3],
                'confidence': row[4],
                'executed_at': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@log_api.route('/api/logs/clean', methods=['POST'])
@require_admin
def clean_logs():
    data = request.get_json() or {}
    log_type = data.get('type')
    
    if log_type == 'error':
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM error_logs WHERE status = "resolved"')
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'已清理 {deleted} 条已解决的错误日志',
                'deleted': deleted
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif log_type == 'maintenance':
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM system_maintenance_logs')
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'已清理 {deleted} 条维护日志',
                'deleted': deleted
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif log_type == 'repair':
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM auto_fix_code_records')
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'已清理 {deleted} 条修复记录',
                'deleted': deleted
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:
        return jsonify({'success': False, 'error': '无效的日志类型'}), 400