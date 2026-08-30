from flask import Blueprint, jsonify
"""brain_bank_routes — AI 脑库探索器 Blueprint

功能: 脑库条目/知识图谱/投喂记录/异常特征库/投喂热力图
表: ai_brain_bank / ai_brain_feeding_log / mt_ai_brain_feed_log / mt_rule_violation_alert
权限: 查询需登录
"""
from . import brain_bank_bp
from ._governance_helpers import (
    _check_login, _query, _query_one, _count, _ok, _fail,
    _arg_int, _arg_str,
)


@brain_bank_bp.route('/stats', methods=['GET'])
def stats():
    """脑库统计 (总条目/经验/异常/违反 + 30天热力图 + 类型分布)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    total = _count('ai_brain_bank')
    by_type = {
        'experience': _count('ai_brain_feeding_log'),
        'knowledge': total,
        'anomaly': _count('mt_rule_violation_alert'),
        'rule': _count('mt_rule_violation_alert', "rule_id LIKE 'MT_RULE%'"),
        'violation': _count('mt_rule_violation_alert'),
    }
    # 30天热力图: ai_brain_bank.created_at 按天聚合
    heatmap = []
    try:
        rows = _query(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM ai_brain_bank "
            "WHERE created_at >= DATE('now','-30 days','localtime') "
            "GROUP BY DATE(created_at) ORDER BY d")
        # 补齐30天
        by_date = {r.get('d'): r.get('c', 0) for r in rows}
        from datetime import datetime, timedelta
        today = datetime.now()
        for i in range(29, -1, -1):
            d = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            heatmap.append(by_date.get(d, 0))
    except Exception:
        heatmap = [0] * 30
    return _ok({
        'total': total,
        'by_type': by_type,
        'heatmap': heatmap,
    })


@brain_bank_bp.route('/list', methods=['GET'])
def list_entries():
    """脑库条目列表 (支持关键词/类型搜索)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    q = _arg_str('q')
    entry_type = _arg_str('type')
    limit = _arg_int('limit', 50, 1, 500)
    where_parts = []
    args = []
    if q:
        where_parts.append("(title LIKE ? OR content LIKE ? OR tags LIKE ?)")
        kw = f'%{q}%'
        args.extend([kw, kw, kw])
    if entry_type:
        # 类型映射: experience→feeding_log, anomaly/violation→rule_violation, knowledge→brain_bank
        if entry_type == 'experience':
            return _ok({'entries': _query(
                "SELECT feed_id AS entry_id, 'experience' AS entry_type, "
                "topics_json AS summary, round_num, knowledge_count, "
                "total_confidence, duration_ms, created_at, 'feeding_log' AS source "
                "FROM ai_brain_feeding_log ORDER BY created_at DESC LIMIT ?", [limit])})
        if entry_type in ('anomaly', 'violation'):
            return _ok({'entries': _query(
                "SELECT alert_id AS entry_id, violation_code AS entry_type, "
                "violation_detail AS summary, rule_id, triggered_by, triggered_at AS created_at, "
                "'rule_violation' AS source, eigenflux_fed, brain_fed, sa_notified "
                "FROM mt_rule_violation_alert ORDER BY triggered_at DESC LIMIT ?", [limit])})
    where = ('WHERE ' + ' AND '.join(where_parts)) if where_parts else ''
    sql = (f"SELECT id AS entry_id, 'knowledge' AS entry_type, category, title, "
           f"content, tags, version, created_at, 'brain_bank' AS source, 0 AS weight "
           f"FROM ai_brain_bank {where} ORDER BY created_at DESC LIMIT ?")
    rows = _query(sql, args + [limit])
    return _ok({'entries': rows, 'count': len(rows)})


@brain_bank_bp.route('/get', methods=['GET'])
def get_entry():
    """脑库条目详情"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    entry_id = _arg_str('id')
    if not entry_id:
        return _fail('缺少 id 参数', 400)
    # 先查 brain_bank
    r = _query_one(
        "SELECT id AS entry_id, 'knowledge' AS entry_type, category, title, content, tags, "
        "version, created_at FROM ai_brain_bank WHERE id=?", [entry_id])
    if r:
        return _ok({'entry': r})
    # 再查 rule_violation
    r = _query_one(
        "SELECT alert_id AS entry_id, violation_code AS entry_type, violation_detail AS content, "
        "rule_id, triggered_by, triggered_at AS created_at, eigenflux_fed, brain_fed, sa_notified "
        "FROM mt_rule_violation_alert WHERE alert_id=?", [entry_id])
    if r:
        return _ok({'entry': r})
    return _fail('条目不存在', 404)


@brain_bank_bp.route('/graph', methods=['GET'])
def graph():
    """知识图谱节点 (Top N 高权重标签)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 200)
    # 从 ai_brain_bank.tags 提取标签频次
    rows = _query(
        "SELECT tags, COUNT(*) AS c FROM ai_brain_bank WHERE tags IS NOT NULL AND tags != '' "
        "GROUP BY tags ORDER BY c DESC LIMIT ?", [limit])
    nodes = []
    for i, r in enumerate(rows):
        tag = (r.get('tags') or '').split(',')[0].strip() or f'tag_{i}'
        nodes.append({'id': i, 'label': tag, 'count': r.get('c', 0), 'weight': r.get('c', 0)})
    return _ok({'nodes': nodes, 'edges': []})


@brain_bank_bp.route('/feed', methods=['GET'])
def feed():
    """最近投喂记录"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 30, 1, 200)
    # 合并 mt_ai_brain_feed_log 和 ai_brain_feeding_log
    rows = _query(
        "SELECT feed_id, flow_id, feed_target, payload_preview AS content, "
        "'brain_feed_log' AS source, 'experience' AS feed_type, fed_at AS created_at, fed_by "
        "FROM mt_ai_brain_feed_log ORDER BY fed_at DESC LIMIT ?", [limit])
    if not rows:
        rows = _query(
            "SELECT feed_id, '' AS flow_id, 'feeding_log' AS feed_target, "
            "topics_json AS content, 'experience' AS feed_type, created_at, '' AS fed_by "
            "FROM ai_brain_feeding_log ORDER BY created_at DESC LIMIT ?", [limit])
    return _ok({'items': rows, 'count': len(rows)})


@brain_bank_bp.route('/anomaly', methods=['GET'])
def anomaly():
    """系统异常错误特征库 (规则违反告警)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 500)
    rows = _query(
        "SELECT alert_id AS feature_id, violation_code AS anomaly_type, "
        "violation_detail AS feature_summary, rule_id, triggered_by, "
        "triggered_at AS last_seen, eigenflux_fed, brain_fed, sa_notified, "
        "COUNT(*) OVER() AS occurrence_count "
        "FROM mt_rule_violation_alert ORDER BY triggered_at DESC LIMIT ?", [limit])
    return _ok({'items': rows, 'count': len(rows)})


bp = Blueprint('brain_bank_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'brain_bank','routes_implemented':1}})

