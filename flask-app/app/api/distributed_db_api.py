#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式数据库管理API - 提供分库分表、数据分片管理接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

distributed_db_api = Blueprint('distributed_db_api', __name__)

# 全局分布式数据库实例
db_instance = None

def init_db():
    """初始化分布式数据库"""
    global db_instance
    if db_instance is None:
        from app.utils.distributed_db_manager import get_distributed_db_manager
        db_instance = get_distributed_db_manager()
    return db_instance

def get_db():
    """获取分布式数据库实例"""
    if db_instance is None:
        return init_db()
    return db_instance

@distributed_db_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'distributed-db-api'})

@distributed_db_api.route('/status')
def status():
    """获取分布式数据库状态"""
    db = get_db()
    return jsonify({
        'enabled': db.config.get('enabled', True),
        'sharding_strategy': db.sharding_strategy.value,
        'shard_count': db.shard_count,
        'replica_count': db.config.get('replica_count', 2),
        'consistency_level': db.config.get('consistency_level', 'eventual'),
        'timestamp': datetime.now().isoformat()
    })

@distributed_db_api.route('/stats')
def stats():
    """获取统计信息"""
    db = get_db()
    return jsonify(db.get_stats())

@distributed_db_api.route('/shards')
def shards():
    """获取分片配置"""
    db = get_db()
    return jsonify(db.shards)

@distributed_db_api.route('/shards/<table_name>')
def table_shards(table_name):
    """获取表的分片信息"""
    db = get_db()
    return jsonify(db.shards.get(table_name, {}))

@distributed_db_api.route('/insert', methods=['POST'])
def insert():
    """插入数据"""
    db = get_db()
    data = request.get_json()
    
    if not data or 'table' not in data or 'data' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    table_name = data['table']
    insert_data = data['data']
    shard_key_value = data.get('shard_key_value')
    
    success = db.insert(table_name, insert_data, shard_key_value)
    
    return jsonify({'success': success, 'message': '插入成功' if success else '插入失败'})

@distributed_db_api.route('/query', methods=['POST'])
def query():
    """查询数据"""
    db = get_db()
    data = request.get_json()
    
    if not data or 'table' not in data or 'sql' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    table_name = data['table']
    sql = data['sql']
    params = data.get('params')
    shard_key_value = data.get('shard_key_value')
    
    result = db.query(table_name, sql, tuple(params) if params else None, shard_key_value)
    rows = [dict(row) for row in result]
    
    return jsonify({
        'success': True,
        'count': len(rows),
        'results': rows[:100]
    })

@distributed_db_api.route('/update', methods=['POST'])
def update():
    """更新数据"""
    db = get_db()
    data = request.get_json()
    
    if not data or 'table' not in data or 'data' not in data or 'where' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    table_name = data['table']
    update_data = data['data']
    where = data['where']
    where_params = data.get('where_params', [])
    shard_key_value = data.get('shard_key_value')
    
    rowcount = db.update(table_name, update_data, where, tuple(where_params), shard_key_value)
    
    return jsonify({'success': True, 'updated_rows': rowcount})

@distributed_db_api.route('/delete', methods=['POST'])
def delete():
    """删除数据"""
    db = get_db()
    data = request.get_json()
    
    if not data or 'table' not in data or 'where' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    table_name = data['table']
    where = data['where']
    where_params = data.get('where_params', [])
    shard_key_value = data.get('shard_key_value')
    
    rowcount = db.delete(table_name, where, tuple(where_params), shard_key_value)
    
    return jsonify({'success': True, 'deleted_rows': rowcount})

@distributed_db_api.route('/config')
def get_config():
    """获取配置"""
    db = get_db()
    return jsonify({
        'enabled': db.config.get('enabled'),
        'sharding_strategy': db.config.get('sharding_strategy'),
        'shard_count': db.config.get('shard_count'),
        'replica_count': db.config.get('replica_count'),
        'database_dir': db.config.get('database_dir'),
        'consistency_level': db.config.get('consistency_level'),
        'distributed_transactions': db.config.get('distributed_transactions'),
        'cross_shard_query': db.config.get('cross_shard_query')
    })

@distributed_db_api.route('/config', methods=['POST'])
def update_config():
    """更新配置"""
    db = get_db()
    data = request.get_json()
    
    if 'sharding_strategy' in data:
        db.sharding_strategy = data['sharding_strategy']
    
    if 'shard_count' in data:
        db.shard_count = data['shard_count']
    
    return jsonify({'success': True, 'message': '配置更新成功'})

@distributed_db_api.route('/health')
def health():
    """健康检查"""
    db = get_db()
    stats = db.get_stats()
    
    return jsonify({
        'status': 'healthy' if stats['errors'] < 10 else 'degraded',
        'shards': stats['tables'],
        'queries': stats['queries'],
        'errors': stats['errors'],
        'timestamp': datetime.now().isoformat()
    })

@distributed_db_api.route('/test')
def test():
    """测试分布式数据库"""
    db = get_db()
    
    results = {
        'insert_test': False,
        'query_test': False,
        'shard_distribution': False
    }
    
    # 测试插入
    try:
        db.insert('users', {
            'id': 999,
            'username': 'test_distributed',
            'email': 'test@distributed.com',
            'password_hash': 'test'
        })
        results['insert_test'] = True
    except Exception:
        pass
    
    # 测试查询
    try:
        result = db.query('users', 'SELECT * FROM users WHERE id = ?', (999,), shard_key_value=999)
        results['query_test'] = len(result) > 0
    except Exception:
        pass
    
    # 测试分片分布
    try:
        stats = db.get_stats()
        results['shard_distribution'] = len(stats.get('data_distribution', {})) > 0
    except Exception:
        pass
    
    return jsonify(results)

@distributed_db_api.route('/data_distribution')
def data_distribution():
    """获取数据分布统计"""
    db = get_db()
    stats = db.get_stats()
    return jsonify({
        'distribution': stats.get('data_distribution', {}),
        'total_queries': stats.get('queries', 0),
        'cross_shard_queries': stats.get('cross_shard_queries', 0)
    })
