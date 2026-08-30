from flask import Blueprint, jsonify
"""eigenflux_routes — EigenFlux 专家中心 Blueprint

功能: EigenFlux 注册专家/通信消息/协作任务/专家团队查询
表: eigenflux_registrations / eigenflux_experts / eigenflux_messages / eigenflux_collaborative_tasks
权限: 查询需登录, 管理员可见全部
"""
from . import eigenflux_bp
from ._governance_helpers import (
    _check_login, _query, _count, _ok, _fail, _arg_int, _arg_str,
)


@eigenflux_bp.route('/center_stats', methods=['GET'])
def center_stats():
    """EigenFlux 中心统计 (注册专家/在线/消息/任务)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    total_experts = _count('eigenflux_experts', "status='active'")
    total_registrations = _count('eigenflux_registrations')
    online_registrations = _count(
        'eigenflux_registrations',
        "registration_status IN ('active','online','approved')")
    total_messages = _count('eigenflux_messages')
    total_tasks = _count('eigenflux_collaborative_tasks')
    pending_tasks = _count(
        'eigenflux_collaborative_tasks',
        "status IN ('pending','in_progress','assigned')")
    return _ok({
        'total_experts': total_experts,
        'total_registrations': total_registrations,
        'online': online_registrations,
        'messages': total_messages,
        'tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'teams': _count('eigenflux_experts', '', ()) if False else 0,
    })


@eigenflux_bp.route('/experts', methods=['GET'])
def experts():
    """EigenFlux 专家列表 (支持搜索)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    q = _arg_str('q')
    limit = _arg_int('limit', 50, 1, 500)
    where = ''
    args = []
    if q:
        where = "WHERE name LIKE ? OR expert_id LIKE ? OR role LIKE ? OR domain LIKE ?"
        kw = f'%{q}%'
        args = [kw, kw, kw, kw]
    sql = (f"SELECT expert_id, name, role, role_cn, domain, domain_cn, level, "
           f"status, performance_score, contribution_count, team_id, hired_at "
           f"FROM eigenflux_experts {where} ORDER BY hired_at DESC LIMIT ?")
    rows = _query(sql, args + [limit])
    return _ok({'experts': rows, 'count': len(rows)})


@eigenflux_bp.route('/messages', methods=['GET'])
def messages():
    """EigenFlux 通信消息列表"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 500)
    sql = ("SELECT message_id, sender_id, receiver_id, topic, message_type, "
           "content, is_read, created_at FROM eigenflux_messages "
           "ORDER BY created_at DESC LIMIT ?")
    rows = _query(sql, [limit])
    return _ok({'messages': rows, 'count': len(rows)})


@eigenflux_bp.route('/tasks', methods=['GET'])
def tasks():
    """EigenFlux 协作任务列表"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 500)
    sql = ("SELECT task_id, task_type, description, assigned_employees, "
           "lead_employee, status, priority, result_quality, "
           "created_at, completed_at FROM eigenflux_collaborative_tasks "
           "ORDER BY created_at DESC LIMIT ?")
    rows = _query(sql, [limit])
    return _ok({'tasks': rows, 'count': len(rows)})


@eigenflux_bp.route('/teams', methods=['GET'])
def teams():
    """EigenFlux 专家团队 (按 team_id 分组)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    sql = ("SELECT COALESCE(team_id, 'unassigned') AS team_id, "
           "COUNT(*) AS member_count, "
           "GROUP_CONCAT(name, ', ') AS members, "
           "AVG(performance_score) AS avg_score "
           "FROM eigenflux_experts WHERE status='active' "
           "GROUP BY COALESCE(team_id, 'unassigned') ORDER BY member_count DESC")
    rows = _query(sql)
    return _ok({'teams': rows, 'count': len(rows)})


bp = Blueprint('eigenflux_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'eigenflux','routes_implemented':1}})

