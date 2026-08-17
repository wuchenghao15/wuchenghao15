#!/usr/bin/env python3
"""
规则管理API
提供系统规则的增删改查接口
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import sqlite3
import os

rule_api = Bluelogger.info('rule_api', __name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

def _get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DATABASE_PATH)

def _rows_to_dicts(rows):
    """将数据库行转换为字典"""
    return [{
        'id': row[0],
        'rule_code': row[1],
        'rule_name': row[2],
        'rule_value': row[3],
        'rule_type': row[4],
        'description': row[5],
        'is_active': bool(row[6]),
        'created_at': row[7],
        'updated_at': row[8],
        'priority': row[9],
        'effective_from': row[10],
        'expires_at': row[11],
        'rule_group': row[12],
        'metadata': json.loads(row[13]) if row[13] else {}
    } for row in rows]

@rule_api.route('/api/rules', methods=['GET'])
def get_rules():
    """获取规则列表"""
    try:
        rule_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = _get_connection()
        cursor = conn.cursor()
        
        if rule_type:
            cursor.execute('''
                SELECT * FROM system_rules WHERE rule_type = ? AND is_active = 1 
                ORDER BY rule_code LIMIT ? OFFSET ?
            ''', (rule_type, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM system_rules WHERE is_active = 1 
                ORDER BY rule_code LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': _rows_to_dicts(rows),
            'total': len(rows)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rule_api.route('/api/rules/<rule_code>', methods=['GET'])
def get_rule(rule_code):
    """获取单个规则"""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_rules WHERE rule_code = ?', (rule_code,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': '规则不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': _rows_to_dicts([row])[0]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rule_api.route('/api/rules', methods=['POST'])
def add_rule():
    """添加新规则"""
    try:
        data = request.get_json()
        
        required_fields = ['rule_code', 'rule_name', 'rule_value']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        rule_code = data['rule_code']
        rule_name = data['rule_name']
        rule_value = data['rule_value']
        rule_type = data.get('rule_type', 'system')
        description = data.get('description', '')
        priority = data.get('priority', 'medium')
        
        conn = _get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO system_rules 
                (rule_code, rule_name, rule_value, rule_type, description, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (rule_code, rule_name, rule_value, rule_type, description, priority))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '规则添加成功',
                'rule_code': rule_code
            }), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': '规则代码已存在'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rule_api.route('/api/rules/<rule_code>', methods=['PUT'])
def update_rule(rule_code):
    """更新规则"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '缺少更新数据'}), 400
        
        conn = _get_connection()
        cursor = conn.cursor()
        
        update_fields = []
        update_values = []
        
        if 'rule_value' in data:
            update_fields.append('rule_value = ?')
            update_values.append(data['rule_value'])
        
        if 'rule_name' in data:
            update_fields.append('rule_name = ?')
            update_values.append(data['rule_name'])
        
        if 'description' in data:
            update_fields.append('description = ?')
            update_values.append(data['description'])
        
        if 'rule_type' in data:
            update_fields.append('rule_type = ?')
            update_values.append(data['rule_type'])
        
        if 'priority' in data:
            update_fields.append('priority = ?')
            update_values.append(data['priority'])
        
        if 'is_active' in data:
            update_fields.append('is_active = ?')
            update_values.append(int(data['is_active']))
        
        if not update_fields:
            conn.close()
            return jsonify({'success': False, 'error': '没有需要更新的字段'}), 400
        
        update_fields.append('updated_at = ?')
        update_values.append(datetime.now().isoformat())
        update_values.append(rule_code)
        
        cursor.execute(f'''
            UPDATE system_rules SET {', '.join(update_fields)} WHERE rule_code = ?
        ''', update_values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if not success:
            return jsonify({'success': False, 'error': '规则不存在'}), 404
        
        return jsonify({
            'success': True,
            'message': '规则更新成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rule_api.route('/api/rules/<rule_code>', methods=['DELETE'])
def delete_rule(rule_code):
    """删除规则"""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM system_rules WHERE rule_code = ?', (rule_code,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if not success:
            return jsonify({'success': False, 'error': '规则不存在'}), 404
        
        return jsonify({
            'success': True,
            'message': '规则删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rule_api.route('/api/rules/summary', methods=['GET'])
def get_rules_summary():
    """获取规则汇总统计"""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_rules WHERE is_active = 1')
        total_rules = cursor.fetchone()[0]
        
        cursor.execute('SELECT rule_type, COUNT(*) FROM system_rules WHERE is_active = 1 GROUP BY rule_type')
        rules_by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('SELECT priority, COUNT(*) FROM system_rules WHERE is_active = 1 GROUP BY priority')
        rules_by_priority = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_rules': total_rules,
                'rules_by_type': rules_by_type,
                'rules_by_priority': rules_by_priority
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rule_api.route('/api/rules/execution-logs', methods=['GET'])
def get_execution_logs():
    """获取规则执行日志"""
    try:
        rule_code = request.args.get('rule_code')
        limit = int(request.args.get('limit', 100))
        
        conn = _get_connection()
        cursor = conn.cursor()
        
        if rule_code:
            cursor.execute('''
                SELECT * FROM rule_execution_logs WHERE rule_code = ? ORDER BY execution_time DESC LIMIT ?
            ''', (rule_code, limit))
        else:
            cursor.execute('''
                SELECT * FROM rule_execution_logs ORDER BY execution_time DESC LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'rule_code': row[1],
                'execution_time': row[2],
                'result': row[3],
                'error_message': row[4],
                'executed_by': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            })
        
        return jsonify({
            'success': True,
            'data': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500