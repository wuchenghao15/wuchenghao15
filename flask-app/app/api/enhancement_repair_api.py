# -*- coding: utf-8 -*-
"""
AI增强修复API
提供代码扫描、错误修复、功能增强的RESTful接口
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

enhancement_repair_api = Blueprint('enhancement_repair_api', __name__)


def get_enhancement_repair_employee():
    """获取增强修复员工实例"""
    from ai_engines.ai_enhancement_repair_employee import get_enhancement_repair_employee
    return get_enhancement_repair_employee()


@enhancement_repair_api.route('/api/enhancement/employee/info', methods=['GET'])
def get_employee_info():
    """获取增强修复员工信息"""
    try:
        employee = get_enhancement_repair_employee()
        return jsonify({
            "success": True,
            "data": {
                "name": employee.name,
                "employee_id": employee.employee_id,
                "role": employee.role,
                "status": employee.status,
                "description": "自动联想增强优化系统功能，自动检测修复源代码错误并上报数据库",
                "capabilities": [
                    "代码错误检测",
                    "自动代码修复",
                    "错误上报数据库",
                    "功能增强建议",
                    "自动优化系统",
                    "智能联想增强"
                ]
            }
        })
    except Exception as e:
        logger.error(f"获取员工信息失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/employee/start', methods=['POST'])
def start_employee():
    """启动增强修复员工"""
    try:
        employee = get_enhancement_repair_employee()
        employee.start()
        return jsonify({"success": True, "message": "AI增强修复员工已启动"})
    except Exception as e:
        logger.error(f"启动员工失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/employee/stop', methods=['POST'])
def stop_employee():
    """停止增强修复员工"""
    try:
        employee = get_enhancement_repair_employee()
        employee.stop()
        return jsonify({"success": True, "message": "AI增强修复员工已停止"})
    except Exception as e:
        logger.error(f"停止员工失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/employee/status', methods=['GET'])
def get_status():
    """获取增强修复员工状态"""
    try:
        employee = get_enhancement_repair_employee()
        status = employee.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/scan', methods=['POST'])
def scan_code():
    """扫描代码"""
    try:
        data = request.get_json() or {}
        directory = data.get('directory')
        
        employee = get_enhancement_repair_employee()
        result = employee.scan_code(directory)
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"扫描代码失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/errors', methods=['GET'])
def get_errors():
    """获取错误列表"""
    try:
        severity = request.args.get('severity')
        
        employee = get_enhancement_repair_employee()
        errors = employee.get_errors(severity)
        
        return jsonify({
            "success": True,
            "data": errors,
            "count": len(errors)
        })
    except Exception as e:
        logger.error(f"获取错误列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/enhance', methods=['POST'])
def enhance_feature():
    """增强指定功能"""
    try:
        data = request.get_json() or {}
        feature_name = data.get('feature_name')
        
        if not feature_name:
            return jsonify({"success": False, "message": "功能名称不能为空"}), 400
        
        employee = get_enhancement_repair_employee()
        result = employee.enhance_feature(feature_name)
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"增强功能失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/auto_enhance', methods=['POST'])
def auto_enhance_all():
    """自动增强所有功能"""
    try:
        employee = get_enhancement_repair_employee()
        result = employee.auto_enhance_all()
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"自动增强失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/enhancements', methods=['GET'])
def get_enhancements():
    """获取增强记录"""
    try:
        employee = get_enhancement_repair_employee()
        enhancements = employee.get_enhancements()
        
        return jsonify({
            "success": True,
            "data": enhancements,
            "count": len(enhancements)
        })
    except Exception as e:
        logger.error(f"获取增强记录失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/suggestions/<feature_name>', methods=['GET'])
def get_suggestions(feature_name):
    """获取功能增强建议"""
    try:
        employee = get_enhancement_repair_employee()
        suggestions = employee.enhancement_engine.suggest_enhancements(feature_name)
        
        return jsonify({
            "success": True,
            "data": {
                "feature_name": feature_name,
                "suggestions": suggestions
            }
        })
    except Exception as e:
        logger.error(f"获取建议失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@enhancement_repair_api.route('/api/enhancement/scan_and_fix', methods=['POST'])
def scan_and_fix():
    """扫描并修复代码"""
    try:
        data = request.get_json() or {}
        directory = data.get('directory')
        fix_only_critical = data.get('fix_only_critical', True)
        
        employee = get_enhancement_repair_employee()
        result = employee.scan_code(directory)
        
        if fix_only_critical:
            critical_errors = [e for e in result['errors'] if e.get('severity') in ['high', 'critical']]
            result['critical_errors_fixed'] = len(critical_errors)
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"扫描修复失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500