#!/usr/bin/env python3
"""
系统优化API路由 - 提供系统优化和功能拓展接口
"""

from flask import Blueprint, jsonify, request
from ..services.system_optimization_service import (
    init_system_optimizer,
    create_system_optimizer_employee,
    get_system_optimizer_employee,
    get_current_version,
    upgrade_version,
    run_auto_optimization,
    expand_features_based_on_existing,
    get_planned_features,
    get_implemented_features,
    get_optimization_history,
    get_performance_metrics,
    update_performance_metric,
    mark_feature_implemented,
    optimize_database,
    optimize_api_performance,
    optimize_security
)

optimizer_bp = Blueprint('optimizer', __name__, url_prefix='/api/optimizer')


@optimizer_bp.route('/employee', methods=['GET'])
def employee_info():
    """获取系统优化AI员工信息"""
    employee = get_system_optimizer_employee()
    if employee:
        return jsonify({
            'status': 'success',
            'data': employee
        })
    return jsonify({
        'status': 'error',
        'message': '系统优化员工不存在'
    }), 404


@optimizer_bp.route('/version', methods=['GET'])
def version_info():
    """获取当前系统版本"""
    return jsonify({
        'status': 'success',
        'data': {
            'version': get_current_version()
        }
    })


@optimizer_bp.route('/version/upgrade', methods=['POST'])
def upgrade_version_endpoint():
    """升级系统版本"""
    data = request.get_json() or {}
    new_version = data.get('version', '5.0.0')
    new_codename = data.get('codename', '智能系统优化版')
    release_notes = data.get('release_notes', '')
    
    if not release_notes:
        release_notes = f"升级到{new_version}版本，新增系统优化AI员工，支持自动优化和功能拓展"
    
    version = upgrade_version(new_version, new_codename, release_notes)
    
    return jsonify({
        'status': 'success',
        'message': f'系统版本已升级到 {version}',
        'data': {
            'version': version,
            'codename': new_codename,
            'release_notes': release_notes
        }
    })


@optimizer_bp.route('/optimize', methods=['POST'])
def optimize_all():
    """运行自动优化"""
    results = run_auto_optimization()
    
    return jsonify({
        'status': 'success',
        'data': results
    })


@optimizer_bp.route('/optimize/database', methods=['POST'])
def optimize_db():
    """优化数据库"""
    opt_id, opts = optimize_database()
    return jsonify({
        'status': 'success',
        'optimization_id': opt_id,
        'optimizations': opts
    })


@optimizer_bp.route('/optimize/performance', methods=['POST'])
def optimize_perf():
    """优化性能"""
    opt_id, opts = optimize_api_performance()
    return jsonify({
        'status': 'success',
        'optimization_id': opt_id,
        'optimizations': opts
    })


@optimizer_bp.route('/optimize/security', methods=['POST'])
def optimize_sec():
    """优化安全性"""
    opt_id, opts = optimize_security()
    return jsonify({
        'status': 'success',
        'optimization_id': opt_id,
        'optimizations': opts
    })


@optimizer_bp.route('/features/expand', methods=['POST'])
def expand_features():
    """根据现有功能拓展新功能"""
    results = expand_features_based_on_existing()
    
    return jsonify({
        'status': 'success',
        'data': results,
        'count': len(results),
        'message': f'已规划{len(results)}个新功能'
    })


@optimizer_bp.route('/features/planned', methods=['GET'])
def planned_features():
    """获取计划中的功能"""
    features = get_planned_features()
    return jsonify({
        'status': 'success',
        'data': features,
        'count': len(features)
    })


@optimizer_bp.route('/features/implemented', methods=['GET'])
def implemented_features():
    """获取已实现的功能"""
    features = get_implemented_features()
    return jsonify({
        'status': 'success',
        'data': features,
        'count': len(features)
    })


@optimizer_bp.route('/features/<feature_id>/implement', methods=['POST'])
def implement_feature(feature_id):
    """标记功能已实现"""
    data = request.get_json() or {}
    api_endpoints = data.get('api_endpoints')
    database_tables = data.get('database_tables')
    files_created = data.get('files_created')
    
    mark_feature_implemented(feature_id, api_endpoints, database_tables, files_created)
    
    return jsonify({
        'status': 'success',
        'message': '功能已标记为已实现',
        'feature_id': feature_id
    })


@optimizer_bp.route('/history', methods=['GET'])
def optimization_history():
    """获取优化历史"""
    limit = int(request.args.get('limit', 50))
    history = get_optimization_history(limit)
    return jsonify({
        'status': 'success',
        'data': history,
        'count': len(history)
    })


@optimizer_bp.route('/performance', methods=['GET'])
def performance_metrics():
    """获取性能指标"""
    metrics = get_performance_metrics()
    return jsonify({
        'status': 'success',
        'data': metrics,
        'count': len(metrics)
    })


@optimizer_bp.route('/performance/update', methods=['POST'])
def update_performance():
    """更新性能指标"""
    data = request.get_json() or {}
    metric_name = data.get('metric_name')
    metric_type = data.get('metric_type')
    current_value = data.get('current_value')
    baseline_value = data.get('baseline_value')
    
    if not metric_name or not metric_type:
        return jsonify({
            'status': 'error',
            'message': '缺少必要参数'
        }), 400
    
    success = update_performance_metric(metric_name, metric_type, current_value, baseline_value)
    return jsonify({
        'status': 'success' if success else 'error',
        'message': '性能指标已更新' if success else '更新失败'
    })
