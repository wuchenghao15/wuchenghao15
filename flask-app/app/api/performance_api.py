# -*- coding: utf-8 -*-
"""
数据库性能API
提供数据库状态查询、性能监控、索引管理等接口
"""

from flask import Blueprint, jsonify, request
from app.services.db_performance_service import db_performance_service

performance_api = Blueprint('performance_api', __name__)


@performance_api.route('/api/performance/db/status', methods=['GET'])
def get_db_status():
    """获取所有数据库状态"""
    status = db_performance_service.get_database_status()
    return jsonify({
        'success': True,
        'data': status
    })


@performance_api.route('/api/performance/db/query-stats', methods=['GET'])
def get_query_stats():
    """获取查询统计"""
    db_name = request.args.get('db_name')
    stats = db_performance_service.get_query_stats(db_name)
    return jsonify({
        'success': True,
        'data': stats
    })


@performance_api.route('/api/performance/db/slow-queries', methods=['GET'])
def get_slow_queries():
    """获取慢查询列表"""
    db_name = request.args.get('db_name')
    limit = int(request.args.get('limit', 20))
    queries = db_performance_service.get_slow_queries(db_name, limit)
    return jsonify({
        'success': True,
        'data': queries
    })


@performance_api.route('/api/performance/db/analyze', methods=['POST'])
def analyze_table():
    """分析表结构"""
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    
    if not db_name or not table_name:
        return jsonify({
            'success': False,
            'message': '缺少参数: db_name 或 table_name'
        })
    
    result = db_performance_service.analyze_table(db_name, table_name)
    return jsonify({
        'success': True,
        'data': result
    })


@performance_api.route('/api/performance/db/optimize', methods=['POST'])
def optimize_database():
    """优化数据库"""
    data = request.get_json()
    db_name = data.get('db_name')
    
    if not db_name:
        return jsonify({
            'success': False,
            'message': '缺少参数: db_name'
        })
    
    result = db_performance_service.optimize_database(db_name)
    return jsonify({
        'success': True,
        'data': result
    })


@performance_api.route('/api/performance/db/index/create', methods=['POST'])
def create_index():
    """创建索引"""
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    columns = data.get('columns', [])
    index_name = data.get('index_name')
    
    if not db_name or not table_name or not columns:
        return jsonify({
            'success': False,
            'message': '缺少参数: db_name、table_name 或 columns'
        })
    
    result = db_performance_service.create_index(db_name, table_name, columns, index_name)
    return jsonify(result)


@performance_api.route('/api/performance/db/index/drop', methods=['POST'])
def drop_index():
    """删除索引"""
    data = request.get_json()
    db_name = data.get('db_name')
    index_name = data.get('index_name')
    
    if not db_name or not index_name:
        return jsonify({
            'success': False,
            'message': '缺少参数: db_name 或 index_name'
        })
    
    result = db_performance_service.drop_index(db_name, index_name)
    return jsonify(result)


@performance_api.route('/api/performance/db/stats/reset', methods=['POST'])
def reset_stats():
    """重置统计数据"""
    db_performance_service.reset_stats()
    return jsonify({
        'success': True,
        'message': '统计数据已重置'
    })


@performance_api.route('/api/performance/db/execute', methods=['POST'])
def execute_query():
    """执行SQL查询并返回执行时间"""
    data = request.get_json()
    db_name = data.get('db_name')
    sql = data.get('sql')
    params = data.get('params', [])
    
    if not db_name or not sql:
        return jsonify({
            'success': False,
            'message': '缺少参数: db_name 或 sql'
        })
    
    rows, execution_time = db_performance_service.execute_with_timing(db_name, sql, tuple(params))
    return jsonify({
        'success': True,
        'data': rows,
        'execution_time': execution_time
    })
