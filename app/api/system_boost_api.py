#!/usr/bin/env python3
"""
系统强化与上报API
暴露输配AI员工、上报数据库、500轮强化引擎、页面功能覆盖率等功能
"""

import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

system_boost_api = Blueprint('system_boost_api', __name__)


def _get_boost_engine():
    from app.services.system_boost_engine import system_boost_engine
    return system_boost_engine


def _get_report_service():
    from app.services.system_report_service import system_report_service
    return system_report_service


def _get_dispatcher():
    from ai_engines.dispatch_ai_employee import create_dispatch_ai_employee
    return create_dispatch_ai_employee()


# ============ 系统强化引擎 ============

@system_boost_api.route('/api/system/boost/run', methods=['POST'])
@require_admin
def run_boost():
    """启动N轮系统强化（默认500轮）"""
    data = request.get_json() or {}
    rounds = min(int(data.get('rounds', 500)), 1000)
    engine = _get_boost_engine()
    result = engine.run_boost(rounds=rounds)
    # 移除round_details避免响应过大
    result.pop('round_details', None)
    return jsonify(result)


@system_boost_api.route('/api/system/boost/history', methods=['GET'])
@require_login
def boost_history():
    """获取强化历史记录"""
    limit = min(int(request.args.get('limit', 50)), 500)
    engine = _get_boost_engine()
    history = engine.get_boost_history(limit=limit)
    return jsonify({'success': True, 'count': len(history), 'data': history})


@system_boost_api.route('/api/system/boost/summary', methods=['GET'])
@require_login
def boost_summary():
    """按类别汇总强化统计"""
    engine = _get_boost_engine()
    summary = engine.get_boost_summary_by_category()
    snapshot = engine._get_system_snapshot()
    return jsonify({'success': True, 'by_category': summary, 'system_snapshot': snapshot})


@system_boost_api.route('/api/system/boost/snapshot', methods=['GET'])
@require_login
def system_snapshot():
    """获取系统快照"""
    engine = _get_boost_engine()
    snapshot = engine._get_system_snapshot()
    return jsonify({'success': True, 'data': snapshot, 'timestamp': datetime.now().isoformat()})


# ============ 输配AI员工 ============

@system_boost_api.route('/api/system/dispatch/execute', methods=['POST'])
@require_login
def dispatch_execute():
    """执行输配任务"""
    data = request.get_json() or {}
    dispatcher = _get_dispatcher()
    result = dispatcher.execute_task(data)
    return jsonify(result)


@system_boost_api.route('/api/system/dispatch/stats', methods=['GET'])
@require_login
def dispatch_stats():
    """获取输配统计"""
    dispatcher = _get_dispatcher()
    stats = dispatcher.get_dispatch_stats()
    return jsonify({'success': True, 'data': stats})


@system_boost_api.route('/api/system/dispatch/rules', methods=['GET'])
@require_login
def dispatch_rules():
    """获取路由规则"""
    dispatcher = _get_dispatcher()
    rules = dispatcher.list_routing_rules()
    return jsonify({'success': True, 'count': len(rules), 'data': rules})


@system_boost_api.route('/api/system/dispatch/rules', methods=['POST'])
@require_admin
def add_dispatch_rule():
    """添加路由规则"""
    data = request.get_json() or {}
    task_type = data.get('task_type')
    target_role = data.get('target_role')
    weight = int(data.get('weight', 50))
    if not task_type or not target_role:
        return jsonify({'success': False, 'error': 'task_type和target_role不能为空'}), 400
    dispatcher = _get_dispatcher()
    ok = dispatcher.add_routing_rule(task_type, target_role, weight)
    return jsonify({'success': ok})


# ============ 上报数据库 ============

@system_boost_api.route('/api/system/report/submit', methods=['POST'])
@require_login
def submit_report():
    """提交上报记录"""
    data = request.get_json() or {}
    svc = _get_report_service()
    result = svc.submit_report(
        report_type=data.get('report_type', 'general'),
        module=data.get('module', 'unknown'),
        severity=data.get('severity', 'info'),
        title=data.get('title', ''),
        content=data.get('content', ''),
        metadata=data.get('metadata', {}),
        reported_by=data.get('reported_by', 'user')
    )
    return jsonify(result)


@system_boost_api.route('/api/system/report/page_usage', methods=['POST'])
@require_login
def report_page_usage():
    """上报页面使用数据"""
    data = request.get_json() or {}
    svc = _get_report_service()
    ok = svc.report_page_usage(
        page_name=data.get('page_name', ''),
        page_category=data.get('page_category', ''),
        user_id=data.get('user_id', ''),
        session_id=data.get('session_id', ''),
        duration=data.get('duration', 0),
        actions=data.get('actions', 0),
        features=data.get('features', []),
        errors=data.get('errors', 0)
    )
    return jsonify({'success': ok})


@system_boost_api.route('/api/system/report/api_call', methods=['POST'])
@require_login
def report_api_call():
    """上报API调用数据"""
    data = request.get_json() or {}
    svc = _get_report_service()
    ok = svc.report_api_call(
        endpoint=data.get('endpoint', ''),
        method=data.get('method', 'GET'),
        status_code=data.get('status_code', 200),
        response_time=data.get('response_time', 0),
        user_id=data.get('user_id', ''),
        error_message=data.get('error_message', '')
    )
    return jsonify({'success': ok})


@system_boost_api.route('/api/system/report/performance', methods=['POST'])
@require_admin
def report_performance():
    """上报性能指标"""
    data = request.get_json() or {}
    svc = _get_report_service()
    ok = svc.report_performance(
        metric_name=data.get('metric_name', ''),
        value=float(data.get('value', 0)),
        unit=data.get('unit', ''),
        category=data.get('category', 'system'),
        warn_threshold=data.get('warn_threshold'),
        critical_threshold=data.get('critical_threshold')
    )
    return jsonify({'success': ok})


@system_boost_api.route('/api/system/report/list', methods=['GET'])
@require_login
def list_reports():
    """查询上报记录"""
    report_type = request.args.get('type', '')
    module = request.args.get('module', '')
    severity = request.args.get('severity', '')
    limit = min(int(request.args.get('limit', 50)), 500)
    svc = _get_report_service()
    reports = svc.get_reports(report_type, module, severity, limit)
    return jsonify({'success': True, 'count': len(reports), 'data': reports})


@system_boost_api.route('/api/system/report/dashboard', methods=['GET'])
@require_login
def report_dashboard():
    """获取上报仪表板"""
    svc = _get_report_service()
    stats = svc.get_dashboard_stats()
    return jsonify({'success': True, 'data': stats})


@system_boost_api.route('/api/system/report/acknowledge/<report_id>', methods=['POST'])
@require_admin
def acknowledge_report(report_id):
    """确认上报记录"""
    svc = _get_report_service()
    ok = svc.acknowledge_report(report_id)
    return jsonify({'success': ok})


@system_boost_api.route('/api/system/report/page_coverage', methods=['GET'])
@require_login
def page_coverage():
    """获取页面功能覆盖率"""
    svc = _get_report_service()
    coverage = svc.get_page_feature_coverage()
    return jsonify({'success': True, 'data': coverage})


# ============ 健康检查 ============

@system_boost_api.route('/api/system/boost/health', methods=['GET'])
@require_login
def boost_health():
    """系统强化健康检查"""
    engine = _get_boost_engine()
    report_svc = _get_report_service()
    snapshot = engine._get_system_snapshot()
    dashboard = report_svc.get_dashboard_stats()
    return jsonify({
        'success': True,
        'status': 'healthy',
        'system_snapshot': snapshot,
        'report_dashboard': {
            'total_reports': dashboard.get('total_reports', 0),
            'unacknowledged_alerts': dashboard.get('unacknowledged_alerts', 0),
            'performance_status': dashboard.get('performance', {})
        },
        'timestamp': datetime.now().isoformat()
    })
