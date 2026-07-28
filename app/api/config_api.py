#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

config_api = Bluelogger.info('config_api', __name__)


def get_all_system_rules():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rule_code, rule_name, rule_value, rule_type, description, is_active, created_at, updated_at
            FROM system_rules
            ORDER BY rule_type, rule_code
        ''')
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'rule_code': row[0],
                'rule_name': row[1],
                'rule_value': row[2],
                'rule_type': row[3],
                'description': row[4],
                'is_active': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        conn.close()
        
        return {'success': True, 'data': rules}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_rule_by_code(rule_code):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rule_code, rule_name, rule_value, rule_type, description, is_active
            FROM system_rules
            WHERE rule_code = ?
        ''', (rule_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'success': True,
                'data': {
                    'rule_code': row[0],
                    'rule_name': row[1],
                    'rule_value': row[2],
                    'rule_type': row[3],
                    'description': row[4],
                    'is_active': row[5]
                }
            }
        else:
            return {'success': False, 'error': '规则不存在'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_rule(rule_code, rule_value, is_active=None):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if is_active is not None:
            cursor.execute('''
                UPDATE system_rules
                SET rule_value = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE rule_code = ?
            ''', (rule_value, is_active, rule_code))
        else:
            cursor.execute('''
                UPDATE system_rules
                SET rule_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE rule_code = ?
            ''', (rule_value, rule_code))
        
        conn.commit()
        updated = cursor.rowcount
        conn.close()
        
        if updated > 0:
            return {'success': True, 'message': '规则更新成功'}
        else:
            return {'success': False, 'error': '规则不存在'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def add_rule(rule_code, rule_name, rule_value, rule_type='system', description=''):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_rules (rule_code, rule_name, rule_value, rule_type, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (rule_code, rule_name, rule_value, rule_type, description))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': '规则添加成功'}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': '规则代码已存在'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_rule(rule_code):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM system_rules WHERE rule_code = ?', (rule_code,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        
        if deleted > 0:
            return {'success': True, 'message': '规则删除成功'}
        else:
            return {'success': False, 'error': '规则不存在'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@config_api.route('/api/config/rules', methods=['GET'])
@require_admin
def list_rules():
    rule_type = request.args.get('type')
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if rule_type:
            cursor.execute('''
                SELECT rule_code, rule_name, rule_value, rule_type, description, is_active
                FROM system_rules
                WHERE rule_type = ?
                ORDER BY rule_code
            ''', (rule_type,))
        else:
            cursor.execute('''
                SELECT rule_code, rule_name, rule_value, rule_type, description, is_active
                FROM system_rules
                ORDER BY rule_type, rule_code
            ''')
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'rule_code': row[0],
                'rule_name': row[1],
                'rule_value': row[2],
                'rule_type': row[3],
                'description': row[4],
                'is_active': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': rules,
            'count': len(rules),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_api.route('/api/config/rules/<rule_code>', methods=['GET'])
@require_admin
def get_rule(rule_code):
    result = get_rule_by_code(rule_code)
    return jsonify(result)


@config_api.route('/api/config/rules/<rule_code>', methods=['PUT'])
@require_admin
def update_rule_api(rule_code):
    data = request.get_json() or {}
    rule_value = data.get('rule_value')
    is_active = data.get('is_active')
    
    if rule_value is None:
        return jsonify({'success': False, 'error': 'rule_value不能为空'}), 400
    
    result = update_rule(rule_code, rule_value, is_active)
    return jsonify(result)


@config_api.route('/api/config/rules', methods=['POST'])
@require_admin
def add_rule_api():
    data = request.get_json() or {}
    
    rule_code = data.get('rule_code')
    rule_name = data.get('rule_name')
    rule_value = data.get('rule_value')
    rule_type = data.get('rule_type', 'system')
    description = data.get('description', '')
    
    if not rule_code or not rule_name or rule_value is None:
        return jsonify({'success': False, 'error': 'rule_code, rule_name, rule_value不能为空'}), 400
    
    result = add_rule(rule_code, rule_name, rule_value, rule_type, description)
    return jsonify(result)


@config_api.route('/api/config/rules/<rule_code>', methods=['DELETE'])
@require_admin
def delete_rule_api(rule_code):
    result = delete_rule(rule_code)
    return jsonify(result)


@config_api.route('/api/config/env', methods=['GET'])
@require_admin
def get_env_vars():
    env_vars = {}
    for key, value in os.environ.items():
        if not key.startswith('SECRET') and not key.startswith('PASSWORD') and not key.startswith('TOKEN'):
            env_vars[key] = value
    
    return jsonify({
        'success': True,
        'data': env_vars,
        'timestamp': datetime.now().isoformat()
    })


@config_api.route('/api/config/app', methods=['GET'])
@require_admin
def get_app_config():
    config = {
        'version': '1.7.0',
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'debug': os.environ.get('DEBUG', 'False').lower() == 'true',
        'database': {
            'path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        },
        'features': {
            'auto_repair': True,
            'auto_sync': True,
            'auto_backup': True,
            'ai_employees': True
        }
    }
    
    return jsonify({
        'success': True,
        'data': config,
        'timestamp': datetime.now().isoformat()
    })


@config_api.route('/api/config/validate', methods=['POST'])
@require_admin
def validate_config():
    data = request.get_json() or {}
    
    errors = []
    
    if 'SECRET_KEY' not in os.environ:
        errors.append('SECRET_KEY 环境变量未设置')
    elif len(os.environ['SECRET_KEY']) < 16:
        errors.append('SECRET_KEY 长度不足16位')
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    if not os.path.exists(db_path):
        errors.append('数据库文件不存在')
    
    if errors:
        return jsonify({
            'success': False,
            'errors': errors,
            'message': '配置验证失败'
        })
    else:
        return jsonify({
            'success': True,
            'message': '配置验证通过'
        })