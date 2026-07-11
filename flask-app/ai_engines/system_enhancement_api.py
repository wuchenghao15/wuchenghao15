# -*- coding: utf-8 -*-
"""
系统综合增强管理器 API 蓝图
提供十大功能模块的统一 HTTP 接口:
1. 数据库功能拓展
2. 端口管理
3. 集群管理
4. 多维度管理
5. 权限规则升级
6. 题库升级
7. AI集群升级
8. AI模型库升级
9. 前端布局优化
10. Git自动同步
"""

import os
import sys
from flask import Blueprint, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ai_engines.system_enhancement_manager import system_enhancement_manager as _mgr
    _MGR_AVAILABLE = True
except Exception as e:
    _MGR_AVAILABLE = False
    _MGR_ERROR = str(e)
    _mgr = None

# 创建蓝图
system_enhancement_bp = Blueprint('system_enhancement', __name__, url_prefix='/api/enhancement')


def _ok(data):
    """统一成功响应封装"""
    return jsonify({'success': True, 'data': data, 'timestamp': __import__('datetime').datetime.now().isoformat()})


def _fail(msg, code=500):
    """统一失败响应封装"""
    return jsonify({'success': False, 'error': msg}), code


# ============================================================
# 健康检查 & 总览
# ============================================================
@system_enhancement_bp.route('/status', methods=['GET'])
def enhancement_status():
    """获取增强管理器总览状态"""
    if not _MGR_AVAILABLE:
        return _fail(f'增强管理器未加载: {_MGR_ERROR}', 503)
    return _ok(_mgr.get_enhancement_status())


@system_enhancement_bp.route('/modules', methods=['GET'])
def enhancement_modules():
    """获取所有功能模块列表"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok({'modules': _mgr.module_status, 'count': len(_mgr.module_status)})


# ============================================================
# 1. 数据库功能拓展
# ============================================================
@system_enhancement_bp.route('/database/health', methods=['GET'])
def db_health():
    """数据库健康检查"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.db_health_check())


@system_enhancement_bp.route('/database/structure', methods=['GET'])
def db_structure():
    """分析指定分片库的表结构"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    db_name = request.args.get('db', 'system.db')
    return _ok(_mgr.analyze_table_structure(db_name))


@system_enhancement_bp.route('/database/index-suggestions', methods=['GET'])
def db_index_suggestions():
    """索引优化建议"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    db_name = request.args.get('db', 'system.db')
    return _ok(_mgr.suggest_index_optimization(db_name))


@system_enhancement_bp.route('/database/cluster', methods=['GET', 'POST', 'DELETE'])
def db_cluster_mgmt():
    """数据库集群管理 (status/add/remove)"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    action = 'status'
    node_info = None
    if request.method == 'GET':
        action = request.args.get('action', 'status')
    elif request.method == 'POST':
        action = request.json.get('action', 'add') if request.json else 'add'
        node_info = request.json if request.json else {}
    elif request.method == 'DELETE':
        action = 'remove'
        node_info = {'node_id': request.args.get('node_id', '')}
    return _ok(_mgr.manage_db_cluster(action, node_info))


# ============================================================
# 2. 端口管理
# ============================================================
@system_enhancement_bp.route('/ports/scan', methods=['GET'])
def ports_scan():
    """扫描端口"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    host = request.args.get('host', '127.0.0.1')
    port_range = request.args.get('range', '8000-9000')
    return _ok(_mgr.scan_ports(host, port_range))


@system_enhancement_bp.route('/ports/stats', methods=['GET'])
def ports_stats():
    """端口使用统计"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.get_port_usage_stats())


@system_enhancement_bp.route('/ports/allocate', methods=['POST'])
def ports_allocate():
    """分配端口"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    data = request.json or {}
    service = data.get('service', 'unknown')
    preferred = data.get('preferred')
    return _ok(_mgr.allocate_port(service, preferred))


# ============================================================
# 3. 集群管理
# ============================================================
@system_enhancement_bp.route('/cluster/nodes', methods=['GET', 'POST', 'DELETE'])
def cluster_nodes():
    """集群节点管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    if request.method == 'GET':
        return _ok(_mgr.manage_cluster_nodes('list'))
    if request.method == 'POST':
        node = request.json or {}
        return _ok(_mgr.manage_cluster_nodes('add', node))
    node_id = request.args.get('node_id', '')
    return _ok(_mgr.manage_cluster_nodes('remove', {'node_id': node_id}))


@system_enhancement_bp.route('/cluster/monitor', methods=['GET'])
def cluster_monitor():
    """集群状态监控"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.monitor_cluster_status())


@system_enhancement_bp.route('/cluster/load-balance', methods=['GET'])
def cluster_load_balance():
    """负载均衡"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    strategy = request.args.get('strategy', 'round_robin')
    return _ok(_mgr.load_balance(strategy))


# ============================================================
# 4. 多维度管理
# ============================================================
@system_enhancement_bp.route('/system/resources', methods=['GET'])
def system_resources():
    """系统资源多维度监控"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.monitor_system_resources())


@system_enhancement_bp.route('/system/performance', methods=['GET'])
def system_performance():
    """性能分析"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.analyze_performance())


# ============================================================
# 5. 权限规则升级
# ============================================================
@system_enhancement_bp.route('/permissions/rules', methods=['GET', 'POST', 'DELETE'])
def permission_rules():
    """权限规则管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    if request.method == 'GET':
        return _ok(_mgr.manage_permission_rules('list'))
    if request.method == 'POST':
        rule = request.json or {}
        action = rule.pop('action', 'upsert')
        return _ok(_mgr.manage_permission_rules(action, rule))
    rule_id = request.args.get('rule_id', '')
    return _ok(_mgr.manage_permission_rules('delete', {'rule_id': rule_id}))


@system_enhancement_bp.route('/permissions/matrix', methods=['GET'])
def permission_matrix():
    """角色权限矩阵"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.get_role_permission_matrix())


# ============================================================
# 6. 题库升级
# ============================================================
@system_enhancement_bp.route('/questions/stats', methods=['GET'])
def questions_stats():
    """题库统计"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.get_question_bank_stats())


@system_enhancement_bp.route('/questions/categories', methods=['GET', 'POST', 'DELETE'])
def questions_categories():
    """题目分类管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    if request.method == 'GET':
        return _ok(_mgr.manage_question_categories('list'))
    if request.method == 'POST':
        category = request.json or {}
        action = category.pop('action', 'upsert')
        return _ok(_mgr.manage_question_categories(action, category))
    category_id = request.args.get('category_id', '')
    return _ok(_mgr.manage_question_categories('delete', {'category_id': category_id}))


@system_enhancement_bp.route('/questions/quality', methods=['GET'])
def questions_quality():
    """题目质量评估"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    limit = int(request.args.get('limit', 100))
    return _ok(_mgr.evaluate_question_quality(limit))


# ============================================================
# 7. AI集群升级
# ============================================================
@system_enhancement_bp.route('/ai-cluster/nodes', methods=['GET', 'POST', 'DELETE'])
def ai_cluster_nodes():
    """AI节点管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    if request.method == 'GET':
        return _ok(_mgr.manage_ai_nodes('list'))
    if request.method == 'POST':
        node = request.json or {}
        action = node.pop('action', 'upsert')
        return _ok(_mgr.manage_ai_nodes(action, node))
    node_id = request.args.get('node_id', '')
    return _ok(_mgr.manage_ai_nodes('delete', {'node_id': node_id}))


@system_enhancement_bp.route('/ai-cluster/schedule', methods=['POST'])
def ai_cluster_schedule():
    """AI模型调度"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    model_id = (request.json or {}).get('model_id', '')
    return _ok(_mgr.schedule_ai_models(model_id))


@system_enhancement_bp.route('/ai-cluster/load-balance', methods=['GET'])
def ai_cluster_load_balance():
    """AI负载均衡"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.ai_load_balance())


# ============================================================
# 8. AI模型库升级
# ============================================================
@system_enhancement_bp.route('/ai-models/register', methods=['POST'])
def ai_models_register():
    """模型注册"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    model = request.json or {}
    return _ok(_mgr.register_model(model))


@system_enhancement_bp.route('/ai-models/versions', methods=['GET'])
def ai_models_versions():
    """模型版本管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    model_name = request.args.get('model_name', '')
    return _ok(_mgr.manage_model_versions(model_name))


@system_enhancement_bp.route('/ai-models/evaluate', methods=['POST'])
def ai_models_evaluate():
    """模型性能评估"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    data = request.json or {}
    model_id = data.get('model_id', '')
    score = float(data.get('score', 0.0))
    return _ok(_mgr.evaluate_model_performance(model_id, score))


# ============================================================
# 9. 前端布局优化
# ============================================================
@system_enhancement_bp.route('/frontend/layouts', methods=['GET', 'POST', 'DELETE'])
def frontend_layouts():
    """布局配置管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    if request.method == 'GET':
        return _ok(_mgr.manage_layout_config('list'))
    if request.method == 'POST':
        layout = request.json or {}
        action = layout.pop('action', 'upsert')
        return _ok(_mgr.manage_layout_config(action, layout))
    layout_id = request.args.get('layout_id', '')
    return _ok(_mgr.manage_layout_config('delete', {'layout_id': layout_id}))


@system_enhancement_bp.route('/frontend/layouts/activate', methods=['POST'])
def frontend_layouts_activate():
    """激活布局"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    layout = request.json or {}
    return _ok(_mgr.manage_layout_config('activate', layout))


@system_enhancement_bp.route('/frontend/themes', methods=['GET', 'POST'])
def frontend_themes():
    """主题管理"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    if request.method == 'GET':
        return _ok(_mgr.manage_themes('list'))
    theme = request.json or {}
    return _ok(_mgr.manage_themes('apply', theme))


# ============================================================
# 10. Git自动同步
# ============================================================
@system_enhancement_bp.route('/git/changes', methods=['GET'])
def git_changes():
    """变更检测"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    return _ok(_mgr.detect_changes())


@system_enhancement_bp.route('/git/commit', methods=['POST'])
def git_commit():
    """自动提交"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    message = (request.json or {}).get('message')
    return _ok(_mgr.auto_commit(message))


@system_enhancement_bp.route('/git/push', methods=['POST'])
def git_push():
    """自动推送"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    data = request.json or {}
    remote = data.get('remote', 'origin')
    branch = data.get('branch')
    return _ok(_mgr.auto_push(remote, branch))


@system_enhancement_bp.route('/git/sync', methods=['POST'])
def git_sync():
    """一键同步 (提交+推送)"""
    if not _MGR_AVAILABLE:
        return _fail('增强管理器未加载', 503)
    data = request.json or {}
    message = data.get('message', f"自动同步 - {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    commit_result = _mgr.auto_commit(message)
    push_result = None
    if commit_result.get('success'):
        push_result = _mgr.auto_push(data.get('remote', 'origin'), data.get('branch'))
    return _ok({
        'commit': commit_result,
        'push': push_result,
        'synced': bool(push_result and push_result.get('success')),
    })


def register_enhancement_blueprint(app):
    """将增强管理器蓝图注册到Flask应用"""
    try:
        from flask import Flask
        if isinstance(app, Flask):
            app.register_blueprint(system_enhancement_bp)
            app.logger.info(f"系统增强管理器蓝图已注册，路由前缀: {system_enhancement_bp.url_prefix}")
            return True
    except Exception as e:
        import logging
        logging.getLogger('system_enhancement_api').error(f"注册增强管理器蓝图失败: {e}")
        return False
    return False


# 模块加载时自动尝试注册到主应用
def _auto_register():
    """尝试自动注册到主应用（如果可用）"""
    try:
        import __main__
        main_app = getattr(__main__, 'app', None)
        if main_app is not None:
            register_enhancement_blueprint(main_app)
    except Exception:
        pass


_auto_register()
