"""maintenance_routes — 自动维护Agent Blueprint
功能: 系统健康监控/异常检测/自动修复/数据库维护/AI员工巡检/安全检查/日志清理/备份管理
遵循: SSOT原则(所有维护数据实时写入数据库) + 5级规则系统
权限: 状态查看需登录，启停/配置/手动触发需管理员
"""
from . import maintenance_bp

# 导入 server_real_db 中的共享函数（权限校验/用户读取）
try:
    from server_real_db import _current_safe_user, _MT_ADMIN_ROLES
except ImportError:
    # 兼容直接从 routes 包导入的场景
    import sys
    import os
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _base not in sys.path:
        sys.path.insert(0, _base)
    from server_real_db import _current_safe_user, _MT_ADMIN_ROLES

from flask import Blueprint, jsonify, jsonify, request
from datetime import datetime


def _check_admin(user):
    """校验管理员权限（超级管理员 wuchenghao15 无条件放行）"""
    if user.get('is_super_admin'):
        return True, None
    if user.get('role') in _MT_ADMIN_ROLES:
        return True, None
    return False, (403, '需要管理员权限')


def _check_login(user):
    """校验登录状态"""
    if user.get('logged_in'):
        return True, None
    return False, (401, '未登录')


def _get_agent():
    """获取维护Agent单例（延迟初始化）"""
    from ai_engines.auto_maintenance_agent import get_maintenance_agent
    return get_maintenance_agent()


# ============================================================================
# 状态查询类（登录即可访问）
# ============================================================================

@maintenance_bp.route('/status', methods=['GET'])
def maintenance_status():
    """获取维护Agent运行状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        return jsonify({'success': True, 'status': agent.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取状态失败: {e}'}), 500


@maintenance_bp.route('/issues', methods=['GET'])
def maintenance_issues():
    """获取最近维护问题列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 500))
        agent = _get_agent()
        issues = agent.get_recent_issues(limit)
        return jsonify({'success': True, 'count': len(issues), 'issues': issues})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取问题列表失败: {e}'}), 500


@maintenance_bp.route('/reports', methods=['GET'])
def maintenance_reports():
    """获取最近维护报告列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = max(1, min(limit, 100))
        agent = _get_agent()
        reports = agent.get_recent_reports(limit)
        return jsonify({'success': True, 'count': len(reports), 'reports': reports})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取报告列表失败: {e}'}), 500


@maintenance_bp.route('/history', methods=['GET'])
def maintenance_history():
    """从数据库查询历史维护问题"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = max(1, min(limit, 1000))
        status_filter = request.args.get('status', None)
        agent = _get_agent()
        history = agent.get_history_from_db(limit=limit, issue_status=status_filter)
        return jsonify({'success': True, 'count': len(history), 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': f'查询历史失败: {e}'}), 500


@maintenance_bp.route('/dashboard', methods=['GET'])
def maintenance_dashboard():
    """维护控制台聚合数据：状态 + 统计 + 最近问题 + 最近报告"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        status = agent.get_status()
        recent_issues = agent.get_recent_issues(10)
        recent_reports = agent.get_recent_reports(5)
        db_reports = agent.get_reports_from_db(10)
        return jsonify({
            'success': True,
            'agent': status,
            'recent_issues': recent_issues,
            'recent_reports': recent_reports,
            'db_reports': db_reports,
            'server_time': datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取控制台数据失败: {e}'}), 500


# ============================================================================
# 操作控制类（需管理员权限）
# ============================================================================

@maintenance_bp.route('/start', methods=['POST'])
def maintenance_start():
    """启动维护Agent后台巡检"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        check_interval = data.get('check_interval')
        agent = _get_agent()
        result = agent.start(check_interval=check_interval)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'启动失败: {e}'}), 500


@maintenance_bp.route('/stop', methods=['POST'])
def maintenance_stop():
    """停止维护Agent后台巡检"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.stop()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'停止失败: {e}'}), 500


@maintenance_bp.route('/cycle', methods=['POST'])
def maintenance_cycle():
    """手动触发一次完整维护巡检周期"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        report = agent.run_maintenance_cycle()
        return jsonify({
            'success': True,
            'report': report.to_dict(),
            'summary': report.summary,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'巡检失败: {e}'}), 500


@maintenance_bp.route('/check/<monitor_type>', methods=['POST'])
def maintenance_single_check(monitor_type):
    """手动触发单个监控器检查
    monitor_type: system_health | database_health | route_api | log_health | file_system
    """
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.run_single_check(monitor_type)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'单项检查失败: {e}'}), 500


@maintenance_bp.route('/config', methods=['POST'])
def maintenance_config():
    """更新维护Agent配置（检查间隔/自动修复开关）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        check_interval = data.get('check_interval')
        auto_repair = data.get('auto_repair')
        agent = _get_agent()
        result = agent.set_config(check_interval=check_interval, auto_repair=auto_repair)
        return jsonify({'success': True, 'config': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'配置更新失败: {e}'}), 500


# ============================================================================
# 双数据库管理（管理员权限）
# ============================================================================

@maintenance_bp.route('/dual-db/status', methods=['GET'])
def maintenance_dual_db_status():
    """获取双数据库状态（主库+镜像库健康/故障切换/写入统计）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.dual_db.health_check()
        return jsonify({'success': True, 'dual_db': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取双库状态失败: {e}'}), 500


@maintenance_bp.route('/dual-db/sync', methods=['POST'])
def maintenance_dual_db_sync():
    """手动同步主库→镜像库"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.dual_db.sync_mirror()
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'同步失败: {e}'}), 500


@maintenance_bp.route('/dual-db/recover', methods=['POST'])
def maintenance_dual_db_recover():
    """从镜像库恢复主库（故障切换后恢复主库）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        agent.dual_db._recover_primary()
        return jsonify({'success': True, 'message': '主库已从镜像库恢复', 'status': agent.dual_db.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'恢复失败: {e}'}), 500


# ============================================================================
# 数据库备份管理（管理员权限）
# ============================================================================

@maintenance_bp.route('/backup/create', methods=['POST'])
def maintenance_backup_create():
    """创建数据库快照备份（在线热备）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        label = data.get('label')
        agent = _get_agent()
        result = agent.backup_manager.create_snapshot(label=label)
        return jsonify({'success': not result.get('error'), 'backup': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'备份失败: {e}'}), 500


@maintenance_bp.route('/backup/list', methods=['GET'])
def maintenance_backup_list():
    """列出所有数据库备份"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        backups = agent.backup_manager.list_backups()
        return jsonify({'success': True, 'count': len(backups), 'backups': backups})
    except Exception as e:
        return jsonify({'success': False, 'error': f'列出备份失败: {e}'}), 500


@maintenance_bp.route('/backup/restore', methods=['POST'])
def maintenance_backup_restore():
    """从备份恢复数据库"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        backup_name = data.get('backup_name')
        if not backup_name:
            return jsonify({'success': False, 'error': '缺少 backup_name 参数'}), 400
        agent = _get_agent()
        result = agent.backup_manager.restore_backup(backup_name)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'恢复失败: {e}'}), 500


@maintenance_bp.route('/backup/status', methods=['GET'])
def maintenance_backup_status():
    """获取备份管理器状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.backup_manager.get_status()
        return jsonify({'success': True, 'backup_status': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取备份状态失败: {e}'}), 500


# ============================================================================
# 备份引擎管理（管理员权限）
# ============================================================================

@maintenance_bp.route('/backup-engine/status', methods=['GET'])
def maintenance_backup_engine_status():
    """获取备份维护引擎状态（双引擎架构）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.backup_engine.get_status()
        return jsonify({'success': True, 'backup_engine': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取备份引擎状态失败: {e}'}), 500


@maintenance_bp.route('/backup-engine/check', methods=['POST'])
def maintenance_backup_engine_check():
    """手动触发主引擎健康检查"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        result = agent.backup_engine.check_primary_health()
        return jsonify({'success': True, 'health': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'健康检查失败: {e}'}), 500


@maintenance_bp.route('/backup-engine/takeover', methods=['POST'])
def maintenance_backup_engine_takeover():
    """手动触发备份引擎接管"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        agent.backup_engine.takeover()
        return jsonify({'success': True, 'message': '备份引擎已接管', 'status': agent.backup_engine.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'接管失败: {e}'}), 500


@maintenance_bp.route('/backup-engine/handback', methods=['POST'])
def maintenance_backup_engine_handback():
    """手动触发备份引擎交还职责"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        agent.backup_engine.handback()
        return jsonify({'success': True, 'message': '备份引擎已交还职责', 'status': agent.backup_engine.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'交还失败: {e}'}), 500


# ============================================================================
# 提案管理系统（自动巡检→自动修复→自动上报）
# ============================================================================

@maintenance_bp.route('/proposals', methods=['GET'])
def maintenance_proposals_list():
    """查询提案列表（支持按状态/类型筛选）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 500))
        status = request.args.get('status', None)
        prop_type = request.args.get('type', None)
        agent = _get_agent()
        proposals = agent.proposal_manager.get_proposals(limit=limit, status=status, prop_type=prop_type)
        return jsonify({'success': True, 'count': len(proposals), 'proposals': proposals})
    except Exception as e:
        return jsonify({'success': False, 'error': f'查询提案失败: {e}'}), 500


@maintenance_bp.route('/proposals/pending', methods=['GET'])
def maintenance_proposals_pending():
    """获取待审批提案"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 20, type=int)
        agent = _get_agent()
        proposals = agent.proposal_manager.get_pending_proposals(limit=limit)
        return jsonify({'success': True, 'count': len(proposals), 'pending_proposals': proposals})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取待审提案失败: {e}'}), 500


@maintenance_bp.route('/proposals/<proposal_id>', methods=['GET'])
def maintenance_proposal_detail(proposal_id):
    """获取提案详情"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        proposal = agent.proposal_manager._load_proposal_from_db(proposal_id)
        if not proposal:
            return jsonify({'success': False, 'error': '提案不存在'}), 404
        return jsonify({'success': True, 'proposal': proposal.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取提案详情失败: {e}'}), 500


@maintenance_bp.route('/proposals/<proposal_id>/review', methods=['POST'])
def maintenance_proposal_review(proposal_id):
    """审批提案（批准/驳回）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        approved = data.get('approved', False)
        notes = data.get('notes')
        reviewer = user.get('username', 'unknown')
        # 超级管理员标记
        if user.get('is_super_admin'):
            reviewer = f"super_admin:{reviewer}"
        agent = _get_agent()
        result = agent.proposal_manager.review_proposal(proposal_id, reviewer, approved, notes)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'审批失败: {e}'}), 500


@maintenance_bp.route('/proposals/<proposal_id>/execute', methods=['POST'])
def maintenance_proposal_execute(proposal_id):
    """执行已批准的提案"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        # 尝试加载提案并执行关联的修复
        proposal = agent.proposal_manager._load_proposal_from_db(proposal_id)
        if not proposal:
            return jsonify({'success': False, 'error': '提案不存在'}), 404

        # 根据提案关联的问题执行修复
        def _execute_repair():
            results = []
            for issue_id in proposal.related_issues:
                # 从数据库加载问题并修复
                issues = agent.dual_db.execute_query(
                    "SELECT * FROM mt_maintenance_issues WHERE issue_id = ?",
                    (issue_id,)
                )
                if issues:
                    from ai_engines.auto_maintenance_agent import MaintenanceIssue, MonitorType, MaintenanceLevel
                    row = issues[0]
                    issue = MaintenanceIssue(
                        issue_id=row['issue_id'],
                        monitor_type=MonitorType(row['monitor_type']),
                        level=MaintenanceLevel(row['level']),
                        title=row['title'],
                        description=row['description'] or '',
                    )
                    agent.repair_engine.repair(issue)
                    agent._save_issue_to_db(issue)
                    results.append(issue.to_dict())
            return {'repaired_issues': len(results), 'details': results}

        result = agent.proposal_manager.execute_approved_proposal(proposal_id, repair_fn=_execute_repair)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'执行失败: {e}'}), 500


@maintenance_bp.route('/proposals/reports', methods=['GET'])
def maintenance_proposal_reports():
    """获取提案上报记录"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 500))
        agent = _get_agent()
        reports = agent.proposal_manager.get_reports(limit=limit)
        return jsonify({'success': True, 'count': len(reports), 'reports': reports})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取上报记录失败: {e}'}), 500


@maintenance_bp.route('/proposals/stats', methods=['GET'])
def maintenance_proposal_stats():
    """获取提案统计"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        stats = agent.proposal_manager.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取提案统计失败: {e}'}), 500


# ============================================================================
# 数据库加密系统（v2.2：字段级AES加密 + 备份加密 + 密钥管理）
# ============================================================================

@maintenance_bp.route('/crypto/status', methods=['GET'])
def maintenance_crypto_status():
    """获取加密管理器状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        status = agent.crypto_manager.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取加密状态失败: {e}'}), 500


@maintenance_bp.route('/crypto/encrypt', methods=['POST'])
def maintenance_crypto_encrypt():
    """加密字段值"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        value = data.get('value')
        if value is None:
            return jsonify({'success': False, 'error': '缺少value参数'}), 400
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        encrypted = agent.crypto_manager.encrypt_field(value)
        agent.crypto_manager.log_audit('field_encrypt', target_type='field', operator=user.get('username', 'unknown'))
        return jsonify({'success': True, 'encrypted': encrypted})
    except Exception as e:
        return jsonify({'success': False, 'error': f'加密失败: {e}'}), 500


@maintenance_bp.route('/crypto/decrypt', methods=['POST'])
def maintenance_crypto_decrypt():
    """解密字段值"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        value = data.get('value')
        if not value:
            return jsonify({'success': False, 'error': '缺少value参数'}), 400
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        decrypted = agent.crypto_manager.decrypt_field(value)
        agent.crypto_manager.log_audit('field_decrypt', target_type='field', operator=user.get('username', 'unknown'))
        return jsonify({'success': True, 'decrypted': decrypted})
    except Exception as e:
        return jsonify({'success': False, 'error': f'解密失败: {e}'}), 500


@maintenance_bp.route('/crypto/encrypt-file', methods=['POST'])
def maintenance_crypto_encrypt_file():
    """加密备份文件"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({'success': False, 'error': '缺少file_path参数'}), 400
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        result = agent.crypto_manager.encrypt_file(file_path, delete_src=data.get('delete_src', False))
        agent.crypto_manager.log_audit('file_encrypt', target_type='file', target_id=file_path, operator=user.get('username', 'unknown'))
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'文件加密失败: {e}'}), 500


@maintenance_bp.route('/crypto/decrypt-file', methods=['POST'])
def maintenance_crypto_decrypt_file():
    """解密备份文件"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({'success': False, 'error': '缺少file_path参数'}), 400
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        result = agent.crypto_manager.decrypt_file(file_path, delete_src=data.get('delete_src', False))
        agent.crypto_manager.log_audit('file_decrypt', target_type='file', target_id=file_path, operator=user.get('username', 'unknown'))
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'文件解密失败: {e}'}), 500


@maintenance_bp.route('/crypto/rotate-key', methods=['POST'])
def maintenance_crypto_rotate_key():
    """密钥轮换（超级管理员/管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        operator = user.get('username', 'unknown')
        if user.get('is_super_admin'):
            operator = f"super_admin:{operator}"
        result = agent.crypto_manager.rotate_key(operator=operator)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'密钥轮换失败: {e}'}), 500


@maintenance_bp.route('/crypto/key-info', methods=['GET'])
def maintenance_crypto_key_info():
    """获取密钥信息（不含密钥本身）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        info = agent.crypto_manager.get_key_info()
        return jsonify({'success': True, 'key_info': info})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取密钥信息失败: {e}'}), 500


@maintenance_bp.route('/crypto/audit', methods=['GET'])
def maintenance_crypto_audit():
    """获取加密审计日志"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 500))
        agent = _get_agent()
        if not agent.crypto_manager:
            return jsonify({'success': False, 'error': '加密管理器未初始化'}), 500
        rows = agent.dual_db.execute_query(
            "SELECT * FROM mt_crypto_audit_log ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return jsonify({'success': True, 'count': len(rows), 'audit_logs': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取审计日志失败: {e}'}), 500


# ============================================================================
# 反编译检测与防护系统（v2.3：代码完整性 + 反编译检测 + 水印）
# ============================================================================

@maintenance_bp.route('/anti-decompile/status', methods=['GET'])
def maintenance_anti_decompile_status():
    """获取反编译防护系统状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.anti_decompilation_guard:
            return jsonify({'success': False, 'error': '反编译防护系统未初始化'}), 500
        status = agent.anti_decompilation_guard.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取状态失败: {e}'}), 500


@maintenance_bp.route('/anti-decompile/check', methods=['POST'])
def maintenance_anti_decompile_check():
    """执行反编译检测"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.anti_decompilation_guard:
            return jsonify({'success': False, 'error': '反编译防护系统未初始化'}), 500
        result = agent.anti_decompilation_guard.run_check()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'检测失败: {e}'}), 500


@maintenance_bp.route('/anti-decompile/baseline', methods=['POST'])
def maintenance_anti_decompile_baseline():
    """生成/重置代码完整性基线"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.anti_decompilation_guard:
            return jsonify({'success': False, 'error': '反编译防护系统未初始化'}), 500
        result = agent.anti_decompilation_guard.generate_baseline()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'生成基线失败: {e}'}), 500


@maintenance_bp.route('/anti-decompile/clean-pyc', methods=['POST'])
def maintenance_anti_decompile_clean_pyc():
    """清理 .pyc 文件"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.anti_decompilation_guard:
            return jsonify({'success': False, 'error': '反编译防护系统未初始化'}), 500
        result = agent.anti_decompilation_guard.clean_pyc()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'清理失败: {e}'}), 500


@maintenance_bp.route('/anti-decompile/watermark', methods=['POST'])
def maintenance_anti_decompile_watermark():
    """注入代码水印"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.anti_decompilation_guard:
            return jsonify({'success': False, 'error': '反编译防护系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        key_files = data.get('key_files')
        results = agent.anti_decompilation_guard.inject_watermarks(key_files)
        return jsonify({'success': True, 'count': len(results), 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': f'水印注入失败: {e}'}), 500


@maintenance_bp.route('/anti-decompile/alerts', methods=['GET'])
def maintenance_anti_decompile_alerts():
    """获取反编译告警列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.anti_decompilation_guard:
            return jsonify({'success': False, 'error': '反编译防护系统未初始化'}), 500
        limit = request.args.get('limit', 50, type=int)
        level = request.args.get('level')
        limit = max(1, min(limit, 500))
        alerts = agent.anti_decompilation_guard.get_alerts(limit=limit, level=level)
        return jsonify({'success': True, 'count': len(alerts), 'alerts': alerts})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取告警失败: {e}'}), 500


# ============================================================================
# JSON数据同步数据库系统（v2.4：JSON↔DB双向同步 + Schema推断）
# ============================================================================

@maintenance_bp.route('/json-sync/status', methods=['GET'])
def maintenance_json_sync_status():
    """获取JSON同步系统状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.json_db_sync:
            return jsonify({'success': False, 'error': 'JSON同步系统未初始化'}), 500
        status = agent.json_db_sync.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取状态失败: {e}'}), 500


@maintenance_bp.route('/json-sync/import', methods=['POST'])
def maintenance_json_sync_import():
    """JSON→数据库导入"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.json_db_sync:
            return jsonify({'success': False, 'error': 'JSON同步系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        filepath = data.get('filepath')
        if not filepath:
            return jsonify({'success': False, 'error': '缺少filepath参数'}), 400
        table_name = data.get('table_name')
        mode = data.get('mode', 'replace')
        result = agent.json_db_sync.import_json(filepath, table_name, mode)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'导入失败: {e}'}), 500


@maintenance_bp.route('/json-sync/export', methods=['POST'])
def maintenance_json_sync_export():
    """数据库→JSON导出"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.json_db_sync:
            return jsonify({'success': False, 'error': 'JSON同步系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        table_name = data.get('table_name')
        if not table_name:
            return jsonify({'success': False, 'error': '缺少table_name参数'}), 400
        output_path = data.get('output_path')
        result = agent.json_db_sync.export_json(table_name, output_path)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'导出失败: {e}'}), 500


@maintenance_bp.route('/json-sync/register', methods=['POST'])
def maintenance_json_sync_register():
    """注册文件自动同步"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.json_db_sync:
            return jsonify({'success': False, 'error': 'JSON同步系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        filepath = data.get('filepath')
        if not filepath:
            return jsonify({'success': False, 'error': '缺少filepath参数'}), 400
        table_name = data.get('table_name')
        direction = data.get('direction', 'json_to_db')
        result = agent.json_db_sync.register(filepath, table_name, direction)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'注册失败: {e}'}), 500


@maintenance_bp.route('/json-sync/sync-all', methods=['POST'])
def maintenance_json_sync_sync_all():
    """同步所有注册文件"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.json_db_sync:
            return jsonify({'success': False, 'error': 'JSON同步系统未初始化'}), 500
        results = agent.json_db_sync.sync_all()
        return jsonify({'success': True, 'count': len(results), 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': f'同步失败: {e}'}), 500


@maintenance_bp.route('/json-sync/log', methods=['GET'])
def maintenance_json_sync_log():
    """获取同步日志"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.json_db_sync:
            return jsonify({'success': False, 'error': 'JSON同步系统未初始化'}), 500
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 500))
        logs = agent.json_db_sync.get_sync_log(limit=limit)
        return jsonify({'success': True, 'count': len(logs), 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取日志失败: {e}'}), 500


# ============================================================================
# 自动升级系统 v2.5.0 (AutoUpgradeSystem)
# 半自动策略：检测 → 提案 → 审批 → 执行(含回滚)
# ============================================================================

@maintenance_bp.route('/upgrade/status', methods=['GET'])
def maintenance_upgrade_status():
    """获取自动升级系统状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        return jsonify({'success': True, 'status': agent.upgrade_system.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取状态失败: {e}'}), 500


@maintenance_bp.route('/upgrade/detect', methods=['POST'])
def maintenance_upgrade_detect():
    """触发升级检测（检测所有4大目标）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        target = data.get('target')
        if target:
            from ai_engines.auto_upgrade_system import UpgradeTarget
            try:
                t = UpgradeTarget(target)
                items = agent.upgrade_system.detect_target(t)
            except ValueError:
                return jsonify({'success': False, 'error': f'未知升级目标: {target}'}), 400
        else:
            items = agent.upgrade_system.detect_all()
        return jsonify({
            'success': True,
            'count': len(items),
            'items': [item.to_dict() for item in items],
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'检测失败: {e}'}), 500


@maintenance_bp.route('/upgrade/items', methods=['GET'])
def maintenance_upgrade_items():
    """获取升级项列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        limit = request.args.get('limit', 100, type=int)
        limit = max(1, min(limit, 500))
        status = request.args.get('status')
        items = agent.upgrade_system.get_items(limit=limit, status=status)
        return jsonify({'success': True, 'count': len(items), 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取升级项失败: {e}'}), 500


@maintenance_bp.route('/upgrade/propose', methods=['POST'])
def maintenance_upgrade_propose():
    """从检测结果生成升级提案（半自动入口）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        summary = data.get('summary', '')
        # 可选：传入指定item_id列表，否则检测全部
        proposal = agent.upgrade_system.create_proposal(summary=summary)
        return jsonify({'success': True, 'proposal': proposal.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': f'生成提案失败: {e}'}), 500


@maintenance_bp.route('/upgrade/proposals', methods=['GET'])
def maintenance_upgrade_proposals():
    """获取提案列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 200))
        proposals = agent.upgrade_system.get_proposals(limit=limit)
        return jsonify({'success': True, 'count': len(proposals), 'proposals': proposals})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取提案失败: {e}'}), 500


@maintenance_bp.route('/upgrade/approve/<proposal_id>', methods=['POST'])
def maintenance_upgrade_approve(proposal_id):
    """审批通过升级提案"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        approved_by = user.get('username', 'unknown')
        result = agent.upgrade_system.approve_proposal(proposal_id, approved_by)
        return jsonify({'success': result['approved'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'审批失败: {e}'}), 500


@maintenance_bp.route('/upgrade/reject/<proposal_id>', methods=['POST'])
def maintenance_upgrade_reject(proposal_id):
    """拒绝升级提案"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        data = request.get_json(silent=True) or {}
        reason = data.get('reason', '')
        result = agent.upgrade_system.reject_proposal(proposal_id, reason)
        return jsonify({'success': result['rejected'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'拒绝失败: {e}'}), 500


@maintenance_bp.route('/upgrade/execute/<proposal_id>', methods=['POST'])
def maintenance_upgrade_execute(proposal_id):
    """执行已审批的升级提案（超级管理员可强制执行跳过审批）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        # 超级管理员 wuchenghao15 可强制执行（跳过审批校验）
        force = bool(user.get('is_super_admin'))
        approved_by = user.get('username', 'unknown')
        result = agent.upgrade_system.execute_proposal(
            proposal_id, approved_by=approved_by, force=force)
        return jsonify({'success': result.get('status') == 'completed',
                        'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'执行失败: {e}'}), 500


@maintenance_bp.route('/upgrade/rollback/<execution_id>', methods=['POST'])
def maintenance_upgrade_rollback(execution_id):
    """回滚指定升级执行"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        result = agent.upgrade_system.rollback(execution_id)
        return jsonify({'success': result['success'], 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'回滚失败: {e}'}), 500


@maintenance_bp.route('/upgrade/history', methods=['GET'])
def maintenance_upgrade_history():
    """获取升级执行历史"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        limit = request.args.get('limit', 50, type=int)
        limit = max(1, min(limit, 200))
        executions = agent.upgrade_system.get_executions(limit=limit)
        return jsonify({'success': True, 'count': len(executions), 'executions': executions})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取历史失败: {e}'}), 500


@maintenance_bp.route('/upgrade/audit', methods=['GET'])
def maintenance_upgrade_audit():
    """获取升级审计日志"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok:
        return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        if not agent.upgrade_system:
            return jsonify({'success': False, 'error': '升级系统未初始化'}), 500
        limit = request.args.get('limit', 100, type=int)
        limit = max(1, min(limit, 500))
        logs = agent.upgrade_system.get_audit_log(limit=limit)
        return jsonify({'success': True, 'count': len(logs), 'audit_logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取审计日志失败: {e}'}), 500


# ============================================================================
# 个性化/定制化/云端化 v2.6.0
#   个性化(4子模块): /api/maintenance/pz/*
#   定制化(3子模块): /api/maintenance/cz/*
#   云端化(4子模块): /api/maintenance/cloud/*
# ============================================================================

def _safe_pz(agent):
    """获取个性化引擎，未初始化返回None"""
    return getattr(agent, 'personalization_core', None)

def _safe_cz(agent):
    """获取定制化引擎，未初始化返回None"""
    return getattr(agent, 'customization_engine', None)

def _safe_cloud(agent):
    """获取云同步层，未初始化返回None"""
    return getattr(agent, 'cloud_sync', None)

def _un(agent_user_getter):
    u = agent_user_getter()
    return u.get('username'), u.get('role', 'user')

# ============================================================================
# 个性化(4子模块): /api/maintenance/pz/*
# ============================================================================

@maintenance_bp.route('/pz/status', methods=['GET'])
def pz_status():
    """个性化引擎状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '个性化引擎未初始化'}), 500
        return jsonify({'success': True, 'status': pz.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/all', methods=['GET'])
def pz_all():
    """获取当前用户4大类全量个性化配置"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        username = user.get('username')
        role = user.get('role', 'user')
        result = pz.get_all_for_user(username, role)
        return jsonify({'success': True, 'username': username, 'role': role, 'profile': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/<category>', methods=['GET'])
def pz_get_category(category):
    """获取单类个性化配置（category: ui_theme/home_menu/data_interaction/ai_employee）"""
    from ai_engines.personalization_core import ProfileCategory
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        cat = ProfileCategory(category)
    except ValueError:
        return jsonify({'success': False, 'error': f'非法分类: {category}'}), 400
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        value = pz.get_profile(user.get('username'), cat, user.get('role', 'user'))
        return jsonify({'success': True, 'category': category, 'value': value})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/<category>', methods=['POST'])
def pz_set_category(category):
    """保存单类个性化配置"""
    from ai_engines.personalization_core import ProfileCategory, ProfileLevel
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        cat = ProfileCategory(category)
    except ValueError:
        return jsonify({'success': False, 'error': f'非法分类: {category}'}), 400
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        value = data.get('value')
        if not isinstance(value, dict):
            return jsonify({'success': False, 'error': 'value必须是对象'}), 400
        device = data.get('device', request.headers.get('X-Device-Id', 'unknown'))
        # 角色/全局默认需管理员
        level_str = data.get('level', 'user')
        try:
            level = ProfileLevel(level_str)
        except ValueError:
            level = ProfileLevel.USER_PERSONAL
        if level in (ProfileLevel.ROLE_DEFAULT, ProfileLevel.GLOBAL_DEFAULT):
            ok2, err2 = _check_admin(user)
            if not ok2: return jsonify({'success': False, 'error': err2[1]}), err2[0]
        result = pz.set_profile(user.get('username'), cat, value,
                                user.get('role', 'user'), level, device)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/ai-employee/<employee_id>', methods=['GET'])
def pz_get_ai_style(employee_id):
    """获取某AI员工的个性化形象定制"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        style = pz.get_ai_employee_style(user.get('username'), employee_id)
        return jsonify({'success': True, 'employee_id': employee_id, 'style': style})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/ai-employee/<employee_id>', methods=['POST'])
def pz_set_ai_style(employee_id):
    """保存某AI员工的个性化形象定制"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        style = data.get('style')
        if not isinstance(style, dict):
            return jsonify({'success': False, 'error': 'style必须是对象'}), 400
        device = data.get('device', request.headers.get('X-Device-Id', 'unknown'))
        result = pz.set_ai_employee_style(user.get('username'), employee_id, style, device)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 个性化配色/主题/设置扩展 (v1.1): /api/maintenance/pz/themes/*
# ============================================================================

@maintenance_bp.route('/pz/themes/presets', methods=['GET'])
def pz_theme_presets():
    """获取所有预设主题方案列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        from ai_engines.personalization_core import get_preset_themes
        presets = get_preset_themes()
        return jsonify({'success': True, 'count': len(presets), 'presets': presets})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/themes/apply', methods=['POST'])
def pz_theme_apply():
    """应用某个预设主题方案到当前用户"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        from ai_engines.personalization_core import apply_preset_theme
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        theme_id = data.get('theme_id', '')
        if not theme_id or not isinstance(theme_id, str):
            return jsonify({'success': False, 'error': 'theme_id必填'}), 400
        # 防注入：只允许预设ID（字母数字下划线）
        import re
        if not re.match(r'^[a-z0-9_]+$', theme_id):
            return jsonify({'success': False, 'error': '非法theme_id'}), 400
        device = data.get('device', request.headers.get('X-Device-Id', 'unknown'))
        role = user.get('role', 'user')
        result = apply_preset_theme(user.get('username'), theme_id, pz, role=role, device=device)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/themes/custom', methods=['POST'])
def pz_theme_custom():
    """保存自定义配色方案（用户自由搭配颜色/字体/密度等）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        from ai_engines.personalization_core import ProfileCategory
        data = request.get_json(silent=True) or {}
        theme_config = data.get('theme_config')
        if not isinstance(theme_config, dict):
            return jsonify({'success': False, 'error': 'theme_config必须是对象'}), 400
        # 校验颜色格式（#RRGGBB）
        import re
        for ck in ('theme_color', 'accent_color'):
            val = theme_config.get(ck)
            if val and not re.match(r'^#[0-9a-fA-F]{6}$', str(val)):
                return jsonify({'success': False, 'error': f'{ck}颜色格式非法,需#RRGGBB'}), 400
        # 校验枚举字段
        for fk, allowed in [('dark_mode', ['light','dark','auto']),
                            ('ui_density', ['compact','comfortable','relaxed']),
                            ('radius_level', ['small','medium','large']),
                            ('font_family', ['system','mono','serif'])]:
            val = theme_config.get(fk)
            if val and val not in allowed:
                return jsonify({'success': False, 'error': f'{fk}取值非法: {val}'}), 400
        device = data.get('device', request.headers.get('X-Device-Id', 'unknown'))
        role = user.get('role', 'user')
        result = pz.set_profile(user.get('username'), ProfileCategory.UI_THEME,
                                theme_config, role=role, device=device)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/pz/css', methods=['GET'])
def pz_css():
    """生成当前用户的CSS变量字符串（前端直接注入<style>）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        from ai_engines.personalization_core import ProfileCategory, generate_css_variables
        agent = _get_agent()
        pz = _safe_pz(agent)
        if not pz: return jsonify({'success': False, 'error': '未初始化'}), 500
        theme_config = pz.get_profile(user.get('username'), ProfileCategory.UI_THEME,
                                      role=user.get('role', 'user'))
        css_text = generate_css_variables(theme_config)
        # 返回CSS纯文本（Content-Type: text/css）
        from flask import Response
        return Response(css_text, mimetype='text/css')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 定制化(3子模块): /api/maintenance/cz/*
# ============================================================================

@maintenance_bp.route('/cz/status', methods=['GET'])
def cz_status():
    """定制化引擎状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '定制化引擎未初始化'}), 500
        return jsonify({'success': True, 'status': cz.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/dashboard/<role>', methods=['GET'])
def cz_get_dashboard(role):
    """获取角色仪表盘组件"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        widgets = cz.get_dashboard(role, user.get('username'))
        return jsonify({'success': True, 'role': role, 'widgets': widgets,
                        'widget_count': len(widgets)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/dashboard/<role>', methods=['POST'])
def cz_set_dashboard(role):
    """保存角色仪表盘（需管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        widgets = data.get('widgets', [])
        if not isinstance(widgets, list):
            return jsonify({'success': False, 'error': 'widgets必须是数组'}), 400
        result = cz.set_dashboard(role, widgets, changed_by=user.get('username', 'system'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/workflows', methods=['GET'])
def cz_list_workflows():
    """列出工作流"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        limit = request.args.get('limit', 100, type=int)
        owner = request.args.get('owner')
        status = request.args.get('status')
        wfs = cz.list_workflows(owner=owner, status=status, limit=limit)
        return jsonify({'success': True, 'count': len(wfs), 'workflows': wfs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/workflows', methods=['POST'])
def cz_create_workflow():
    """创建工作流"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        name = data.get('name', '').strip()
        trigger = data.get('trigger')
        actions = data.get('actions', [])
        if not name or not trigger or not isinstance(actions, list):
            return jsonify({'success': False, 'error': '缺少必填字段name/trigger/actions'}), 400
        result = cz.create_workflow(name, user.get('username'), trigger, actions,
            condition=data.get('condition'), description=data.get('description', ''))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/workflows/<wf_id>/status', methods=['POST'])
def cz_workflow_status(wf_id):
    """切换工作流状态(draft/active/paused/archived)"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        status = data.get('status')
        if not status:
            return jsonify({'success': False, 'error': '缺少status字段'}), 400
        result = cz.set_workflow_status(wf_id, status, user.get('username'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/workflows/<wf_id>/execute', methods=['POST'])
def cz_workflow_execute(wf_id):
    """手动触发工作流执行"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        result = cz.execute_workflow(wf_id, data.get('context'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/form/<page>', methods=['GET'])
def cz_get_form(page):
    """获取页面自定义表单字段"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        fields = cz.get_form_fields(page)
        return jsonify({'success': True, 'page': page, 'fields': fields, 'count': len(fields)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/form/<page>/<field_name>', methods=['POST'])
def cz_set_form_field(page, field_name):
    """设置/更新页面自定义字段（需管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        ft = data.get('field_type', data.get('type'))
        label = data.get('label', field_name)
        if not ft:
            return jsonify({'success': False, 'error': '缺少field_type'}), 400
        result = cz.set_form_field(
            page, field_name, ft, label,
            required=bool(data.get('required', False)),
            default=data.get('default'),
            validations=data.get('validations'),
            options=data.get('options', []),
            display_order=data.get('display_order', 0),
            visible=bool(data.get('visible', True)),
            changed_by=user.get('username', 'system'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cz/form/<page>/<field_name>', methods=['DELETE'])
def cz_delete_form_field(page, field_name):
    """删除页面自定义字段（需管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cz = _safe_cz(agent)
        if not cz: return jsonify({'success': False, 'error': '未初始化'}), 500
        result = cz.delete_form_field(page, field_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 云端化(4子模块): /api/maintenance/cloud/*
# ============================================================================

@maintenance_bp.route('/cloud/status', methods=['GET'])
def cloud_status():
    """云同步层状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '云同步层未初始化'}), 500
        return jsonify({'success': True, 'status': cloud.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/sync-now', methods=['POST'])
def cloud_sync_now():
    """手动触发一次双向同步"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        result = cloud.force_sync_now(user.get('username'))
        return jsonify({'success': True, 'sync': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/snapshots', methods=['GET'])
def cloud_list_snapshots():
    """获取配置快照列表"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        limit = request.args.get('limit', 50, type=int)
        scope = request.args.get('scope')
        snaps = cloud.list_snapshots(scope=scope, limit=limit)
        return jsonify({'success': True, 'count': len(snaps), 'snapshots': snaps})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/snapshots', methods=['POST'])
def cloud_create_snapshot():
    """创建配置快照并上传云端"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        snap = cloud.create_snapshot(
            scope=data.get('scope', 'full'),
            username=user.get('username'),
            label=data.get('label', ''))
        return jsonify({'success': True, 'snapshot': snap})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/snapshots/<snap_id>/restore', methods=['POST'])
def cloud_restore_snapshot(snap_id):
    """从快照恢复配置（需管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        result = cloud.restore_snapshot(snap_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/session', methods=['GET'])
def cloud_get_session():
    """获取跨设备会话状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        device = request.args.get('device')
        sessions = cloud.load_session_state(user.get('username'), device)
        return jsonify({'success': True, 'username': user.get('username'), 'sessions': sessions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/session', methods=['POST'])
def cloud_save_session():
    """保存当前设备会话状态（自动跨设备同步）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        state = data.get('state')
        if not isinstance(state, dict):
            return jsonify({'success': False, 'error': 'state必须是对象'}), 400
        device = data.get('device', request.headers.get('X-Device-Id', 'unknown'))
        result = cloud.save_session_state(user.get('username'), device, state)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/cloud/cold-backup', methods=['POST'])
def cloud_cold_backup():
    """核心数据云端冷备(what: db/brain/all)（需管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        agent = _get_agent()
        cloud = _safe_cloud(agent)
        if not cloud: return jsonify({'success': False, 'error': '未初始化'}), 500
        data = request.get_json(silent=True) or {}
        what = data.get('what', 'db')
        if what not in ('db', 'brain', 'all'):
            return jsonify({'success': False, 'error': 'what必须是db/brain/all之一'}), 400
        result = cloud.cold_backup_core(what=what, label=data.get('label', ''))
        return jsonify({'success': True, 'cold_backup': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 智能化题库管理 (IntelligentQuestionBankManager) — 登录查看，操作需管理员
# ============================================================================

def _get_iqbm():
    """获取智能化题库管理器单例"""
    from ai_engines.intelligent_question_bank_manager import get_iqbm_manager
    return get_iqbm_manager()


@maintenance_bp.route('/iqbm/status', methods=['GET'])
def iqbm_status():
    """智能化题库管理系统状态"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        mgr = _get_iqbm()
        return jsonify({'success': True, 'status': mgr.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 知识点图谱 ---

@maintenance_bp.route('/iqbm/kg/tree', methods=['GET'])
def iqbm_kg_tree():
    """获取知识点树"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        subject = request.args.get('subject')
        parent_id = request.args.get('parent_id')
        mgr = _get_iqbm()
        tree = mgr.knowledge_graph.get_tree(subject=subject, parent_id=parent_id)
        return jsonify({'success': True, 'count': len(tree), 'tree': tree})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/kg/node', methods=['POST'])
def iqbm_kg_add_node():
    """添加知识点节点（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        mgr = _get_iqbm()
        result = mgr.knowledge_graph.add_node(
            node_id=data.get('node_id', ''),
            subject=data.get('subject', '通用'),
            node_type=data.get('node_type', 'knowledge_point'),
            name=data.get('name', ''),
            parent_id=data.get('parent_id'),
            description=data.get('description'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/kg/dependency', methods=['POST'])
def iqbm_kg_add_dep():
    """添加知识点依赖关系（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        mgr = _get_iqbm()
        result = mgr.knowledge_graph.add_dependency(
            data.get('from_node', ''), data.get('to_node', ''),
            data.get('dep_type', 'prerequisite'), data.get('weight', 1.0))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/kg/coverage', methods=['GET'])
def iqbm_kg_coverage():
    """知识点覆盖率分析"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        subject = request.args.get('subject')
        mgr = _get_iqbm()
        return jsonify({'success': True, 'coverage': mgr.knowledge_graph.get_coverage(subject)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/kg/node/<node_id>', methods=['DELETE'])
def iqbm_kg_delete_node(node_id):
    """删除知识点节点（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        mgr = _get_iqbm()
        return jsonify(mgr.knowledge_graph.delete_node(node_id))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 智能组卷 ---

@maintenance_bp.route('/iqbm/paper/blueprints', methods=['GET'])
def iqbm_paper_blueprints():
    """列出组卷蓝图"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        subject = request.args.get('subject')
        mgr = _get_iqbm()
        blueprints = mgr.paper_composer.list_blueprints(subject)
        return jsonify({'success': True, 'count': len(blueprints), 'blueprints': blueprints})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/paper/blueprint', methods=['POST'])
def iqbm_paper_save_blueprint():
    """保存组卷蓝图（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        mgr = _get_iqbm()
        result = mgr.paper_composer.save_blueprint(
            blueprint_id=data.get('blueprint_id', ''),
            name=data.get('name', ''),
            subject=data.get('subject', '通用'),
            config=data.get('config', {}),
            total_score=data.get('total_score', 100),
            duration_min=data.get('duration_min', 120),
            created_by=user.get('username', 'system'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/paper/compose', methods=['POST'])
def iqbm_paper_compose():
    """遗传算法智能组卷（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        mgr = _get_iqbm()
        result = mgr.paper_composer.compose_paper(
            subject=data.get('subject', '通用'),
            blueprint_config=data.get('blueprint_config', {}),
            paper_name=data.get('paper_name'),
            composed_by=user.get('username', 'system'),
            population_size=data.get('population_size', 50),
            generations=data.get('generations', 100))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/paper/list', methods=['GET'])
def iqbm_paper_list():
    """列出已组卷的试卷"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        subject = request.args.get('subject')
        limit = request.args.get('limit', 50, type=int)
        mgr = _get_iqbm()
        papers = mgr.paper_composer.list_papers(subject, limit)
        return jsonify({'success': True, 'count': len(papers), 'papers': papers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 题目生命周期 ---

@maintenance_bp.route('/iqbm/lifecycle/transition', methods=['POST'])
def iqbm_lifecycle_transition():
    """题目状态转换（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        mgr = _get_iqbm()
        result = mgr.lifecycle.transition(
            question_id=data.get('question_id', ''),
            to_state=data.get('to_state', ''),
            operator=user.get('username', 'system'),
            reason=data.get('reason'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/lifecycle/history/<question_id>', methods=['GET'])
def iqbm_lifecycle_history(question_id):
    """获取题目生命周期历史"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        limit = request.args.get('limit', 50, type=int)
        mgr = _get_iqbm()
        history = mgr.lifecycle.get_lifecycle_history(question_id, limit)
        return jsonify({'success': True, 'count': len(history), 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/lifecycle/auto-scan', methods=['POST'])
def iqbm_lifecycle_auto_scan():
    """自动状态转换扫描（管理员）"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    ok, err = _check_admin(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        mgr = _get_iqbm()
        result = mgr.lifecycle.auto_transition_scan()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/lifecycle/stats', methods=['GET'])
def iqbm_lifecycle_stats():
    """生命周期统计"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        mgr = _get_iqbm()
        return jsonify({'success': True, 'stats': mgr.lifecycle.get_lifecycle_stats()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 自适应学习路径 ---

@maintenance_bp.route('/iqbm/learning/analyze', methods=['POST'])
def iqbm_learning_analyze():
    """分析薄弱知识点并生成学习路径"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        student_id = data.get('student_id') or user.get('username', 'anonymous')
        mgr = _get_iqbm()
        result = mgr.learning_path.analyze_weakness(
            student_id=student_id,
            subject=data.get('subject', '通用'),
            answer_records=data.get('answer_records', []))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/iqbm/learning/path', methods=['GET'])
def iqbm_learning_path():
    """获取学习路径"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        student_id = request.args.get('student_id') or user.get('username', 'anonymous')
        subject = request.args.get('subject')
        mgr = _get_iqbm()
        paths = mgr.learning_path.get_path(student_id, subject)
        return jsonify({'success': True, 'count': len(paths), 'paths': paths})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 题库健康度 ---

@maintenance_bp.route('/iqbm/health', methods=['GET'])
def iqbm_health():
    """题库健康度分析"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        subject = request.args.get('subject')
        mgr = _get_iqbm()
        result = mgr.health_analyzer.analyze(subject)
        return jsonify({'success': True, 'health': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 智能标签推荐 ---

@maintenance_bp.route('/iqbm/tags/recommend', methods=['POST'])
def iqbm_tags_recommend():
    """智能标签推荐"""
    user = _current_safe_user()
    ok, err = _check_login(user)
    if not ok: return jsonify({'success': False, 'error': err[1]}), err[0]
    try:
        data = request.get_json(silent=True) or {}
        mgr = _get_iqbm()
        result = mgr.tag_recommender.recommend_tags(
            content=data.get('content', ''),
            subject=data.get('subject'),
            existing_tags=data.get('existing_tags', []))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


bp = Blueprint('maintenance_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'maintenance','routes_implemented':1}})

