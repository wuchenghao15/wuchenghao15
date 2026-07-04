# -*- coding: utf-8 -*-
"""
AI 智能分散数据库系统 API
提供对 6 个分片库、4 个 DB 员工、迁移框架、路由表、健康检查和决策日志的 HTTP 访问。

端点分组：
    - 系统状态与分片信息：/status, /shards, /shards/<name>, /health
    - 路由元数据：       /routing, /route/test (POST)
    - 迁移管理：         /migration/status, /migration/progress/<t>, /migration/start (POST)
    - DB 员工管理：      /employees, /employees/start-all (POST), /employees/stop-all (POST),
                              /employees/<id>/start (POST), /employees/<id>/stop (POST)
    - 决策日志：         /decisions

鉴权策略：
    只读端点 → @require_login
    写操作端点 → @require_admin (admin/super_admin/hardware_admin/hardware_vikey_admin)

安全约束：
    所有接受 table_name 参数的端点必须通过白名单校验（仅允许 TABLE_REGISTRY 中的表），
    防止 migration_framework 内部 f-string 拼接 SQL 造成注入风险。

懒加载策略：
    permission_decorators 仅依赖 flask+functools，可在模块级导入；
    ai_engines 模块涉及数据库连接，必须在函数内懒加载导入。
"""

import logging
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify

# 轻量级权限装饰器（仅依赖 flask+functools，可模块级导入）
from app.middlewares.permission_decorators import require_login, require_admin

logger = logging.getLogger(__name__)

ai_distributed_db_api = Blueprint('ai_distributed_db_api', __name__)

# 模块级缓存，避免每次请求重复创建迁移框架实例
_migration_framework_instance = None


# ============================================================
# 懒加载 getter（ai_engines 涉及数据库连接，必须延迟导入）
# ============================================================
def get_manager():
    """获取 AIDistributedDatabaseManager 单例"""
    try:
        from ai_engines.ai_distributed_db_manager import get_ai_distributed_db_manager
        return get_ai_distributed_db_manager()
    except Exception as e:
        logger.error(f"获取 AI 分散数据库管理器失败: {e}")
        return None


def get_migration_framework():
    """获取 MigrationFramework 实例（按需创建并缓存）"""
    global _migration_framework_instance
    if _migration_framework_instance is not None:
        return _migration_framework_instance
    try:
        from ai_engines.db_employees.migration_framework import MigrationFramework
        manager = get_manager()
        if not manager:
            return None
        _migration_framework_instance = MigrationFramework(manager)
        return _migration_framework_instance
    except Exception as e:
        logger.error(f"获取迁移框架实例失败: {e}")
        return None


def _validate_table_name(table_name: str) -> Optional[str]:
    """校验表名是否在白名单中。

    Returns:
        None   - 校验通过
        str    - 错误消息（用于响应给客户端）
    """
    if not table_name:
        return "缺少 table_name 参数"
    try:
        from ai_engines.db_schema_registry import get_table_info
        info = get_table_info(table_name)
        if info is None:
            return f"表 {table_name} 不在路由注册表中（未知表名）"
        return None
    except Exception as e:
        return f"表名校验异常: {e}"


# ============================================================
# 系统状态与分片信息（只读 → @require_login）
# ============================================================
@ai_distributed_db_api.route('/ai-distributed-db/status', methods=['GET'])
@require_login
def get_status():
    """获取 AI 智能分散数据库系统整体状态"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        status = manager.get_status()
        return jsonify({
            'success': True,
            'data': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取分散数据库状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/shards', methods=['GET'])
@require_login
def list_shards():
    """列出所有分片库信息"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        shards = manager.get_shards_info()
        return jsonify({
            'success': True,
            'data': shards,
            'total': len(shards),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取分片列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/shards/<path:name>', methods=['GET'])
@require_login
def get_shard_detail(name):
    """获取单个分片库详情"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        shards = manager.get_shards_info()
        matched = [s for s in shards if s.get('db_name') == name or s.get('name') == name]
        if not matched:
            return jsonify({'success': False, 'error': f'分片 {name} 不存在'}), 404
        return jsonify({
            'success': True,
            'data': matched[0],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取分片详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 路由元数据
# ============================================================
@ai_distributed_db_api.route('/ai-distributed-db/routing', methods=['GET'])
@require_login
def get_routing_table():
    """获取表路由表（表名 → 分片库映射）"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        routing = manager.get_routing_table()
        return jsonify({
            'success': True,
            'data': routing,
            'total': len(routing),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取路由表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/route/test', methods=['POST'])
@require_admin
def test_route():
    """测试路由决策（给定表名和操作类型，返回目标分片库）

    需管理员权限。请求体 JSON: {"table_name": "...", "operation": "select|insert|update|delete"}
    """
    try:
        data = request.get_json(silent=True) or {}
        table_name = data.get('table_name')
        operation = data.get('operation', 'select')

        err = _validate_table_name(table_name)
        if err:
            return jsonify({'success': False, 'error': err}), 400

        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        result = manager.route_query(table_name, operation)
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"测试路由决策失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 迁移管理
# ============================================================
@ai_distributed_db_api.route('/ai-distributed-db/migration/status', methods=['GET'])
@require_login
def get_migration_status():
    """获取所有迁移进度汇总（含迁移框架和元数据库记录）"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503

        migration_status = manager.get_migration_status()
        framework = get_migration_framework()
        framework_progress = framework.get_all_progress() if framework else []

        return jsonify({
            'success': True,
            'data': {
                'meta_status': migration_status,
                'framework_progress': framework_progress
            },
            'total': len(migration_status),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取迁移状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/migration/progress/<table_name>', methods=['GET'])
@require_login
def get_migration_progress(table_name):
    """获取指定表的迁移进度"""
    try:
        err = _validate_table_name(table_name)
        if err:
            return jsonify({'success': False, 'error': err}), 400

        framework = get_migration_framework()
        if not framework:
            return jsonify({'success': False, 'error': '迁移框架未初始化'}), 503
        progress = framework.get_progress(table_name)
        return jsonify({
            'success': True,
            'data': progress,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取单表迁移进度失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/migration/start', methods=['POST'])
@require_admin
def start_migration():
    """启动下一批迁移（分批 1000 条，含 MD5 校验）

    需管理员权限。请求体 JSON: {"table_name": "..."}
    """
    try:
        data = request.get_json(silent=True) or {}
        table_name = data.get('table_name')

        err = _validate_table_name(table_name)
        if err:
            return jsonify({'success': False, 'error': err}), 400

        framework = get_migration_framework()
        if not framework:
            return jsonify({'success': False, 'error': '迁移框架未初始化'}), 503

        result = framework.migrate_next_batch(table_name)
        return jsonify({
            'success': result.get('status') != 'error',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"启动迁移失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# DB 员工管理
# ============================================================
@ai_distributed_db_api.route('/ai-distributed-db/employees', methods=['GET'])
@require_login
def list_employees():
    """列出所有 DB 员工状态"""
    try:
        from ai_engines.db_employees import get_db_employees_status
        employees = get_db_employees_status()
        return jsonify({
            'success': True,
            'data': employees,
            'total': len(employees),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取 DB 员工列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/employees/start-all', methods=['POST'])
@require_admin
def start_all_employees():
    """启动所有 DB 员工守护线程（需管理员权限）"""
    try:
        from ai_engines.db_employees import start_all_db_employees
        result = start_all_db_employees()
        started_count = sum(1 for v in result.values() if v)
        return jsonify({
            'success': True,
            'data': result,
            'message': f"已启动 {started_count} / {len(result)} 个员工",
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"启动所有 DB 员工失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/employees/stop-all', methods=['POST'])
@require_admin
def stop_all_employees():
    """停止所有 DB 员工守护线程（需管理员权限）"""
    try:
        from ai_engines.db_employees import stop_all_db_employees
        result = stop_all_db_employees()
        stopped_count = sum(1 for v in result.values() if v)
        return jsonify({
            'success': True,
            'data': result,
            'message': f"已停止 {stopped_count} / {len(result)} 个员工",
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"停止所有 DB 员工失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/employees/<employee_id>/start', methods=['POST'])
@require_admin
def start_employee(employee_id):
    """启动指定 DB 员工守护线程（需管理员权限）"""
    try:
        from ai_engines.db_employees import get_db_employee
        employee = get_db_employee(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': f'员工 {employee_id} 不存在'}), 404
        ok = employee.start()
        return jsonify({
            'success': ok,
            'data': {'employee_id': employee_id, 'started': ok},
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"启动 DB 员工 {employee_id} 失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/employees/<employee_id>/stop', methods=['POST'])
@require_admin
def stop_employee(employee_id):
    """停止指定 DB 员工守护线程（需管理员权限）"""
    try:
        from ai_engines.db_employees import get_db_employee
        employee = get_db_employee(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': f'员工 {employee_id} 不存在'}), 404
        ok = employee.stop()
        return jsonify({
            'success': ok,
            'data': {'employee_id': employee_id, 'stopped': ok},
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"停止 DB 员工 {employee_id} 失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 健康检查与决策日志
# ============================================================
@ai_distributed_db_api.route('/ai-distributed-db/health', methods=['GET'])
@require_login
def get_health():
    """检查所有分片库健康状态（容量/锁状态/journal）"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        health = manager.check_shard_health()
        return jsonify({
            'success': True,
            'data': health,
            'total': len(health),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_distributed_db_api.route('/ai-distributed-db/decisions', methods=['GET'])
@require_login
def get_decisions():
    """获取 AI 决策日志（支持 limit 查询参数，默认 50，上限 1000）"""
    try:
        manager = get_manager()
        if not manager:
            return jsonify({'success': False, 'error': '系统未初始化'}), 503
        try:
            limit = int(request.args.get('limit', 50))
            if limit <= 0 or limit > 1000:
                limit = 50
        except (TypeError, ValueError):
            limit = 50
        decisions = manager.get_decisions(limit=limit)
        return jsonify({
            'success': True,
            'data': decisions,
            'total': len(decisions),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取决策日志失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 初始化钩子（由 _register_blueprints 通过 hasattr 自动检测并调用）
# ============================================================
def init_enhanced_system():
    """初始化 AI 分散数据库系统（创建 DB 员工实例，不启动守护线程）

    守护线程需通过 POST /api/ai-distributed-db/employees/start-all 手动启动，
    避免 Flask 启动时阻塞。

    函数名沿用 init_enhanced_system 以匹配 _register_blueprints 中的
    hasattr(mod, 'init_enhanced_system') 自动检测逻辑。
    """
    try:
        from ai_engines.ai_distributed_db_manager import get_ai_distributed_db_manager
        from ai_engines.db_employees import init_db_employees
        manager = get_ai_distributed_db_manager()
        employees = init_db_employees(manager=manager)
        logger.info(f"AI 分散数据库系统初始化完成: {len(employees)} 名 DB 员工已注册")
        return True
    except Exception as e:
        logger.error(f"AI 分散数据库系统初始化失败: {e}")
        return False


# 别名，便于外部按语义调用
init_ai_distributed_db = init_enhanced_system


__all__ = ['ai_distributed_db_api', 'init_enhanced_system', 'init_ai_distributed_db']
