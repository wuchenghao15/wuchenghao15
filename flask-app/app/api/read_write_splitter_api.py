# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库读写分离管理API - 提供读写分离状态查询和管理接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

read_write_splitter_api = Blueprint('read_write_splitter_api', __name__)

# 全局读写分离实例
rw_splitter_instance = None

def init_rw_splitter():
    """初始化读写分离管理器"""
    global rw_splitter_instance
    if rw_splitter_instance is None:
        from app.utils.read_write_splitter import get_read_write_splitter
        rw_splitter_instance = get_read_write_splitter()
    return rw_splitter_instance

def get_splitter():
    """获取读写分离管理器实例"""
    if rw_splitter_instance is None:
        return init_rw_splitter()
    return rw_splitter_instance

@read_write_splitter_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'read-write-splitter-api'})

@read_write_splitter_api.route('/status')
def status():
    """获取读写分离状态"""
    splitter = get_splitter()
    return jsonify({
        'enabled': splitter.enabled,
        'force_master_read': splitter.force_master_read,
        'master_databases': splitter.master_databases,
        'slave_databases': splitter.slave_databases
    })

@read_write_splitter_api.route('/stats')
def stats():
    """获取统计信息"""
    splitter = get_splitter()
    return jsonify(splitter.get_stats())

@read_write_splitter_api.route('/stats/reset', methods=['POST'])
def reset_stats():
    """重置统计信息"""
    splitter = get_splitter()
    splitter.stats = {
        'read_operations': 0,
        'write_operations': 0,
        'read_from_master': 0,
        'read_from_slave': 0,
        'write_to_master': 0,
        'transaction_count': 0,
        'errors': 0
    }
    return jsonify({'success': True, 'message': '统计已重置'})

@read_write_splitter_api.route('/config')
def get_config():
    """获取配置信息"""
    splitter = get_splitter()
    return jsonify({
        'enabled': splitter.enabled,
        'force_master_read': splitter.force_master_read,
        'read_replication_lag': splitter.read_replication_lag,
        'master_databases': splitter.master_databases,
        'slave_databases': splitter.slave_databases,
        'database_dir': splitter.config.get('database_dir'),
        'connection_pool_size': splitter.config.get('connection_pool_size'),
        'connection_timeout': splitter.config.get('connection_timeout')
    })

@read_write_splitter_api.route('/config', methods=['POST'])
def update_config():
    """更新配置"""
    splitter = get_splitter()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '缺少配置数据'}), 400
    
    if 'enabled' in data:
        splitter.enabled = data['enabled']
    
    if 'force_master_read' in data:
        splitter.force_master_read = data['force_master_read']
    
    if 'read_replication_lag' in data:
        splitter.read_replication_lag = data['read_replication_lag']
    
    return jsonify({'success': True, 'message': '配置已更新'})

@read_write_splitter_api.route('/query', methods=['POST'])
def execute_query():
    """执行查询"""
    splitter = get_splitter()
    data = request.get_json()
    
    if not data or 'db_name' not in data or 'sql' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    db_name = data['db_name']
    sql = data['sql']
    params = data.get('params')
    force_master = data.get('force_master', False)
    
    operation = splitter._identify_operation(sql)
    
    try:
        if operation.value == 'read':
            result = splitter.query(db_name, sql, tuple(params) if params else None, force_master)
            rows = [dict(row) for row in result]
            return jsonify({
                'success': True,
                'operation': 'read',
                'result_count': len(rows),
                'results': rows[:10]  # 最多返回10条
            })
        else:
            cursor = splitter.execute(db_name, sql, tuple(params) if params else None, force_master)
            if cursor:
                return jsonify({
                    'success': True,
                    'operation': 'write',
                    'rowcount': cursor.rowcount if hasattr(cursor, 'rowcount') else 0
                })
            else:
                return jsonify({'success': False, 'error': '执行失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@read_write_splitter_api.route('/health')
def health():
    """健康检查"""
    splitter = get_splitter()
    stats = splitter.get_stats()
    
    return jsonify({
        'status': 'healthy' if stats['errors'] < 10 else 'degraded',
        'enabled': splitter.enabled,
        'active_connections': stats['active_connections'],
        'errors': stats['errors'],
        'timestamp': datetime.now().isoformat()
    })

@read_write_splitter_api.route('/databases')
def databases():
    """获取数据库列表"""
    splitter = get_splitter()
    return jsonify({
        'master': {
            'role': 'master',
            'description': '主数据库(写操作)',
            'databases': splitter.master_databases
        },
        'slave': {
            'role': 'slave',
            'description': '从数据库(读操作)',
            'databases': splitter.slave_databases
        }
    })

@read_write_splitter_api.route('/test')
def test():
    """测试读写分离"""
    splitter = get_splitter()
    
    results = {
        'test_read': False,
        'test_write': False,
        'read_routed_to_slave': False,
        'write_routed_to_master': False
    }
    
    # 测试读取
    try:
        result = splitter.query('questions', 'SELECT * FROM questions LIMIT 1')
        results['test_read'] = True
        stats = splitter.get_stats()
        results['read_routed_to_slave'] = (stats['read_from_slave'] > 0)
    except Exception:
        pass
    
    # 测试写入
    try:
        splitter.insert('users', 'users', {
            'username': f'test_rw_{int(time.time())}',
            'email': 'test@example.com',
            'password_hash': 'test'
        })
        results['test_write'] = True
        stats = splitter.get_stats()
        results['write_routed_to_master'] = (stats['write_to_master'] > 0)
    except Exception:
        pass
    
    return jsonify(results)

@read_write_splitter_api.route('/test/routing')
def test_routing():
    """测试路由逻辑"""
    splitter = get_splitter()
    
    test_cases = [
        ('SELECT * FROM users', 'read', 'should route to slave'),
        ('INSERT INTO users VALUES (...)', 'write', 'should route to master'),
        ('UPDATE users SET ...', 'write', 'should route to master'),
        ('DELETE FROM users', 'write', 'should route to master'),
        ('SHOW TABLES', 'read', 'should route to slave'),
        ('CREATE TABLE test (...)', 'write', 'should route to master')
    ]
    
    results = []
    for sql, expected, description in test_cases:
        operation = splitter._identify_operation(sql)
        results.append({
            'sql': sql[:50],
            'expected': expected,
            'detected': operation.value,
            'match': operation.value == expected,
            'description': description
        })
    
    return jsonify({'test_cases': results})

import time
