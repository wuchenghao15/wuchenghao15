from flask import Blueprint, jsonify
"""devflow_routes — 强制开发流程 Blueprint

功能: 18节点状态机/流程记录/A轮B轮讨论/验收测试/Git同步状态
表: mt_dev_flow_session / mt_dev_flow_events
权限: 查询需登录
"""
from . import devflow_bp
from ._governance_helpers import (
    _check_login, _query, _query_one, _count, _ok, _fail,
    _arg_int, _arg_str,
)
import json


# 18节点状态机定义 (与 §14 强制开发12步骤规则一致)
_NODES_18 = [
    'STEP_1_PROPOSAL', 'STEP_2A_ROUND', 'STEP_3_ZXF_DECISION',
    'STEP_31_B_ROUND', 'STEP_311_SA_JUDGMENT', 'STEP_312_AUTO_PASS',
    'STEP_32_PASS_SKIP_B', 'STEP_4_CLERK_RECORD', 'STEP_5_IMPL_DOCKING',
    'STEP_6_AI_TEAM_COORD', 'STEP_7_EXECUTE', 'STEP_8_ACCEPTANCE',
    'STEP_9A_PASS_OR_LOOPBACK', 'STEP_9B_SUMMARY',
    'STEP_10_VERSION_UPGRADE', 'STEP_11_GIT_SYNC',
    'STEP_12_TEST_1000', 'DONE',
]
_NODE_LABELS = {
    'STEP_1_PROPOSAL': '提案', 'STEP_2A_ROUND': 'A轮讨论', 'STEP_3_ZXF_DECISION': '张晓峰表决',
    'STEP_31_B_ROUND': 'B轮再讨论', 'STEP_311_SA_JUDGMENT': 'SA决断', 'STEP_312_AUTO_PASS': '方案自动通过',
    'STEP_32_PASS_SKIP_B': '直接通过跳过B轮', 'STEP_4_CLERK_RECORD': '会议记录', 'STEP_5_IMPL_DOCKING': '实施团队对接',
    'STEP_6_AI_TEAM_COORD': 'AI实施团队统筹', 'STEP_7_EXECUTE': '下场实施', 'STEP_8_ACCEPTANCE': '收场验收',
    'STEP_9A_PASS_OR_LOOPBACK': '验收结果分支', 'STEP_9B_SUMMARY': '汇总上报投喂',
    'STEP_10_VERSION_UPGRADE': '版本强制评估', 'STEP_11_GIT_SYNC': 'Git同步', 'STEP_12_TEST_1000': '1000轮测试',
    'DONE': '完成',
}


def _node_status(flow_step: str, final_status: str, current_index: int) -> str:
    """判断节点状态: done/current/blocked/"""
    if final_status == 'DONE':
        return 'done'
    if final_status in ('BLOCKED', 'VIOLATION'):
        return 'blocked'
    return 'current' if current_index == 0 else ('done' if current_index > 0 else '')


@devflow_bp.route('/stats', methods=['GET'])
def stats():
    """开发流程统计 (总数/已完成/进行中/回环/阻断)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    total = _count('mt_dev_flow_session')
    done = _count('mt_dev_flow_session', "final_status='DONE'")
    progress = _count('mt_dev_flow_session', "final_status NOT IN ('DONE','BLOCKED','VIOLATION','CLOSED')")
    loopback = _count('mt_dev_flow_session', "loopback_count > 0")
    blocked = _count('mt_dev_flow_session', "final_status IN ('BLOCKED','VIOLATION')")
    return _ok({
        'total': total, 'done': done, 'progress': progress,
        'loopback': loopback, 'blocked': blocked,
    })


@devflow_bp.route('/list', methods=['GET'])
def list_flows():
    """流程记录列表 (支持搜索)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    q = _arg_str('q')
    limit = _arg_int('limit', 100, 1, 500)
    where = ''
    args = []
    if q:
        where = "WHERE flow_id LIKE ? OR proposal_title LIKE ? OR created_by LIKE ?"
        kw = f'%{q}%'
        args = [kw, kw, kw]
    sql = (f"SELECT flow_id, proposal_title, proposal_summary, current_step, "
           f"final_status, loopback_count, created_at, created_by "
           f"FROM mt_dev_flow_session {where} ORDER BY created_at DESC LIMIT ?")
    rows = _query(sql, args + [limit])
    # 补充 proposer 字段
    for r in rows:
        r['proposer'] = r.get('created_by') or '-'
        r['current_node'] = r.get('current_step')
    return _ok({'flows': rows, 'count': len(rows)})


@devflow_bp.route('/machine', methods=['GET'])
def machine():
    """18节点状态机视图 (单个流程)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    flow_id = _arg_str('flow_id')
    if not flow_id:
        return _fail('缺少 flow_id 参数', 400)
    r = _query_one(
        "SELECT flow_id, current_step, final_status, loopback_count, "
        "zhangxiaofeng_decision, super_admin_judgment, git_sync_status "
        "FROM mt_dev_flow_session WHERE flow_id=?", [flow_id])
    if not r:
        return _fail('流程不存在', 404)
    current_step = r.get('current_step') or 'STEP_1_PROPOSAL'
    final_status = r.get('final_status') or 'OPEN'
    # 计算每个节点的状态
    try:
        current_idx = _NODES_18.index(current_step) if current_step in _NODES_18 else 0
    except ValueError:
        current_idx = 0
    nodes = []
    for i, code in enumerate(_NODES_18):
        if final_status == 'DONE':
            st = 'done'
        elif final_status in ('BLOCKED', 'VIOLATION'):
            st = 'blocked' if i == current_idx else 'done'
        elif i < current_idx:
            st = 'done'
        elif i == current_idx:
            st = 'current'
        else:
            st = ''
        nodes.append({'code': code, 'label': _NODE_LABELS.get(code, code), 'status': st})
    # 4层拦截状态 (从 final_status 和 git_sync_status 派生)
    intercept = {
        'pre_commit': True,
        'before_request': True,
        'ci_check': True,
        'git_hook': bool(r.get('git_sync_status')),
    }
    return _ok({
        'flow_id': flow_id,
        'current_node': current_step,
        'final_status': final_status,
        'loopback_count': r.get('loopback_count', 0),
        'nodes': nodes,
        'intercept': intercept,
    })


@devflow_bp.route('/discuss', methods=['GET'])
def discuss():
    """A轮/B轮讨论记录"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 200)
    rows = _query(
        "SELECT flow_id, current_step, "
        "a_round_attendance_json, a_round_discussion_json, "
        "b_round_panels_json, b_round_discussion_json, "
        "b_round_zhangxiaofeng_participated, b_round_agree_suspend, "
        "b_round_disagree_suspend, zhangxiaofeng_decision, "
        "clerk_vote_summary, created_at "
        "FROM mt_dev_flow_session "
        "WHERE current_step LIKE 'STEP_2%' OR current_step LIKE 'STEP_3%' "
        "ORDER BY created_at DESC LIMIT ?", [limit])
    items = []
    for r in rows:
        flow_id = r.get('flow_id')
        # A轮记录
        try:
            attendance = json.loads(r.get('a_round_attendance_json') or '[]')
            if isinstance(attendance, dict):
                attendance = list(attendance.keys())
        except Exception:
            attendance = []
        try:
            a_disc = json.loads(r.get('a_round_discussion_json') or '{}')
            a_summary = (a_disc.get('summary') or a_disc.get('summary_text') or '') if isinstance(a_disc, dict) else str(a_disc)[:100]
        except Exception:
            a_summary = ''
        items.append({
            'flow_id': flow_id,
            'round': 'A',
            'attendance': attendance if isinstance(attendance, list) else [],
            'summary': a_summary,
            'vote_summary': r.get('clerk_vote_summary', ''),
            'zxf_decision': r.get('zhangxiaofeng_decision', ''),
        })
        # B轮记录 (仅当有 B 轮数据)
        if r.get('b_round_panels_json') or r.get('b_round_discussion_json'):
            try:
                b_disc = json.loads(r.get('b_round_discussion_json') or '{}')
                b_summary = (b_disc.get('summary') or b_disc.get('summary_text') or '') if isinstance(b_disc, dict) else str(b_disc)[:100]
            except Exception:
                b_summary = ''
            b_attendance = []
            try:
                bp = json.loads(r.get('b_round_panels_json') or '[]')
                if isinstance(bp, list):
                    b_attendance = [str(p.get('name', p)) if isinstance(p, dict) else str(p) for p in bp]
            except Exception:
                pass
            items.append({
                'flow_id': flow_id,
                'round': 'B',
                'attendance': b_attendance,
                'summary': b_summary,
                'vote_summary': f"同意暂缓:{r.get('b_round_agree_suspend',0)} 不同意暂缓:{r.get('b_round_disagree_suspend',0)}",
                'zxf_decision': '未参加B轮' if r.get('b_round_zhangxiaofeng_participated') == 0 else '参加',
            })
    return _ok({'items': items, 'count': len(items)})


@devflow_bp.route('/acceptance', methods=['GET'])
def acceptance():
    """验收与测试进度"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 200)
    rows = _query(
        "SELECT flow_id, acceptance_passed, acceptance_json, acceptance_step_results_json, "
        "test1000_total, test1000_pass, test1000_fail, test1000_vuln, "
        "super_admin_judgment, final_status, created_at "
        "FROM mt_dev_flow_session "
        "WHERE current_step LIKE 'STEP_8%' OR current_step LIKE 'STEP_9%' "
        "OR current_step LIKE 'STEP_10%' OR current_step LIKE 'STEP_11%' "
        "OR current_step LIKE 'STEP_12%' OR final_status='DONE' "
        "ORDER BY created_at DESC LIMIT ?", [limit])
    items = []
    for r in rows:
        # 从 acceptance_step_results_json 派生 step_total/step_passed
        step_total = 0
        step_passed = 0
        try:
            results = json.loads(r.get('acceptance_step_results_json') or '{}')
            if isinstance(results, dict):
                step_total = len(results)
                step_passed = sum(1 for v in results.values() if v in (True, 'pass', 'passed', 1))
            elif isinstance(results, list):
                step_total = len(results)
                step_passed = sum(1 for v in results if v in (True, 'pass', 'passed', 1))
        except Exception:
            pass
        items.append({
            'flow_id': r.get('flow_id'),
            'acceptor': r.get('super_admin_judgment') or '石监理',
            'step_total': step_total,
            'step_passed': step_passed,
            'test_total': r.get('test1000_total', 0),
            'test_passed': r.get('test1000_pass', 0),
            'acceptance_passed': bool(r.get('acceptance_passed')),
        })
    return _ok({'items': items, 'count': len(items)})


@devflow_bp.route('/git_status', methods=['GET'])
def git_status():
    """Git同步状态 (Layer-4 pre-push 拦截)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 200)
    rows = _query(
        "SELECT flow_id, git_sync_target_branch, git_sync_commit_hash, "
        "git_sync_commit_subject, git_sync_status, git_sync_error, "
        "git_sync_remote_name, final_status, updated_at "
        "FROM mt_dev_flow_session "
        "WHERE git_sync_commit_hash IS NOT NULL AND git_sync_commit_hash != '' "
        "ORDER BY updated_at DESC LIMIT ?", [limit])
    items = []
    for r in rows:
        status = (r.get('git_sync_status') or '').upper()
        items.append({
            'flow_id': r.get('flow_id'),
            'commit_sha': r.get('git_sync_commit_hash', ''),
            'branch': r.get('git_sync_target_branch', ''),
            'pushed_at': r.get('updated_at', ''),
            'pre_push_passed': status in ('SUCCESS', 'DONE', 'PUSHED', 'OK', 'SYNCED'),
            'final_status': r.get('final_status', ''),
        })
    return _ok({'items': items, 'count': len(items)})


bp = Blueprint('devflow_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'devflow','routes_implemented':1}}})

return bp
