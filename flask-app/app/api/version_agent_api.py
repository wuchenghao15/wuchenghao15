# -*- coding: utf-8 -*-
"""
VersionAgent AI API
系统版本管理Agent接口
"""

from flask import Blueprint, jsonify, request
from ai_engines.version_agent_ai import version_agent_ai
from app.utils.logging import logger

version_agent_api = Blueprint('version_agent_api', __name__)


@version_agent_api.route('/version-agent/status')
def get_version_agent_status():
    """获取VersionAgent状态"""
    try:
        status = version_agent_ai.get_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取VersionAgent状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/version')
def get_current_version():
    """获取当前版本信息"""
    try:
        version_info = version_agent_ai.get_current_version()
        return jsonify({
            'success': True,
            'version': version_info
        })
    except Exception as e:
        logger.error(f"获取当前版本失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/rules')
def get_version_rules():
    """获取版本规则"""
    try:
        rules = version_agent_ai.get_version_rules()
        return jsonify({
            'success': True,
            'rules': rules
        })
    except Exception as e:
        logger.error(f"获取版本规则失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/triggers')
def get_trigger_conditions():
    """获取触发条件"""
    try:
        triggers = version_agent_ai.get_trigger_conditions()
        return jsonify({
            'success': True,
            'triggers': triggers
        })
    except Exception as e:
        logger.error(f"获取触发条件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/check-triggers')
def check_trigger_conditions():
    """检查触发条件"""
    try:
        result = version_agent_ai.check_trigger_conditions()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"检查触发条件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/maintenance-plans')
def get_maintenance_plans():
    """获取维护计划"""
    try:
        plans = version_agent_ai.get_maintenance_plans()
        return jsonify({
            'success': True,
            'plans': plans
        })
    except Exception as e:
        logger.error(f"获取维护计划失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/maintenance-plans/<plan_id>/execute', methods=['POST'])
def execute_maintenance_plan(plan_id):
    """执行维护计划"""
    try:
        result = version_agent_ai.execute_maintenance_plan(plan_id)
        return jsonify({
            'success': result.get('success', False),
            'result': result
        })
    except Exception as e:
        logger.error(f"执行维护计划失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/maintenance-plans/<plan_id>/enable', methods=['POST'])
def enable_maintenance_plan(plan_id):
    """启用/禁用维护计划"""
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled', True)
        
        success = version_agent_ai.enable_maintenance_plan(plan_id, enabled)
        
        return jsonify({
            'success': success,
            'message': f"维护计划 {'已启用' if enabled else '已禁用'}"
        })
    except Exception as e:
        logger.error(f"设置维护计划状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/maintenance-logs')
def get_maintenance_logs():
    """获取维护日志"""
    try:
        limit = request.args.get('limit', 20, type=int)
        logs = version_agent_ai.get_maintenance_logs(limit)
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs)
        })
    except Exception as e:
        logger.error(f"获取维护日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/violations')
def get_violations():
    """获取违规记录"""
    try:
        limit = request.args.get('limit', 20, type=int)
        violations = version_agent_ai.get_violations(limit)
        return jsonify({
            'success': True,
            'violations': violations,
            'total': len(violations)
        })
    except Exception as e:
        logger.error(f"获取违规记录失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/violations/<violation_id>/resolve', methods=['POST'])
def resolve_violation(violation_id):
    """解决违规记录"""
    try:
        success = version_agent_ai.resolve_violation(int(violation_id))
        
        return jsonify({
            'success': success,
            'message': '违规记录已解决' if success else '解决失败'
        })
    except Exception as e:
        logger.error(f"解决违规记录失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/check-version', methods=['POST'])
def check_version_rules():
    """检查版本规则"""
    try:
        data = request.get_json() or {}
        new_version = data.get('version')
        
        if not new_version:
            return jsonify({
                'success': False,
                'error': '请提供版本号'
            }), 400
        
        violations = version_agent_ai.check_version_rules(new_version)
        
        return jsonify({
            'success': True,
            'version': new_version,
            'valid': len(violations) == 0,
            'violations': violations
        })
    except Exception as e:
        logger.error(f"检查版本规则失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/bump-version', methods=['POST'])
def bump_version():
    """升级版本号"""
    try:
        data = request.get_json() or {}
        change_type = data.get('type', 'patch')
        
        current_version = version_agent_ai.get_current_version().get('version', '0.0.0')
        
        from ai_engines.version_agent_ai import VersionChangeType
        change_type_enum = VersionChangeType(change_type.upper())
        
        new_version = version_agent_ai.bump_version(current_version, change_type_enum)
        
        return jsonify({
            'success': True,
            'current_version': current_version,
            'new_version': new_version,
            'change_type': change_type
        })
    except Exception as e:
        logger.error(f"升级版本失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/compare')
def compare_versions():
    """比较两个版本"""
    try:
        v1 = request.args.get('v1')
        v2 = request.args.get('v2')
        
        if not v1 or not v2:
            return jsonify({
                'success': False,
                'error': '请提供两个版本号 v1 和 v2'
            }), 400
        
        result = version_agent_ai.compare_versions(v1, v2)
        
        comparison_text = 'equal'
        if result > 0:
            comparison_text = f'{v1} > {v2}'
        elif result < 0:
            comparison_text = f'{v1} < {v2}'
        
        return jsonify({
            'success': True,
            'v1': v1,
            'v2': v2,
            'comparison': comparison_text,
            'result': result
        })
    except Exception as e:
        logger.error(f"比较版本失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/validate-format')
def validate_version_format():
    """验证版本格式"""
    try:
        version = request.args.get('version')
        
        if not version:
            return jsonify({
                'success': False,
                'error': '请提供版本号'
            }), 400
        
        valid = version_agent_ai.validate_version_format(version)
        
        return jsonify({
            'success': True,
            'version': version,
            'valid': valid,
            'message': '格式正确' if valid else '格式错误，必须符合X.Y.Z格式'
        })
    except Exception as e:
        logger.error(f"验证版本格式失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/health-check', methods=['POST'])
def run_health_check():
    """运行健康检查"""
    try:
        result = version_agent_ai._check_database_health()
        disk_result = version_agent_ai._check_disk_space()
        log_result = version_agent_ai._check_logs()
        backup_result = version_agent_ai._check_backups()
        version_result = version_agent_ai._check_version_consistency()
        
        overall_status = 'healthy'
        for check in [result, disk_result, log_result, backup_result, version_result]:
            if check.get('status') == 'critical':
                overall_status = 'critical'
                break
            elif check.get('status') == 'warning' and overall_status == 'healthy':
                overall_status = 'warning'
        
        return jsonify({
            'success': True,
            'overall_status': overall_status,
            'checks': {
                'database': result,
                'disk_space': disk_result,
                'logs': log_result,
                'backups': backup_result,
                'version_consistency': version_result
            }
        })
    except Exception as e:
        logger.error(f"运行健康检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_agent_api.route('/version-agent/create-backup', methods=['POST'])
def create_backup():
    """创建备份"""
    try:
        data = request.get_json() or {}
        description = data.get('description', '手动备份')
        
        result = version_agent_ai._create_full_backup()
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        })
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500