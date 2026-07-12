#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统参数管理API接口
根据《系统参数数据规范与操作规范》实现
"""

import logging
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session

logger = logging.getLogger('system_params_api')

system_params_bp = Blueprint('system_params', __name__, url_prefix='/api/system_params')

DATABASE_PATH = None

def set_database_path(db_path):
    global DATABASE_PATH
    DATABASE_PATH = db_path

def get_db_connection():
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_error_id():
    return str(uuid.uuid4())[:10]

def get_current_user():
    return session.get('username', 'system'), session.get('role', 'guest')

def validate_param_key(key):
    if not key or not isinstance(key, str):
        return False, '参数键不能为空'
    
    parts = key.split('.')
    if len(parts) < 2:
        return False, '参数键必须至少包含2个层级'
    
    for part in parts:
        if not part:
            return False, '参数键层级不能为空'
        if not part.islower():
            return False, '参数键层级必须使用小写字母'
        if not part.replace('_', '').isalnum():
            return False, '参数键层级只能包含小写字母、数字和下划线'
    
    if len(key) > 100:
        return False, '参数键长度不能超过100字符'
    
    return True, None

def validate_param_value(value, data_type):
    if value is None:
        return False, '参数值不能为空'
    
    try:
        if data_type == 'string':
            if not isinstance(value, str):
                value = str(value)
            if len(value) > 255:
                return False, '字符串参数值长度不能超过255字符'
        
        elif data_type == 'integer':
            if not isinstance(value, int):
                try:
                    value = int(value)
                except ValueError:
                    return False, '整数参数值必须为有效整数'
        
        elif data_type == 'float':
            if not isinstance(value, float):
                try:
                    value = float(value)
                except ValueError:
                    return False, '浮点数参数值必须为有效浮点数'
        
        elif data_type == 'boolean':
            if isinstance(value, bool):
                pass
            elif isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes')
            else:
                return False, '布尔参数值必须为true或false'
        
        elif data_type == 'json':
            if isinstance(value, str):
                json.loads(value)
            elif not isinstance(value, dict):
                return False, 'JSON参数值必须为有效JSON格式'
        
        elif data_type == 'list':
            if not isinstance(value, list):
                return False, '列表参数值必须为数组格式'
            if len(value) == 0:
                return False, '列表参数值不能为空'
        
        elif data_type == 'datetime':
            if isinstance(value, str):
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                return False, '日期时间参数值必须为ISO8601格式'
        
        return True, None
    except Exception as e:
        return False, str(e)

def log_param_change(operation, setting_key, old_value, new_value):
    operator, operator_role = get_current_user()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO param_change_logs 
            (log_id, operation, setting_key, old_value, new_value, operator, operator_role, timestamp, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            operation,
            setting_key,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None,
            operator,
            operator_role,
            datetime.now().isoformat(),
            request.remote_addr if request else 'unknown'
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"记录参数变更日志失败: {e}")

def create_response(code, message, data=None, error_id=None, error_type=None, suggestion=None, details=None):
    response = {
        'code': code,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    if data is not None:
        response['data'] = data
    if error_id:
        response['error_id'] = error_id
    if error_type:
        response['error_type'] = error_type
    if suggestion:
        response['suggestion'] = suggestion
    if details:
        response['details'] = details
    return jsonify(response)

@system_params_bp.route('/list', methods=['GET'])
def list_params():
    """列出所有参数"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        category = request.args.get('category')
        scope = request.args.get('scope')
        keyword = request.args.get('keyword')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = 'SELECT * FROM system_settings WHERE is_active = 1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        if scope:
            query += ' AND scope = ?'
            params.append(scope)
        if keyword:
            query += ' AND (setting_key LIKE ? OR description LIKE ?)'
            params.append('%' + keyword + '%')
            params.append('%' + keyword + '%')
        
        query += ' ORDER BY category, setting_key'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        total = len(rows)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_rows = rows[start:end]
        
        params_list = []
        for row in paginated_rows:
            params_list.append({
                'id': row['id'],
                'setting_key': row['setting_key'],
                'value': json.loads(row['value']) if row['value'] else None,
                'category': row['category'],
                'description': row['description'],
                'data_type': row['data_type'],
                'scope': row['scope'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        conn.close()
        
        return create_response(200, 'success', {
            'params': params_list,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 列出参数失败: {e} error_id={error_id}")
        return create_response(500, '获取参数列表失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/get', methods=['GET'])
def get_param():
    """获取单个参数"""
    try:
        key = request.args.get('key')
        
        if not key:
            return create_response(400, '参数键不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供参数键key')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_settings WHERE setting_key = ? AND is_active = 1', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return create_response(404, '参数不存在', None, generate_error_id(), 'RESOURCE_NOT_FOUND', '请检查参数键是否正确')
        
        return create_response(200, 'success', {
            'id': row['id'],
            'setting_key': row['setting_key'],
            'value': json.loads(row['value']) if row['value'] else None,
            'category': row['category'],
            'description': row['description'],
            'data_type': row['data_type'],
            'scope': row['scope'],
            'is_active': bool(row['is_active']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 获取参数失败: {e} error_id={error_id}")
        return create_response(500, '获取参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/set', methods=['POST'])
def set_param():
    """设置参数值"""
    try:
        data = request.get_json() or {}
        key = data.get('key')
        value = data.get('value')
        reason = data.get('reason', '')
        
        if not key:
            return create_response(400, '参数键不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供参数键key')
        
        valid, msg = validate_param_key(key)
        if not valid:
            return create_response(400, msg, None, generate_error_id(), 'VALIDATION_ERROR', '请检查参数键格式')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_settings WHERE setting_key = ? AND is_active = 1', (key,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return create_response(404, '参数不存在', None, generate_error_id(), 'RESOURCE_NOT_FOUND', '请先创建该参数')
        
        data_type = row['data_type']
        valid, msg = validate_param_value(value, data_type)
        if not valid:
            conn.close()
            return create_response(400, msg, None, generate_error_id(), 'VALIDATION_ERROR', '请检查参数值格式')
        
        old_value = json.loads(row['value']) if row['value'] else None
        
        new_value_json = json.dumps(value)
        cursor.execute('''
            UPDATE system_settings 
            SET value = ?, updated_at = ? 
            WHERE setting_key = ?
        ''', (new_value_json, datetime.now().isoformat(), key))
        conn.commit()
        
        log_param_change('update', key, old_value, value)
        
        conn.close()
        
        return create_response(200, 'success', {
            'key': key,
            'value': value,
            'updated_at': datetime.now().isoformat()
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 设置参数失败: {e} error_id={error_id}")
        return create_response(500, '设置参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/create', methods=['POST'])
def create_param():
    """创建新参数"""
    try:
        data = request.get_json() or {}
        key = data.get('key')
        value = data.get('value')
        category = data.get('category', 'general')
        description = data.get('description', '')
        data_type = data.get('data_type', 'string')
        scope = data.get('scope', 'global')
        
        if not key:
            return create_response(400, '参数键不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供参数键key')
        
        if not data_type:
            return create_response(400, '数据类型不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供数据类型')
        
        valid, msg = validate_param_key(key)
        if not valid:
            return create_response(400, msg, None, generate_error_id(), 'VALIDATION_ERROR', '请检查参数键格式')
        
        valid, msg = validate_param_value(value, data_type)
        if not valid:
            return create_response(400, msg, None, generate_error_id(), 'VALIDATION_ERROR', '请检查参数值格式')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM system_settings WHERE setting_key = ?', (key,))
        if cursor.fetchone():
            conn.close()
            return create_response(409, '参数已存在', None, generate_error_id(), 'CONFLICT_ERROR', '该参数键已被使用')
        
        value_json = json.dumps(value)
        cursor.execute('''
            INSERT INTO system_settings 
            (setting_key, value, category, description, data_type, scope, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (key, value_json, category, description, data_type, scope, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        
        log_param_change('create', key, None, value)
        
        conn.close()
        
        return create_response(201, '参数创建成功', {
            'key': key,
            'value': value,
            'category': category,
            'description': description,
            'data_type': data_type,
            'scope': scope,
            'created_at': datetime.now().isoformat()
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 创建参数失败: {e} error_id={error_id}")
        return create_response(500, '创建参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/delete', methods=['DELETE'])
def delete_param():
    """删除参数"""
    try:
        data = request.get_json() or {}
        key = data.get('key')
        
        if not key:
            return create_response(400, '参数键不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供参数键key')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_settings WHERE setting_key = ? AND is_active = 1', (key,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return create_response(404, '参数不存在', None, generate_error_id(), 'RESOURCE_NOT_FOUND', '请检查参数键是否正确')
        
        old_value = json.loads(row['value']) if row['value'] else None
        
        cursor.execute('UPDATE system_settings SET is_active = 0, updated_at = ? WHERE setting_key = ?', 
                      (datetime.now().isoformat(), key))
        conn.commit()
        
        log_param_change('delete', key, old_value, None)
        
        conn.close()
        
        return create_response(200, '参数删除成功')
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 删除参数失败: {e} error_id={error_id}")
        return create_response(500, '删除参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/reset', methods=['POST'])
def reset_param():
    """重置参数为默认值"""
    try:
        data = request.get_json() or {}
        key = data.get('key')
        
        if not key:
            return create_response(400, '参数键不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供参数键key')
        
        default_values = {
            'system.general.name': 'MTSCOS AI',
            'system.general.version': '7.9.0',
            'security.auth.session_timeout': 1800,
            'security.password.min_length': 8,
            'security.password.max_length': 32,
            'database.connection.pool_size': 10,
            'database.connection.timeout': 30,
            'ai.worker.auto_scaling': True,
            'exam.paper.duration_minutes': 90,
            'monitor.metrics.cpu_threshold': 90.0,
            'monitor.metrics.memory_threshold': 90.0,
            'cache.redis.ttl_hours': 24,
            'logging.level': 'INFO'
        }
        
        if key not in default_values:
            return create_response(404, '该参数没有默认值', None, generate_error_id(), 'RESOURCE_NOT_FOUND', '只有预设参数支持重置')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_settings WHERE setting_key = ? AND is_active = 1', (key,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return create_response(404, '参数不存在', None, generate_error_id(), 'RESOURCE_NOT_FOUND', '请检查参数键是否正确')
        
        old_value = json.loads(row['value']) if row['value'] else None
        new_value = default_values[key]
        
        data_type = row['data_type']
        valid, msg = validate_param_value(new_value, data_type)
        if not valid:
            conn.close()
            return create_response(400, msg, None, generate_error_id(), 'VALIDATION_ERROR', '默认值格式验证失败')
        
        value_json = json.dumps(new_value)
        cursor.execute('''
            UPDATE system_settings 
            SET value = ?, updated_at = ? 
            WHERE setting_key = ?
        ''', (value_json, datetime.now().isoformat(), key))
        conn.commit()
        
        log_param_change('reset', key, old_value, new_value)
        
        conn.close()
        
        return create_response(200, '参数已重置为默认值', {
            'key': key,
            'value': new_value
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 重置参数失败: {e} error_id={error_id}")
        return create_response(500, '重置参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/batch', methods=['POST'])
def batch_operation():
    """批量操作"""
    try:
        data = request.get_json() or {}
        operation = data.get('operation')
        params = data.get('params', [])
        
        if not operation:
            return create_response(400, '操作类型不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请指定操作类型')
        
        if not params or not isinstance(params, list):
            return create_response(400, '参数列表不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供参数列表')
        
        results = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for param_data in params:
            key = param_data.get('key')
            if not key:
                results.append({'key': None, 'success': False, 'message': '参数键不能为空'})
                continue
            
            try:
                if operation == 'set':
                    value = param_data.get('value')
                    cursor.execute('SELECT data_type FROM system_settings WHERE setting_key = ? AND is_active = 1', (key,))
                    row = cursor.fetchone()
                    if not row:
                        results.append({'key': key, 'success': False, 'message': '参数不存在'})
                        continue
                    
                    data_type = row['data_type']
                    valid, msg = validate_param_value(value, data_type)
                    if not valid:
                        results.append({'key': key, 'success': False, 'message': msg})
                        continue
                    
                    value_json = json.dumps(value)
                    cursor.execute('UPDATE system_settings SET value = ?, updated_at = ? WHERE setting_key = ?',
                                  (value_json, datetime.now().isoformat(), key))
                    results.append({'key': key, 'success': True, 'message': '设置成功'})
                
                elif operation == 'delete':
                    cursor.execute('UPDATE system_settings SET is_active = 0, updated_at = ? WHERE setting_key = ?',
                                  (datetime.now().isoformat(), key))
                    results.append({'key': key, 'success': True, 'message': '删除成功'})
                
                elif operation == 'reset':
                    cursor.execute('SELECT data_type FROM system_settings WHERE setting_key = ? AND is_active = 1', (key,))
                    row = cursor.fetchone()
                    if not row:
                        results.append({'key': key, 'success': False, 'message': '参数不存在'})
                        continue
                    
                    default_values = {
                        'system.general.name': 'MTSCOS AI',
                        'system.general.version': '7.9.0',
                        'security.auth.session_timeout': 1800,
                        'security.password.min_length': 8
                    }
                    
                    if key not in default_values:
                        results.append({'key': key, 'success': False, 'message': '没有默认值'})
                        continue
                    
                    value_json = json.dumps(default_values[key])
                    cursor.execute('UPDATE system_settings SET value = ?, updated_at = ? WHERE setting_key = ?',
                                  (value_json, datetime.now().isoformat(), key))
                    results.append({'key': key, 'success': True, 'message': '重置成功'})
                
                else:
                    results.append({'key': key, 'success': False, 'message': '未知操作类型'})
            
            except Exception as e:
                results.append({'key': key, 'success': False, 'message': str(e)})
        
        conn.commit()
        conn.close()
        
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count
        
        return create_response(200, '批量操作完成', {
            'results': results,
            'success_count': success_count,
            'fail_count': fail_count
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 批量操作失败: {e} error_id={error_id}")
        return create_response(500, '批量操作失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/logs', methods=['GET'])
def get_change_logs():
    """查询变更日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        setting_key = request.args.get('setting_key')
        operator = request.args.get('operator')
        operation = request.args.get('operation')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = 'SELECT * FROM param_change_logs'
        params = []
        
        conditions = []
        if setting_key:
            conditions.append('setting_key = ?')
            params.append(setting_key)
        if operator:
            conditions.append('operator = ?')
            params.append(operator)
        if operation:
            conditions.append('operation = ?')
            params.append(operation)
        if start_time:
            conditions.append('timestamp >= ?')
            params.append(start_time)
        if end_time:
            conditions.append('timestamp <= ?')
            params.append(end_time)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        total = len(rows)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_rows = rows[start:end]
        
        logs = []
        for row in paginated_rows:
            logs.append({
                'log_id': row['log_id'],
                'operation': row['operation'],
                'setting_key': row['setting_key'],
                'old_value': json.loads(row['old_value']) if row['old_value'] else None,
                'new_value': json.loads(row['new_value']) if row['new_value'] else None,
                'operator': row['operator'],
                'operator_role': row['operator_role'],
                'timestamp': row['timestamp'],
                'ip_address': row['ip_address']
            })
        
        conn.close()
        
        return create_response(200, 'success', {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 获取变更日志失败: {e} error_id={error_id}")
        return create_response(500, '获取变更日志失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/backup', methods=['POST'])
def backup_params():
    """备份参数"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_settings WHERE is_active = 1')
        rows = cursor.fetchall()
        
        backup_data = []
        for row in rows:
            backup_data.append({
                'id': row['id'],
                'setting_key': row['setting_key'],
                'value': json.loads(row['value']) if row['value'] else None,
                'category': row['category'],
                'description': row['description'],
                'data_type': row['data_type'],
                'scope': row['scope'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        backup_id = str(uuid.uuid4())
        backup_json = json.dumps(backup_data)
        
        cursor.execute('''
            INSERT INTO param_backups 
            (backup_id, backup_data, backup_time, operator)
            VALUES (?, ?, ?, ?)
        ''', (backup_id, backup_json, datetime.now().isoformat(), get_current_user()[0]))
        conn.commit()
        conn.close()
        
        return create_response(200, '参数备份成功', {
            'backup_id': backup_id,
            'backup_time': datetime.now().isoformat(),
            'param_count': len(backup_data)
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 备份参数失败: {e} error_id={error_id}")
        return create_response(500, '备份参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/restore', methods=['POST'])
def restore_params():
    """恢复参数"""
    try:
        data = request.get_json() or {}
        backup_id = data.get('backup_id')
        
        if not backup_id:
            return create_response(400, '备份ID不能为空', None, generate_error_id(), 'VALIDATION_ERROR', '请提供备份ID')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT backup_data FROM param_backups WHERE backup_id = ?', (backup_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return create_response(404, '备份不存在', None, generate_error_id(), 'RESOURCE_NOT_FOUND', '请检查备份ID是否正确')
        
        backup_data = json.loads(row['backup_data'])
        
        restored_count = 0
        for param in backup_data:
            try:
                key = param['setting_key']
                value_json = json.dumps(param['value'])
                
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings 
                    (id, setting_key, value, category, description, data_type, scope, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    param['id'],
                    key,
                    value_json,
                    param['category'],
                    param['description'],
                    param['data_type'],
                    param['scope'],
                    1,
                    param['created_at'],
                    datetime.now().isoformat()
                ))
                restored_count += 1
            except Exception as e:
                logger.warning(f"恢复参数 {param.get('setting_key')} 失败: {e}")
        
        conn.commit()
        conn.close()
        
        return create_response(200, '参数恢复成功', {
            'backup_id': backup_id,
            'restored_count': restored_count
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 恢复参数失败: {e} error_id={error_id}")
        return create_response(500, '恢复参数失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取参数分类"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM system_settings WHERE is_active = 1 ORDER BY category')
        rows = cursor.fetchall()
        
        categories = [row['category'] for row in rows]
        
        conn.close()
        
        return create_response(200, 'success', {
            'categories': categories,
            'total': len(categories)
        })
    
    except Exception as e:
        error_id = generate_error_id()
        logger.error(f"[系统参数] 获取分类失败: {e} error_id={error_id}")
        return create_response(500, '获取分类失败', None, error_id, 'SYSTEM_ERROR', '请稍后重试')

@system_params_bp.route('/scopes', methods=['GET'])
def get_scopes():
    """获取作用域列表"""
    scopes = [
        {'value': 'global', 'name': '全局', 'description': '对所有用户生效'},
        {'value': 'user', 'name': '用户', 'description': '针对特定用户'},
        {'value': 'session', 'name': '会话', 'description': '仅当前会话有效'},
        {'value': 'system', 'name': '系统', 'description': '仅系统内部使用'}
    ]
    
    return create_response(200, 'success', {'scopes': scopes})

@system_params_bp.route('/data_types', methods=['GET'])
def get_data_types():
    """获取数据类型列表"""
    data_types = [
        {'value': 'string', 'name': '字符串', 'description': '文本字符串，最大255字符'},
        {'value': 'integer', 'name': '整数', 'description': '整数数值'},
        {'value': 'float', 'name': '浮点数', 'description': '浮点数值'},
        {'value': 'boolean', 'name': '布尔', 'description': 'true或false'},
        {'value': 'json', 'name': 'JSON', 'description': 'JSON对象'},
        {'value': 'list', 'name': '列表', 'description': '数组列表'},
        {'value': 'datetime', 'name': '日期时间', 'description': 'ISO8601格式'}
    ]
    
    return create_response(200, 'success', {'data_types': data_types})