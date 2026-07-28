#!/usr/bin/env python3
import os
import sqlite3
import json
import csv
import zipfile
import io
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from app.middlewares.access_control import require_login, require_admin

export_api = Bluelogger.info('export_api', __name__)


def _get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def export_table_to_csv(table_name):
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        
        return {'success': True, 'content': output.getvalue(), 'columns': columns, 'row_count': len(rows)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def export_table_to_json(table_name):
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        
        conn.close()
        
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        return {'success': True, 'data': data, 'columns': columns, 'row_count': len(data)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def export_multiple_tables(tables, format='json'):
    result = {}
    
    for table_name in tables:
        if format == 'json':
            table_result = export_table_to_json(table_name)
        else:
            table_result = export_table_to_csv(table_name)
        
        if table_result['success']:
            result[table_name] = table_result
        else:
            result[table_name] = {'error': table_result['error']}
    
    return {'success': True, 'data': result, 'format': format}


def get_available_tables():
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        
        tables = []
        for row in cursor.fetchall():
            tables.append(row[0])
        
        conn.close()
        
        return {'success': True, 'data': tables}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@export_api.route('/api/export/tables', methods=['GET'])
@require_admin
def list_tables():
    result = get_available_tables()
    return jsonify(result)


@export_api.route('/api/export/table/<table_name>', methods=['GET'])
@require_admin
def export_single_table(table_name):
    export_format = request.args.get('format', 'json')
    
    if export_format == 'csv':
        result = export_table_to_csv(table_name)
        if result['success']:
            return send_file(
                io.BytesIO(result['content'].encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:
            return jsonify(result), 500
    else:
        result = export_table_to_json(table_name)
        return jsonify(result)


@export_api.route('/api/export/tables/batch', methods=['POST'])
@require_admin
def export_multiple_tables_api():
    data = request.get_json() or {}
    tables = data.get('tables', [])
    export_format = data.get('format', 'json')
    compress = data.get('compress', False)
    
    if not tables:
        return jsonify({'success': False, 'error': '请指定要导出的表'}), 400
    
    if export_format == 'csv' and compress:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for table_name in tables:
                result = export_table_to_csv(table_name)
                if result['success']:
                    zip_file.writestr(f'{table_name}.csv', result['content'])
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'tables_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )
    elif export_format == 'csv':
        result = export_multiple_tables(tables, 'csv')
        return jsonify(result)
    else:
        result = export_multiple_tables(tables, 'json')
        return jsonify(result)


@export_api.route('/api/export/users', methods=['GET'])
@require_admin
def export_users():
    export_format = request.args.get('format', 'json')
    
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, education_system, created_at, last_login
            FROM users
            ORDER BY created_at
        ''')
        
        columns = ['id', 'username', 'email', 'role', 'education_system', 'created_at', 'last_login']
        rows = cursor.fetchall()
        
        conn.close()
        
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return jsonify({
                'success': True,
                'data': data,
                'count': len(data)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@export_api.route('/api/export/activity', methods=['GET'])
@require_admin
def export_activity():
    export_format = request.args.get('format', 'json')
    
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, username, user_role, activity_type, activity_detail, 
                   ip_address, timestamp, success, error_message
            FROM user_activity
            ORDER BY timestamp DESC
        ''')
        
        columns = ['id', 'user_id', 'username', 'user_role', 'activity_type', 'activity_detail',
                   'ip_address', 'timestamp', 'success', 'error_message']
        rows = cursor.fetchall()
        
        conn.close()
        
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'activity_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return jsonify({
                'success': True,
                'data': data,
                'count': len(data)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@export_api.route('/api/export/errors', methods=['GET'])
@require_admin
def export_errors():
    export_format = request.args.get('format', 'json')
    
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, error_type, error_message, stack_trace, request_path, request_method,
                   user_id, user_role, client_ip, status, created_at, resolved_at
            FROM error_logs
            ORDER BY created_at DESC
        ''')
        
        columns = ['id', 'error_type', 'error_message', 'stack_trace', 'request_path', 'request_method',
                   'user_id', 'user_role', 'client_ip', 'status', 'created_at', 'resolved_at']
        rows = cursor.fetchall()
        
        conn.close()
        
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'errors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return jsonify({
                'success': True,
                'data': data,
                'count': len(data)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@export_api.route('/api/export/ai_employees', methods=['GET'])
@require_admin
def export_ai_employees():
    export_format = request.args.get('format', 'json')
    
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent_id, agent_name, agent_type, status, config, 
                   created_at, updated_at, last_heartbeat
            FROM ai_employees
            ORDER BY created_at
        ''')
        
        columns = ['id', 'agent_id', 'agent_name', 'agent_type', 'status', 'config',
                   'created_at', 'updated_at', 'last_heartbeat']
        rows = cursor.fetchall()
        
        conn.close()
        
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'ai_employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        else:
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            return jsonify({
                'success': True,
                'data': data,
                'count': len(data)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@export_api.route('/api/export/full', methods=['GET'])
@require_admin
def export_full_database():
    db_path = _get_db_path()
    
    if not os.path.exists(db_path):
        return jsonify({'success': False, 'error': '数据库文件不存在'}), 404
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(db_path, f'mtscos_db_{timestamp}.sqlite')
        
        result = get_available_tables()
        if result['success']:
            for table in result['data']:
                csv_result = export_table_to_csv(table)
                if csv_result['success']:
                    zip_file.writestr(f'tables/{table}.csv', csv_result['content'])
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'mtscos_full_export_{timestamp}.zip'
    )